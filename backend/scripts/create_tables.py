# This script is used to create the database and stamp it with the latest revision.
from pathlib import Path

# get the environment variables
from alembic import command
from alembic.config import Config

# https://alembic.sqlalchemy.org/en/latest/cookbook.html#building-an-up-to-date-database-from-scratch
from domainwizard.models import Base, Session, engine
from sqlalchemy import text

with Session.begin() as session:
    session.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

Base.metadata.create_all(engine)

# then, load the Alembic configuration and generate the
# version table, "stamping" it with the most recent rev:

script_location = Path(__file__)
alembic_cfg = Config(script_location.parents[1] / "alembic.ini")
command.stamp(alembic_cfg, "head")
