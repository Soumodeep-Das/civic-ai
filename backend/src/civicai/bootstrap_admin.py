from getpass import getpass

from sqlalchemy import select
from sqlalchemy.orm import Session

from civicai.auth import create_user, record_audit
from civicai.config import database_url
from civicai.database import build_engine
from civicai.domain import MunicipalRole
from civicai.models import MunicipalUser
from civicai.schemas import MunicipalUserCreate


def main() -> None:
    engine = build_engine(database_url())
    try:
        with Session(engine) as session:
            existing = session.scalar(select(MunicipalUser).where(
                MunicipalUser.role == MunicipalRole.ADMIN.value,
                MunicipalUser.is_active.is_(True),
            ))
            if existing is not None:
                raise SystemExit("An active municipal administrator already exists; bootstrap refused.")
            username = input("Administrator username: ").strip()
            password = getpass("Password (12-128 characters): ")
            confirmation = getpass("Confirm password: ")
            if password != confirmation:
                raise SystemExit("Passwords do not match.")
            user = create_user(session, MunicipalUserCreate(
                username=username, password=password, role=MunicipalRole.ADMIN
            ))
            record_audit(session, "account_created", actor_id=user.user_id, subject_id=user.user_id)
            session.commit()
            print(f"Municipal administrator '{user.username}' created.")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
