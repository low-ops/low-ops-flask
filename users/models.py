from datetime import datetime, timezone

from config.database import db


def _utcnow():
    return datetime.now(timezone.utc)


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(254), unique=True, nullable=False)
    avatar = db.Column(db.Text, nullable=True)
    avatar_key = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=_utcnow,
        onupdate=_utcnow,
        nullable=False,
    )

    def __str__(self):
        return self.name
