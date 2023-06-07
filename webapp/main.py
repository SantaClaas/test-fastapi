from typing import Annotated
from os.path import dirname, abspath, join
from fastapi import FastAPI, Form
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from urllib.request import urlopen
from urllib.parse import urlparse
import json
import starlette.status as status

current_dir = dirname(abspath(__file__))
static_path = join(current_dir, "static")

app = FastAPI()
app.mount("/ui", StaticFiles(directory=static_path), name="ui")

@app.get('/')
def root():
    html_path = join(static_path, "index.html")
    return FileResponse(html_path)

@app.get("/apps/{app_id}")
def view_app(app_id: str):
    return { "app_id": app_id }

@app.post("/apps")
async def create_app(url: Annotated[str, Form(alias="url")]):
    #TODO url validation
    # An application is defined by the manifest so these terms can be used interchangibly

    # We use the host as the id for the app
    #TODO find a way to avoid duplicate apps from hosts that have the same web manifest by using a more qualified
    # comparison of manifests like comparing a hash or other distinguishing characteristics
    components = urlparse(url)
    app_id = components.netloc

    # Get manifest from user provided url
    #TODO error handling
    response = urlopen(url)
    manifest = json.loads(response.read())
    # Persist application to database
    # Return user to new page for app

    return RedirectResponse(f"/apps/{app_id}", status_code=status.HTTP_303_SEE_OTHER)
