from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Parent class for every database model. Each subclass maps to one table."""

    pass