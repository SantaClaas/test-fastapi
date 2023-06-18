import uvicorn
from typing import Annotated
from os.path import dirname, abspath, join
from fastapi import FastAPI, Form, Depends, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from urllib.parse import urlparse, urlunsplit, urljoin
import starlette.status as status
from .data.models import Base
from .data import crud, models
from .data.database import SessionLocal, engine
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
import httpx
from .models import ManifestSchema, Manifest

# Create tables
# We just delete and recreate the database every new start and after changes to iterate quickly. In a real app we would
# have to implement migrations (apparantly this is posible with "Alembic")
Base.metadata.create_all(bind=engine)


def fetch_app_details(user_provided_url: str):
    # Get manifest from user provided url
    client = httpx.Client()

    # Twitter sets a cookie in a redirect, httpx seems to set the cookie automatically
    request = client.build_request("GET", user_provided_url)
    while request is not None:
        response = client.send(request)
        request = response.next_request

    # TODO fail if no content type
    # If response is HTML, find url to manifest
    content_type: str = response.headers.get("content-type")
    if content_type.startswith("text/html"):
        # This should be improved later as we read and allocate the whole content but we only need a small section from
        # the head
        content = response.text
        new_manifest_url, error = extract_manifest_url(content)
        if error is not None:
            # TODO add error to template
            return error

        # Get manifest
        # new_manifest_url = ensure_is_absolute(new_manifest_url, with_path)
        # Ensure is absolute
        new_manifest_url = urljoin(user_provided_url, new_manifest_url)
        response = client.get(new_manifest_url, follow_redirects=True)
        content_type = response.headers.get("content-type")
        user_provided_url = new_manifest_url
        # It is still technically possible that the server returns a valid manifest with wrong content type but we
        # assume this is very unlikely
        if not content_type.startswith("application/manifest+json") and not content_type.startswith("application/json"):
            return "Invalid response type"

    # else if response is json+manifest, json, try deserialize manifest
    # TODO validate manifest
    # TODO handle deserialization error
    schema = ManifestSchema()
    result: Manifest = schema.loads(response.text)
    return result, str(response.url)


def save_to_database(session: Session, app_id: str, manifest_url: str, manifest: Manifest):
    # Persist icons
    icons = list(
        map(
            lambda icon: models.Icon(
                app_id=app_id,
                source=icon.src,
                sizes=icon.sizes,
                type=icon.type,
                label=icon.label,
                purpose=icon.purpose),
            manifest.icons))

    # Persist categories
    # IDK how to avoid unique insert issue with the ORM so we filter categories to include only unique categories
    existing_categories = frozenset(map(
        lambda category: category.name, crud.get_categories(session)))

    categories = filter(
        lambda category: category not in existing_categories,
        manifest.categories)

    # To model
    categories = list(map(lambda category: models.Category(
        name=category), categories))

    # Persist screenshots

    screenshots = list(
        map(lambda screenshot: models.Screenshot(
            app_id=app_id,
            source=screenshot.src,
            sizes=screenshot.sizes,
            type=screenshot.type),
            manifest.screenshots))

    # Persist application to database
    web_app = models.App(
        id=app_id,
        manifest_url=manifest_url,
        name=manifest.name,
        icons=icons,
        start_url=manifest.start_url,
        description=manifest.description,
        categories=categories,
        screenshots=screenshots)

    crud.create_app(session, web_app)


def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


apps_to_seed = [
    # Twitter uses redirect to set cookie
    "twitter.com",
    "pass.claas.dev",
    "social.claas.dev",
    "yqnn.github.io/svg-path-editor/",
    "jakearchibald.github.io/svgomg/",
    "youtube.com",
    "coronavirus.app",
    "recorder.google.com",
    "notepad.js.org",
    "squoosh.app"
]

# Prepend scheme which should always be https
apps_to_seed = map(
    lambda app_id: (urlunsplit(("https", app_id, "", "", ""))),
    apps_to_seed)


def seed_apps():
    session = SessionLocal()
    for url in apps_to_seed:
        components = urlparse(url)
        # App id should be host and path
        app_id = components.netloc + components.path
        if crud.get_app(session, app_id):
            continue

        print("Seeding", url)
        manifest_or_error = fetch_app_details(url)
        if isinstance(manifest_or_error, str):
            # Error logging is probably done differently but for now just print
            print(
                f"Error while seeding {app_id}", manifest_or_error)

            continue

        manifest, manifest_url = manifest_or_error
        save_to_database(session, app_id, manifest_url, manifest)

    session.close()


def lifespan(app: FastAPI):
    # Seed data
    seed_apps()
    yield


# App initialization(?)
app = FastAPI(lifespan=lifespan)

# Database dependency


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


def getPrimaryIconUrl(app: models.App):
    # We use the last one declared that is appropiate as per spec https://w3c.github.io/manifest/#icons-member
    # Appropiate for us in this case is purpose not monochrome and maskable
    icon = list(
        filter(lambda icon: "any" in icon.purpose.split(), app.icons))[-1]

    return ensure_is_absolute(icon.source, app.id)


@app.get('/', response_class=HTMLResponse)
@app.get('/apps', response_class=HTMLResponse)
@app.get('/apps/delete', response_class=HTMLResponse)
def root(request: Request, database: Session = Depends(get_session)):

    apps = map(lambda app:
               {"name": app.name,
                "description": app.description,
                "icon_url": getPrimaryIconUrl(app),
                "id": app.id,
                "categories": map(lambda category: category.name, app.categories)},
               crud.get_apps(database))

    return templates.TemplateResponse("apps/index.html", {"request": request, "apps": apps, "is_delete": request.url.path == "/apps/delete"})


@app.get("/apps/new")
def view_new_app(request: Request):
    return templates.TemplateResponse("apps/new.html", {"request": request})


@app.get('/apps/delete/{app_id:path}')
def delete_app(app_id: str, database: Session = Depends(get_session)):
    crud.delete_app(database, app_id)
    return RedirectResponse("/apps/delete", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/apps/{app_id:path}", response_class=HTMLResponse)
def view_app(request: Request, app_id: str, database: Session = Depends(get_session)):
    # Get app
    web_app = crud.get_app(database, app_id)

    if web_app is None:
        # TODO return not found page (can I do that with 404 status code and the browser not breaking?)
        return templates.TemplateResponse("apps/detail.html", {"request": request, "id": web_app.id, "name": web_app.name})

    # Build image source url
    source = getPrimaryIconUrl(web_app)

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


def find_manifest_rel(content: str):

    for rel_kind in ["rel=\"manifest\"", "rel=manifest", "rel='manifest'"]:
        index = content.find(rel_kind)
        if index != -1:
            return index

    return -1


def extract_href_from_link(link_elemt: str):
    # The order of " " (space) and  ">" is important to not cut to end of link instantly
    for href_start, href_allowed_ends in [("href=\"", ['"']), ("href='", ["'"]), ("href=", [" ", ">"])]:
        # Find start
        key_index = link_elemt.find(href_start)
        if key_index == -1:
            continue

        value_start = key_index + len(href_start)
        value_end = None
        # Find end
        for allowed_end in href_allowed_ends:
            value_end = link_elemt.find(allowed_end, value_start)
            if value_end != -1:
                break

        if value_end == -1:
            return None
        return link_elemt[value_start:value_end]
    return None


def extract_manifest_url(content: str):

    # Extract manifest url
    # We need to find something like <link rel="manifest" href="..."> but attributes can be in different order
    # TODO might need to add check because simple quotes are allowed too?
    relationship_index = find_manifest_rel(content)
    if relationship_index == -1:
        # A tuple of result and error message
        return None, "Could not find manifest url"

    # Define boundaries
    element_end = content.find(">", relationship_index)

    # Only search in string before relationship since relationship is in the middle of the link element
    element_start = content.rfind("<", 0, relationship_index)

    link_element = content[element_start:element_end+1]

    href = extract_href_from_link(link_element)
    if href is None:
        return None, "Invalid manifest link, missing href"

    return href, None


@app.post("/apps")
def create_app(request: Request, url: Annotated[str, Form(alias="url")], session: Session = Depends(get_session)):
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
    uvicorn.run("wApp.main:app")
