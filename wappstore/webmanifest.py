"""
A module containting logic related to fetching and processing webmanifest files that describe
web apps
"""
from urllib.parse import urljoin

import httpx

from wappstore.data import crud, models
from wappstore.data.database import SessionLocal
from wappstore.models import Manifest, ManifestSchema


def save_to_database(session: SessionLocal, app_id: str, manifest_url: str, manifest: Manifest):
    """
    Saves a webmanifest to the database
    """
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
    existing_categories = dict(map(
        lambda category: (category.name, category), crud.get_categories(session)))

    def get_or_create(category_name: str):
        if category_name in existing_categories:
            return existing_categories[category_name]

        return models.Category(name=category_name)

    categories = list(map(get_or_create, manifest.categories))

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


def find_manifest_rel(content: str):
    """
    Finds the index manifest relationship attribute in an HTML string
    """

    for rel_kind in ["rel=\"manifest\"", "rel=manifest", "rel='manifest'"]:
        index = content.find(rel_kind)
        if index != -1:
            return index

    return -1


def extract_href_from_link(link_elemt: str):
    """
    Extracts the href attribute value (url) from a string that is in the form of a link element
    """

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
    """
    Extracts the manifest url from an HTML content string
    """

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


def fetch_app_details(user_provided_url: str):
    """
    Fetches the app details from the manifest with the url to the HTML page of the web app or the manifest url
    """

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
