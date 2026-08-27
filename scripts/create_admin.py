import getpass
import sys

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.db.database import SessionLocal
from app.models.user import User
from app.services.auth import hash_password


def main() -> None:
    print("=== Create Admin User ===")

    username = input(
        "Username: "
    ).strip()

    email = input(
        "Email: "
    ).strip()

    password = getpass.getpass(
        "Password: "
    )

    password_confirm = getpass.getpass(
        "Confirm password: "
    )

    # ------------------------------------
    # Validation
    # ------------------------------------

    if not username:
        print(
            "Username must not be empty."
        )
        sys.exit(1)

    if not email:
        print(
            "Email must not be empty."
        )
        sys.exit(1)

    if not password:
        print(
            "Password must not be empty."
        )
        sys.exit(1)

    if password != password_confirm:
        print(
            "Passwords do not match."
        )
        sys.exit(1)

    if len(password) < 12:
        print(
            "Password must be at least "
            "12 characters."
        )
        sys.exit(1)

    # ------------------------------------
    # Database
    # ------------------------------------

    db = SessionLocal()

    try:
        existing_user = (
            db.query(User)
            .filter(
                (
                    User.username
                    == username
                )
                | (
                    User.email
                    == email
                )
            )
            .first()
        )

        if existing_user is not None:
            print(
                "Username or email "
                "already exists."
            )
            sys.exit(1)

        user = User(
            username=username,
            email=email,
            password_hash=hash_password(
                password
            ),
            role="admin",
            is_active=True,
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        print()
        print(
            f"Admin user created. "
            f"id={user.id}, "
            f"username={user.username}"
        )

    except IntegrityError:
        db.rollback()
        print(
            "Username or email "
            "already exists."
        )
        sys.exit(1)

    except SQLAlchemyError as exc:
        db.rollback()
        print(
            f"Failed to create admin: "
            f"{exc}"
        )
        sys.exit(1)

    finally:
        db.close()


if __name__ == "__main__":
    main()