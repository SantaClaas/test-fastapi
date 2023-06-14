import uvicorn
from typing import Annotated
from os.path import dirname, abspath, join
from fastapi import FastAPI, Form, Depends, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from urllib.request import urlopen
from urllib.parse import urlparse, urlunsplit
import json
import starlette.status as status

from .data.models import Base
from .data import crud, models
from .data.database import SessionLocal, engine
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
import httpx

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

# Ensures the provided url is absolute. If not it uses the provided host to form an absolute url


def ensure_is_absolute(url: str, host: str):
    is_absolute = bool(urlparse(url).netloc)
    if is_absolute:
        return url
    # TODO write test that this includes fragments and queries
    return urlunsplit(("https", host, url, "", ""))


def getIconUrl(app: models.App):
    # We use the last one declared that is appropiate as per spec https://w3c.github.io/manifest/#icons-member
    # Appropiate for us in this case is purpose not monochrome and maskable
    icon = list(filter(lambda icon: icon.purpose == "any", app.icons))[-1]

    return ensure_is_absolute(icon.source, app.id)


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
    web_app = crud.get_app(database, app_id)

    if web_app is None:
        # TODO return not found page (can I do that with 404 status code and the browser not breaking?)
        return templates.TemplateResponse("apps/detail.html", {"request": request, "id": web_app.id, "name": web_app.name})

    # TODO check if image url is absolute or relative
    # Build image source url
    source = getIconUrl(web_app)

    # Render template
    return templates.TemplateResponse(
        "apps/detail.html",
        {"request": request,
         "id": web_app.id,
         "name": web_app.name,
         "description": web_app.description,
         "source": source,
         "screenshots": web_app.screenshots
         })


def createIconFor(app_id: str):
    return lambda json: models.Icon(
        app_id=app_id,
        source=json["src"],
        sizes=json["sizes"],
        type=json["type"],
        label=json.get("label", None),
        purpose=json.get("purpose", "any"))


def createScreenshotFor(app_id: str):
    return lambda json: models.Screenshot(
        app_id=app_id,
        source=json["src"],
        sizes=json["sizes"],
        type=json["type"])


def extract_manifest_url(content: str):
    # Extract manifest url
    # We need to find something like <link rel="manifest" href="..."> but attributes can be in different order
    # TODO might need to add check because simple quotes are allowed too?
    relationship_index = content.find("rel=\"manifest\"")
    if relationship_index == -1:
        # A tuple of result and error message
        return None, "Could not find manifest url"

    # Define boundaries
    element_end = content.find(">", relationship_index)

    # Only search in string before relationship since relationship is in the middle of the link element
    element_start = content.rfind("<", 0, relationship_index)

    link_element = content[element_start:element_end]

    href_key = "href=\""
    # Find href in link element
    href_key_start = link_element.find(href_key)

    if href_key_start == -1:
        # TODO fail if invalid and no href
        return None, "Invalid manifest link, missing href"

    href_key_end = href_key_start + len(href_key)
    # Find end of href
    end_href = link_element.find('"', href_key_end)

    href = link_element[href_key_end:end_href]
    return href, None


@app.post("/apps")
def create_app(request: Request, url: Annotated[str, Form(alias="url")], session: Session = Depends(get_database)):
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

    response = httpx.get(url)

    # Twitter sets a cookie in a redirect
    # TODO change to "if page wants to set cookie"
    # TODO add maximum retry count to not loop endlessly
    while response.status_code == httpx.codes.FOUND:
        new_url = response.headers["location"]
        cookie: str = response.headers.get("Set-Cookie")
        # Use same host as before if it is relative
        new_url = ensure_is_absolute(new_url, components.netloc)

        # TODO fail if no cookie
        headers = {"Cookie": cookie.split(';')[0]}
        response = httpx.get(url, headers=headers)

    # TODO fail if no content type
    # If response is HTML, find url to manifest
    content_type: str = response.headers.get("content-type")

    if content_type.startswith("text/html"):

        # This should be improved later as we read and allocate the whole content but we only need a small section from
        # the head
        content = response.text
        manifest_url, error = extract_manifest_url(content)
        if error is not None:
            # TODO add error to template
            return templates.TemplateResponse("apps/new.html", {"request": request})

        # Get manifest
        manifest_url = ensure_is_absolute(manifest_url, components.netloc)
        response = httpx.get(manifest_url)
        content_type = response.headers.get("content-type")
        # It is still technically possible that the server returns a valid manifest with wrong content type but we
        # assume this is very unlikely
        if not content_type.startswith("application/manifest+json") and not content_type.startswith("application/json"):
            # TODO error invalid response
            return templates.TemplateResponse("apps/new.html", {"request": request})

    # else if response is json+manifest, json, try deserialize manifest
    # TODO validate manifest
    # TODO handle deserialization error
    manifest = json.loads(response.text)

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

    # Persist screenshots
    screenshots = list(map(createScreenshotFor(app_id),
                       manifest.get("screenshots", [])))

    # Persist application to database
    web_app = models.App(
        id=app_id,
        manifest_url=url,
        name=manifest["name"],
        icons=icons,
        start_url=manifest["start_url"],
        description=manifest["description"],
        categories=categories,
        screenshots=screenshots)

    crud.create_app(session, web_app)

    # Return user to new page for app

    return RedirectResponse(f"/apps/{app_id}", status_code=status.HTTP_303_SEE_OTHER)


# Run with "poetry run python -m wappstore.main"
# Based on https://stackoverflow.com/questions/63177681/is-there-a-difference-between-running-fastapi-from-uvicorn-command-in-dockerfile
if __name__ == "__main__":
    uvicorn.run("wApp.main:app")
