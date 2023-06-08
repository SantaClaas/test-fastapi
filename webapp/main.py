from typing import Annotated
from os.path import dirname, abspath, join
from fastapi import FastAPI, Form, Depends, Request
from fastapi.responses import FileResponse, RedirectResponse, HTMLResponse
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
from fastapi.templating import Jinja2Templates

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


current_directory = dirname(abspath(__file__))
# Static files
static_path = join(current_directory, "static")

app.mount("/ui", StaticFiles(directory=static_path), name="ui")

# Templating
template_path = join(current_directory, "templates")
templates = Jinja2Templates(directory=template_path)

# Routes


@app.get('/')
def root():
    html_path = join(static_path, "index.html")
    return FileResponse(html_path)


@app.get("/apps/{app_id}", response_class=HTMLResponse)
def view_app(request: Request, app_id: str, database: Session = Depends(get_database)):
    # Get app
    app = crud.get_app(database, app_id)

    if app == None:
        # TODO return not found page (can I do that with 404 status code and the browser not breaking?)
        return templates.TemplateResponse("app.html", {"request": request, "id": app.id, "name": app.name})

    # Render template
    return templates.TemplateResponse("app.html", {"request": request, "id": app.id, "name": app.name})


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
        # TODO use templating to add error of already created with url to app page
        return RedirectResponse(f"/apps/{app_id}", status_code=status.HTTP_303_SEE_OTHER)

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
