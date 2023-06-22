"""
The main starting point and module of the web app
"""
from os.path import dirname, abspath, join
from typing import Annotated
from urllib.parse import urlparse

import uvicorn
from fastapi import FastAPI, Form, Depends, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette import status
from sqlalchemy.orm import Session

from wappstore.url import ensure_is_absolute
from .data.seeding import seed_apps
from .webmanifest import fetch_app_details, save_to_database
from .data.database import SessionLocal, engine
from .data.models import Base
from .data import crud


# Create tables
# We don't support migrations currently. Just delete the database
Base.metadata.create_all(bind=engine)


# Database dependency

def get_session():
    """
    Used for dependency in route functions to get database access
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def lifespan(_: FastAPI):
    """
    Lifespan method for FastAPI to allow for code to run before start and after shutdown
    """
    # Seed data
    seed_apps()
    yield
    # Run code after shutdown here


# App initialization
app = FastAPI(lifespan=lifespan)

current_directory = dirname(abspath(__file__))
# Static files like CSS
static_path = join(current_directory, "static")

app.mount("/static", StaticFiles(directory=static_path), name="static")

# Templating
template_path = join(current_directory, "templates")
templates = Jinja2Templates(directory=template_path)


# Routes


@app.get('/', response_class=HTMLResponse)
@app.get('/apps', response_class=HTMLResponse)
@app.get('/apps/delete', response_class=HTMLResponse)
def view_index(request: Request, database: Session = Depends(get_session)):
    """
    Returns the overview of all apps. Can also return the overview in delete mode
    """
    apps = map(lambda app:
               {"name": app.name,
                "description": app.description,
                "icon_url": app.get_primary_icon_url(),
                "id": app.id,
                "categories": map(lambda category: category.name, app.categories)},
               crud.get_apps(database))

    return templates.TemplateResponse("apps/index.html", {"request": request, "apps": apps, "is_delete": request.url.path == "/apps/delete"})


@app.get("/apps/new")
def view_new_app(request: Request):
    """
    Returns the page to add a new app
    """
    return templates.TemplateResponse("apps/new.html", {"request": request})


@app.get('/apps/delete/{app_id:path}')
def delete_app(app_id: str, database: Session = Depends(get_session)):
    """
    Endpoint that if invoked and delets the app specified by id. Returns the app overview in delete mode
    """
    crud.delete_app(database, app_id)
    return RedirectResponse("/apps/delete", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/apps/{app_id:path}", response_class=HTMLResponse)
def view_app(request: Request, app_id: str, database: Session = Depends(get_session)):
    """
    Get the details page for an app
    """

    # Get app
    web_app = crud.get_app(database, app_id)

    if web_app is None:
        # TODO return not found page (can I do that with 404 status code and the browser not breaking?)
        return templates.TemplateResponse("apps/detail.html", {"request": request, "id": web_app.id, "name": web_app.name})

    # Build image source url
    source = web_app.get_primary_icon_url()

    for screenshot in web_app.screenshots:
        screenshot.source = ensure_is_absolute(screenshot.source, web_app.id)

    # Render template
    return templates.TemplateResponse(
        "apps/detail.html",
        {"request": request,
         "id": web_app.id,
         "name": web_app.name,
         "description": web_app.description,
         "source": source,
         "screenshots": web_app.screenshots,
         "categories": web_app.categories,
         "start_url": ensure_is_absolute(web_app.start_url, web_app.id),
         "manifest_url": ensure_is_absolute(web_app.manifest_url, web_app.id)
         })


@app.post("/apps")
def create_app(request: Request, url: Annotated[str, Form(alias="url")], session: Session = Depends(get_session)):
    """
    Endpoint where the form for app creation posts to. Creates a new app and redirects to in on success.
    Returns to add app page with error on failure
    """

    # TODO url validation
    # An application is defined by the manifest so these terms can be used interchangibly

    # We use the host as the id for the app
    # TODO find a way to avoid duplicate apps from hosts that have the same web manifest by using a more qualified
    # comparison of manifests like comparing a hash or other distinguishing characteristics
    components = urlparse(url)
    app_id = components.netloc + components.path

    # If app exists, return add app view with error message
    if crud.get_app(session, app_id):
        # TODO use templating to add error of already created with url to app page
        return RedirectResponse(f"/apps/{app_id}", status_code=status.HTTP_303_SEE_OTHER)

    manifest_or_error = fetch_app_details(url)
    if manifest_or_error == "Could not find manifest url" or manifest_or_error == "Could not find manifest url" or manifest_or_error == "Invalid response type":
        # TODO errror UI
        return templates.TemplateResponse("apps/new.html", {"request": request})

    manifest, manifest_url = manifest_or_error
    save_to_database(session, app_id, manifest_url, manifest)

    # Return user to new page for app

    return RedirectResponse(f"/apps/{app_id}", status_code=status.HTTP_303_SEE_OTHER)


# Run with "poetry run python -m wappstore.main"
# Based on https://stackoverflow.com/questions/63177681/is-there-a-difference-between-running-fastapi-from-uvicorn-command-in-dockerfile
if __name__ == "__main__":
    uvicorn.run("wappstore.main:app")
