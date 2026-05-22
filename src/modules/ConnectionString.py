import configparser
import os
import sqlalchemy as db
from sqlalchemy import event
from sqlalchemy_utils import database_exists, create_database
from flask import current_app

_connection_string_cache = {}
_engine_cache = {}

def ConnectionString(database) -> str:
    global _connection_string_cache
    if database in _connection_string_cache:
        return _connection_string_cache[database]

    parser = configparser.ConfigParser(strict=False)
    # Use context manager for reading config
    with open('wg-dashboard.ini', "r") as f:
        parser.read_file(f)
    sqlitePath = os.path.join("db")
    if not os.path.isdir(sqlitePath):
        os.mkdir(sqlitePath)

    db_type = None
    if parser.has_section("Database") and parser.has_option("Database", "type"):
        db_type = parser.get("Database", "type")

    if db_type == "postgresql":
        cn = f'postgresql+psycopg://{parser.get("Database", "username", fallback="")}:{parser.get("Database", "password", fallback="")}@{parser.get("Database", "host", fallback="")}/{database}'
    elif db_type == "mysql":
        cn = f'mysql+pymysql://{parser.get("Database", "username", fallback="")}:{parser.get("Database", "password", fallback="")}@{parser.get("Database", "host", fallback="")}/{database}'
    else:
        cn = f'sqlite:///{os.path.join(sqlitePath, f"{database}.db")}'
    try:
        if not database_exists(cn):
            create_database(cn)
    except Exception as e:
        if hasattr(current_app, 'logger'):
            current_app.logger.error("Database error. Terminating...", exc_info=e)
        exit(1)
        
    _connection_string_cache[database] = cn
    return cn

def CreateEngine(connection_string, **kwargs) -> db.Engine:
    global _engine_cache
    if connection_string in _engine_cache:
        return _engine_cache[connection_string]
    
    engine = db.create_engine(connection_string, **kwargs)
    if engine.url.drivername == 'sqlite':
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.close()
            
    _engine_cache[connection_string] = engine
    return engine