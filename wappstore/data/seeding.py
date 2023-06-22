"""
A module containing the logic for seeding the application with data for presentation purposes
"""
from urllib.parse import urlparse, urlunsplit

from wappstore.data import crud
from wappstore.data.database import SessionLocal
from wappstore.webmanifest import fetch_app_details, save_to_database


apps_to_seed = [
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
    """
    Seeds predefined apps by fetching their manifest
    """
    session = SessionLocal()
    for url in apps_to_seed:
        components = urlparse(url)
        # App id should be host and path
        app_id = components.netloc + components.path
        if crud.get_app(session, app_id):
            continue

        # Should use proper logging
        print("Seeding", url)
        manifest_or_error = fetch_app_details(url)
        if isinstance(manifest_or_error, str):
            print(
                f"Error while seeding {app_id}", manifest_or_error)

            continue

        manifest, manifest_url = manifest_or_error
        save_to_database(session, app_id, manifest_url, manifest)

    session.close()
