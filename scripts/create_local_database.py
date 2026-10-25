"""Native Windows PostgreSQL setup. No Ubuntu or Docker required."""
import getpass
import os
from pathlib import Path

import psycopg
from dotenv import dotenv_values
from psycopg import sql

root = Path(__file__).resolve().parents[1]
values = dotenv_values(root / ".env")
if values.get("APP_ENV") != "local":
    raise SystemExit("This helper is only for a local database")
password = values.get("LOCAL_DB_PASSWORD")
if not password:
    raise SystemExit("Run configure_local.py first")
admin_password = getpass.getpass("Local PostgreSQL administrator password (hidden): ")
host = os.environ.get("LOCAL_PG_HOST", "localhost")
with psycopg.connect(host=host, port=5432, user="postgres", password=admin_password,
                     dbname="postgres", autocommit=True) as connection:
    exists = connection.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", ("apaar_app",)).fetchone()
    if exists:
        raise SystemExit("apaar_app already exists. Preserved it; use its existing credentials in .env instead.")
    for database in ["apaar", "apaar_test"]:
        if connection.execute("SELECT 1 FROM pg_database WHERE datname = %s", (database,)).fetchone():
            raise SystemExit(f"{database} already exists. Preserved it; choose a fresh local target.")
    connection.execute(sql.SQL("CREATE ROLE {} LOGIN PASSWORD {}").format(sql.Identifier("apaar_app"), sql.Literal(password)))
    for database in ["apaar", "apaar_test"]:
        connection.execute(sql.SQL("CREATE DATABASE {} OWNER {}").format(sql.Identifier(database), sql.Identifier("apaar_app")))
print("Created isolated local application/test databases. No existing database was changed.")
