"""Create or promote the first SPECTRA-UPI moderator/admin.

There is no default password anywhere in the repository.

Usage (from ``backend/``):

    python -m scripts.create_admin --email you@example.com \
        --name "Your Name" --phone 9876543210

The password is prompted for interactively. For CI/automation you may set
``ADMIN_PASSWORD`` in the environment instead of typing it.
"""

from __future__ import annotations

import argparse
import getpass
import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from api.auth import hash_password  # noqa: E402
from db.database import SessionLocal, create_tables  # noqa: E402
from db.models import User  # noqa: E402


def _password() -> str:
    env_password = os.getenv("ADMIN_PASSWORD")
    if env_password:
        return env_password
    first = getpass.getpass("Password: ")
    second = getpass.getpass("Confirm password: ")
    if first != second:
        raise SystemExit("Passwords do not match")
    if len(first) < 8:
        raise SystemExit("Use at least 8 characters")
    return first


def main() -> None:
    parser = argparse.ArgumentParser(description="Create/promote a SPECTRA-UPI admin")
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", default=os.getenv("ADMIN_NAME", "SPECTRA Admin"))
    parser.add_argument("--phone", default=os.getenv("ADMIN_PHONE"))
    parser.add_argument("--role", choices=["admin", "moderator", "user"], default="admin")
    args = parser.parse_args()

    email = args.email.strip().lower()
    create_tables()
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            if not args.phone:
                raise SystemExit("--phone is required when creating a new user")
            if db.query(User).filter(User.phone == args.phone).first():
                raise SystemExit("That phone number is already registered")
            password = _password()
            user = User(
                full_name=args.name.strip(),
                email=email,
                phone=args.phone.strip(),
                hashed_password=hash_password(password),
                role=args.role,
            )
            db.add(user)
            print(f"Created {args.role} {email}")
        else:
            user.role = args.role
            if os.getenv("ADMIN_PASSWORD") or getattr(args, "reset_password", False):
                user.hashed_password = hash_password(_password())
                print("Password reset.")
            print(f"Promoted {email} to {args.role}")

        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    main()
