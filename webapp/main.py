from typing import Annotated
from os.path import dirname, abspath, join
from fastapi import FastAPI, Form, Depends, Request
from fastapi.responses import FileResponse, RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from urllib.request import urlopen
from urllib.parse import urlparse, urlunsplit
import json
import starlette.status as status

from .data.models import Base
from .data import schemas, crud, models
from .data.database import SessionLocal, engine
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

app.mount("/static", StaticFiles(directory=static_path), name="static")

# Templating
template_path = join(current_directory, "templates")
templates = Jinja2Templates(directory=template_path)

# Routes


def getIconUrl(app: models.App):
    # We use the last one declared that is appropiate as per spec https://w3c.github.io/manifest/#icons-member
    # Appropiate for us in this case is purpose not monochrome and maskable
    icon = list(filter(lambda icon: icon.purpose == "any", app.icons))[-1]

    url = urlparse(icon.source)
    # If the url is absolute (not relative/has a host)
    if url.netloc:
        return icon.source

    # Else substitute the host
    return urlunsplit(("https", app.id, icon.source, "", ""))


@app.get('/', response_class=HTMLResponse)
@app.get('/apps', response_class=HTMLResponse)
def root(request: Request, database: Session = Depends(get_database)):

    apps = map(lambda app:
               {"name": app.name,
                "description": app.description,
                "icon_url": getIconUrl(app),
                "id": app.id,
                "categories": map(lambda category: category.name, app.categories)},
               crud.get_apps(database))

    return templates.TemplateResponse("apps/index.html", {"request": request, "apps": apps})


@app.get("/apps/new")
def view_new_app(request: Request):
    return templates.TemplateResponse("apps/new.html", {"request": request})


@app.get("/apps/{app_id}", response_class=HTMLResponse)
def view_app(request: Request, app_id: str, database: Session = Depends(get_database)):
    # Get app
    app = crud.get_app(database, app_id)

    if app is None:
        # TODO return not found page (can I do that with 404 status code and the browser not breaking?)
        return templates.TemplateResponse("apps/detail.html", {"request": request, "id": app.id, "name": app.name})

    # TODO check if image url is absolute or relative
    # Build image source url
    source = getIconUrl(app)

    # Render template
    return templates.TemplateResponse(
        "apps/detail.html",
        {"request": request,
         "id": app.id,
         "name": app.name,
         "description": app.description,
         "source": source
         })


def createIconFor(app_id: str):
    return lambda json: models.Icon(
        app_id=app_id,
        source=json["src"],
        sizes=json["sizes"],
        type=json["type"],
        label=json.get("label", None),
        purpose=json.get("purpose", "any"))


@app.post("/apps")
def create_app(url: Annotated[str, Form(alias="url")], session: Session = Depends(get_database)):
    # TODO url validation
    # An application is defined by the manifest so these terms can be used interchangibly

    # We use the host as the id for the app
    # TODO find a way to avoid duplicate apps from hosts that have the same web manifest by using a more qualified
    # comparison of manifests like comparing a hash or other distinguishing characteristics
    components = urlparse(url)
    app_id = components.netloc

    # If app exists, return add app view with error message
    if crud.get_app(session, app_id):
        # TODO use templating to add error of already created with url to app page
        return RedirectResponse(f"/apps/{app_id}", status_code=status.HTTP_303_SEE_OTHER)

    # Get manifest from user provided url
    # TODO request error handling
    response = urlopen(url)
    # TODO validate manifest
    # TODO handle deserialization error

    manifest = json.loads(response.read())

    # Persist icons
    icons = manifest["icons"]
    icons = list(map(createIconFor(app_id), icons))

    # Persist categories
    # IDK how to avoid unique insert issue with the ORM so we filter categories to include only unique categories
    existing_categories = frozenset(map(
        lambda category: category.name, crud.get_categories(session)))

    categories = filter(
        lambda category: category not in existing_categories,
        manifest.get("categories", []))

    # To model
    categories = list(map(lambda category: models.Category(
        name=category), categories))

    # Persist application to database
    app = models.App(
        id=app_id,
        manifest_url=url,
        name=manifest["name"],
        icons=icons,
        start_url=manifest["start_url"],
        description=manifest["description"],
        categories=categories)

    # TODO use transaction to cancel creation in case icon write fails so we don't have an app without icons
    crud.create_app(session, app)

    # Return user to new page for app

    return RedirectResponse(f"/apps/{app_id}", status_code=status.HTTP_303_SEE_OTHER)
