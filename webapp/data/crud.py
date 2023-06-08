from sqlalchemy.orm import Session

from . import models, schemas


def get_app(database: Session, app_id: str):
    return database.query(models.App).filter(models.App.id == app_id).first()


def create_app(database: Session, app: models.App):

    database.add(app)
    database.commit()
    database.refresh(app)
    return app


# def create_app_icon(database: Session, icon: schemas.IconCreate, app_id: str):
#     model = models.Icon(**icon.dict(), app=app_id)
#     database.add(model)
#     database.commit()
#     database.refresh(model)
#     return model
