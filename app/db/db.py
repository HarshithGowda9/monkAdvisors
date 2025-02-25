from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Sequence, Boolean, Float
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.sql.expression import text
from sqlalchemy.sql import func
from app import config
from datetime import datetime

settings = config.get_postgres_settings()
SQLALCHEMY_DATABASE_URL_POSTGRES = 'postgresql://'+settings.POSTGRES_USER+':'+settings.POSTGRES_PASSWORD+'@'+settings.POSTGRES_HOST+'/'+settings.POSTGRES_DB_NAME
engine = create_engine(SQLALCHEMY_DATABASE_URL_POSTGRES)
sessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'  
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, nullable=False)
    password = Column(String, nullable=False)
    is_active = Column(Boolean, nullable=False)
    time_created = Column(TIMESTAMP(timezone=True), nullable = False, server_default=text('now()'))
    time_updated = Column(TIMESTAMP(timezone=True), onupdate=text('now()'))
    roles = relationship('userRole', back_populates='user')

class Role(Base):
    __tablename__ = 'roles'
    id = Column(Integer, primary_key=True, autoincrement=True)
    role_name = Column(String, nullable=False)
    users = relationship('userRole', back_populates= 'role')
    permissions = relationship('rolePermission', back_populates= 'role')

class Permission(Base):
    __tablename__ = 'permissions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    permission_name = Column(String, nullable=False)
    roles = relationship('rolePermission', back_populates= 'permission')

class UserRole(Base):
    __tablename__ = 'user_role'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    role_id = Column(Integer, ForeignKey('roles.id', ondelete='CASCADE'), nullable=False)
    user = relationship('User', back_populates='roles')
    role = relationship('Role', back_populates='users')

class RolePermission(Base):
    __tablename__ = 'role_permission'
    id = Column(Integer, primary_key=True, autoincrement=True)
    role_id = Column(Integer, ForeignKey('roles.id', ondelete='CASCADE'))
    permission_id = Column(Integer, ForeignKey('permissions.id', ondelete='CASCADE'))
    role = relationship('Role', back_populates='permissions')
    permission = relationship('Permission', back_populates='roles')

class StrategyPerformance(Base):
    __tablename__ = 'strategy_performance'  
    id = Column(Integer, primary_key=True, autoincrement=True)
    strategy_name = Column(String, nullable=False)
    entry_price = Column(Float, nullable=False)
    entry_time = Column(TIMESTAMP(timezone=True), nullable = False)
    target = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    instrument = Column(String, nullable=True)
    options_trading_call = Column(String, nullable=True)
    expected_price = Column(Float, nullable=False)


def get_db():
    db = sessionLocal()
    try:
        yield db
    finally:
        db.close()