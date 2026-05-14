import sqlalchemy as sa
from .db_session import SqlAlchemyBase


class Favorite(SqlAlchemyBase):
    __tablename__ = 'favorites'

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'), nullable=False)
    kinopoisk_id = sa.Column(sa.Integer, nullable=False)

    __table_args__ = (sa.UniqueConstraint(
        'user_id', 'kinopoisk_id', name='unique_user_film'),)
