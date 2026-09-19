from alembic import context
from sqlalchemy import create_engine, pool

from civicai.config import database_url
from civicai.database import Base
from civicai import models  # noqa: F401 -- registers metadata

target_metadata = Base.metadata
# Programmatic test override; normal CLI always reads DATABASE_URL.
url = context.config.attributes.get("database_url") or database_url()

if context.is_offline_mode():
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    engine = create_engine(url, poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()
