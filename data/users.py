import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session
import sqlalchemy_serializer as ss

from flask_login import UserMixin  
from .db_session import SqlAlchemyBase


class User(SqlAlchemyBase, UserMixin, ss.SerializerMixin):  
    __tablename__ = 'users'

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    
    surname = sa.Column(sa.String, nullable=True)
    name = sa.Column(sa.String, nullable=True)
    age = sa.Column(sa.Integer, nullable=True)
    
    email = sa.Column(sa.String, index=True, unique=True, nullable=True)
    hashed_password = sa.Column(sa.String, nullable=True)
    
    def set_password(self, password):
        import werkzeug.security as ws
        self.hashed_password = ws.generate_password_hash(password)
    
    def check_password(self, password):
        import werkzeug.security as ws
        return ws.check_password_hash(self.hashed_password, password)
    
    def __repr__(self):
        return f'<User {self.name} {self.surname}>'