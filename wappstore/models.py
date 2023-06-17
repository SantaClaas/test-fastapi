from marshmallow import EXCLUDE, Schema, fields, post_load

# Models for JSON deserialization

# TODO define ImageResource base class for Screenshot and Icon


class Icon:
    """"
    Describes an icon in a web app manifest
    """
    src: str
    sizes: str
    type: str
    label: str
    purpose: str

    def __init__(self, src: str, sizes: str, type: str, label: str | None = None, purpose: str = "any") -> None:
        self.src = src
        self.sizes = sizes
        self.type = type
        self.label = label
        self.purpose = purpose


class IconSchema(Schema):
    """"
    Describes the schema for an icon in a web app manifest
    An icon is an ImageResource with the additional purpose field as per spec
    """
    src = fields.Str()
    sizes = fields.Str()
    type = fields.Str()
    label = fields.Str(default=None)
    purpose = fields.Str(default="any")

    class Meta:
        unknown = EXCLUDE

    @post_load
    def make_icon(self, data, **kwargs) -> Icon:
        return Icon(**data)


class Screenshot:
    """"
    Describes a screenshot in a web app manifest
    """
    src: str
    sizes: str
    type: str

    def __init__(self, src: str, sizes: str, type: str) -> None:
        self.src = src
        self.sizes = sizes
        self.type = type


class ScreenshotSchema(Schema):
    """"
    Describes the schema for a screenshot in a web app manifest
    """
    src = fields.Str()
    sizes = fields.Str()
    type = fields.Str()

    class Meta:
        unknown = EXCLUDE

    @post_load
    def make_screenshot(self, data, **kwargs):
        return Screenshot(**data)


class Manifest:
    """
    Describes a web app manifest
    """
    name: str
    description: str
    start_url: str
    icons: list[Icon]
    categories: list[str]
    screenshots: list[Screenshot]

    def __init__(self, name: str, description: str, start_url: str, icons: list[Icon], categories: list[str] = [], screenshots: list[Screenshot] = []) -> None:
        self.name = name
        self.description = description
        self.start_url = start_url
        self.icons = icons
        self.categories = categories
        self.screenshots = screenshots


class ManifestSchema(Schema):
    """
    Describes the schema of a web app manifest
    """
    name = fields.Str()
    description = fields.Str()
    start_url = fields.Str()
    icons = fields.List(fields.Nested(IconSchema))
    categories = fields.List(fields.Str)
    screenshots = fields.List(fields.Nested(ScreenshotSchema))

    class Meta:
        unknown = EXCLUDE

    @post_load
    def make_manifest(self, data, **kwargs):
        return Manifest(**data)
