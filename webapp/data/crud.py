from sqlalchemy.orm import Session

from typing import Iterable
from . import models


# TODO implement pagination when app list gets too big
def get_apps(session: Session):
    return session.query(models.App)


def get_app(session: Session, app_id: str):
    return session.query(models.App).filter(models.App.id == app_id).first()


def create_app(session: Session, app: models.App):

    session.add(app)
    session.commit()
