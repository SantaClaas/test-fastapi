from typing import Annotated
from os.path import dirname, abspath, join
from fastapi import FastAPI, Form, Depends
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from urllib.request import urlopen
from urllib.parse import urlparse
import json
import starlette.status as status

# from sql_app import crud, models, schemas
from .sql_app.models import Base
from .sql_app import schemas, crud, models
from .sql_app.database import SessionLocal, engine
from sqlalchemy.orm import Session

# Create tables
# We just delete and recreate the database every new start and after changes to iterate quickly. In a real app we would
# have to implement migrations (apparantly this is posible with "Alembic")
Base.metadata.create_all(bind=engine)

# App initialization(?)
app = FastAPI()

# Database dependency


def get_database():
    database = SessionLocal()
    try:
        yield database
    finally:
        database.close()


# Static files
current_dir = dirname(abspath(__file__))
static_path = join(current_dir, "static")

app.mount("/ui", StaticFiles(directory=static_path), name="ui")

temp_app = None


@app.get('/')
def root():
    html_path = join(static_path, "index.html")
    return FileResponse(html_path)


@app.get("/apps/{app_id}")
def view_app(app_id: str):
    return {"app_id": app_id}


@app.post("/apps")
async def create_app(url: Annotated[str, Form(alias="url")], database: Session = Depends(get_database)):
    # TODO url validation
    # An application is defined by the manifest so these terms can be used interchangibly

    # We use the host as the id for the app
    # TODO find a way to avoid duplicate apps from hosts that have the same web manifest by using a more qualified
    # comparison of manifests like comparing a hash or other distinguishing characteristics
    components = urlparse(url)
    app_id = components.netloc

    # If app exists, return add app view with error message
    if crud.get_app(database, app_id):
        # TODO use templating to add error
        html_path = join(static_path, "index.html")
        return FileResponse(html_path)

    # Get manifest from user provided url
    # TODO request error handling
    response = urlopen(url)
    # TODO validate manifest
    # TODO handle deserialization error
    manifest = json.loads(response.read())
    print(type(manifest["icons"]))

    # Persist application to database
    app = models.App(
        id=app_id, name=manifest["name"], start_url=manifest["start_url"], description=manifest["description"])
    crud.create_app(database, app)

    # Return user to new page for app

    return RedirectResponse(f"/apps/{app_id}", status_code=status.HTTP_303_SEE_OTHER)
