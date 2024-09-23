from domainwizard.config import config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

if db_url := config.get("DB_URL"):
    engine = create_engine(db_url, isolation_level="AUTOCOMMIT")
else:
    raise ValueError("DB_URL environment variable not set. Cannot initialize database engine.")

Session = sessionmaker(bind=engine)
