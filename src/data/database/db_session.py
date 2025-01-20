"""
This module handles database initialization and session management for the application.
It provides functions to set up the database connection (`global_init`) and to create 
new sessions for interacting with the database (`create_session`).
"""
import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session
import sqlalchemy.ext.declarative as dec

SqlAlchemyBase = dec.declarative_base()
__factory = None


def global_init(db_file):
    """
    Initializes the database connection.
    
    :param db_file: Path to the database file
    """
    global __factory

    if __factory:
        return

    if not db_file or not db_file.strip():
        raise Exception("A valid database file must be specified.")

    conn_str = f'sqlite:///{db_file.strip()}?check_same_thread=False'

    engine = sa.create_engine(conn_str, echo=False)
    __factory = orm.sessionmaker(bind=engine)

    from . import __all_models
    SqlAlchemyBase.metadata.create_all(engine)


def create_session() -> Session:
    """
    Creates a new session for interacting with the database.
    
    :return: A new SQLAlchemy session
    """
    global __factory
    return __factory()
