"""
A module to simplify CRUD operations on the database
"""
from sqlalchemy.orm import Session
from . import models


def get_apps(session: Session):
    """
    Gets all apps saved in the the database
    """
    return session.query(models.App)


def get_app(session: Session, app_id: str):
    """
    Gets an app by its id from the database
    """
    return session.query(models.App).filter(models.App.id == app_id).first()


def create_app(session: Session, app: models.App):
    """
    Creates an app in the database
    """
    session.add(app)
    session.commit()


def delete_app(session: Session, app_id: str):
    """
    Delets an app by id in the database
    """
    app = session.query(models.App).filter_by(id=app_id).first()
    session.delete(app)

    session.commit()


def get_categories(session: Session):
    """
    Gets all existing app categories in the database
    """
    return session.query(models.Category)
