from sqlalchemy.orm import Session

from typing import Iterable
from . import models


# TODO implement pagination when app list gets too big
def get_apps(database: Session):
    return database.query(models.App)


def get_app(database: Session, app_id: str):
    return database.query(models.App).filter(models.App.id == app_id).first()


def create_app(database: Session, app: models.App):

    database.add(app)
    database.commit()


def create_app_icons(database: Session, icons: Iterable[models.Icon]):
    database.add_all(icons)
    database.commit()
