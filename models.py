from sqlalchemy import Column, Integer, String, Sequence
from sqlalchemy.ext.declarative import declarative_base

from config import USER_TABLE_NAME

Base = declarative_base()


class User(Base):

	__tablename__ = USER_TABLE_NAME

	id = Column('id', Integer, Sequence('users_seq'), primary_key=True)
	email = Column('email', String)
	password = Column('password', String)
