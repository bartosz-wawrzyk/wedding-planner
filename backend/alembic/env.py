import asyncio
import os
import sys
from logging.config import fileConfig

from dotenv import load_dotenv
load_dotenv() 

from sqlalchemy import pool, text
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '../../')))

from app.db.base import Base

from app.modules.auth.models import User, RefreshToken
from app.modules.event.models import Event
from app.modules.guest.models import Guest
from app.modules.invitation.models import Invitation
from app.modules.table.models import Table
from app.modules.finance.models import Expense, Payment

config = context.config

db_url = os.environ.get("DATABASE_URL")
if db_url:
    config.set_main_option("sqlalchemy.url", db_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table_schema="wp",
        include_schemas=True,
    )

    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        version_table_schema="wp",
        include_schemas=True,
        include_object=lambda obj, name, type_, reflected, compare_to: 
            not (type_ == "table" and obj.schema != "wp")
    )

    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.execute(text("CREATE SCHEMA IF NOT EXISTS wp"))
        await connection.commit()
        
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

def run_migrations_online() -> None:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        loop.create_task(run_async_migrations())
    else:
        asyncio.run(run_async_migrations())

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()