from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker,declarative_base




DB_SERVER_NAME = 'RAJESH\\SQLEXPRESS'
DB_NAME = 'Trance'

URL_DATABASE = f"mssql+pyodbc://@{DB_SERVER_NAME}/{DB_NAME}?trusted_connection=yes&driver=ODBC+Driver+17+for+SQL+Server"

engine = create_engine(URL_DATABASE)

SessionLocal = sessionmaker(autocommit=False, autoflush=False,bind=engine)
Base = declarative_base()