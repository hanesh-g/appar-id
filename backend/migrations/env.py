from alembic import context

from app import models  # noqa: F401
from app.config import Settings
from app.db import Base, make_engine


def run(connection):
    context.configure(connection=connection, target_metadata=Base.metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


provided_connection = context.config.attributes.get("connection")
if provided_connection is not None:
    run(provided_connection)
else:
    engine = make_engine(Settings().database_url.get_secret_value())
    with engine.connect() as connection:
        run(connection)
    engine.dispose()
