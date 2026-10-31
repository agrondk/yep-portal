import argparse
import getpass
from datetime import UTC, date, datetime

from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.modules.core.auth_service import normalize_email
from app.modules.core.models import Organization, Role, RoleAssignment, ScopeType, User, UserStatus


def admin_create(email: str | None) -> None:
    address = normalize_email(email or input("Administrator email: "))
    password = getpass.getpass("Password (minimum 12 characters): ")
    if len(password) < 12:
        raise SystemExit("Password must contain at least 12 characters.")
    now = datetime.now(UTC)
    with SessionLocal.begin() as db:
        if db.scalar(select(User.id).where(User.email == address)) is not None:
            raise SystemExit("A user with this email already exists.")
        organization = db.scalar(select(Organization))
        if organization is None:
            organization = Organization(
                name="Young Engineers Prishtina",
                timezone="Europe/Belgrade",
                default_locale="sq",
                reporting_year_start_month=1,
                created_at=now,
            )
            db.add(organization)
            db.flush()
        user = User(
            email=address,
            password_hash=hash_password(password),
            locale="sq",
            status=UserStatus.ACTIVE,
            mfa_enabled=False,
            email_verified_at=now,
            created_at=now,
        )
        db.add(user)
        db.flush()
        db.add(
            RoleAssignment(
                user_id=user.id,
                role=Role.OWNER_ADMIN,
                scope_type=ScopeType.ORGANIZATION,
                scope_id=None,
                valid_from=date.today(),
                granted_by=user.id,
                created_at=now,
            )
        )
    print(f"Administrator created: {address}")


def seed_demo() -> None:
    print("Demo seed skeleton ready. Business-module demo records are added by their modules.")


def main() -> None:
    parser = argparse.ArgumentParser(prog="yep-portal")
    subcommands = parser.add_subparsers(dest="command", required=True)
    admin = subcommands.add_parser("admin-create")
    admin.add_argument("--email")
    subcommands.add_parser("seed-demo")
    args = parser.parse_args()
    if args.command == "admin-create":
        admin_create(args.email)
    else:
        seed_demo()


if __name__ == "__main__":
    main()
