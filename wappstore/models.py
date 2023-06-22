"""
Models and schemas for deserializing webmanifest JSON files
"""
from typing import Literal
from marshmallow import EXCLUDE, Schema, fields, post_load

# Models for JSON deserialization


class ImageResource:
    """
    Defines an image resource like in the W3C spec. Only exists as an abstract class currently to
    provide correct fields to inheriting classes
    """
    src: str
    sizes: str | None
    label: str | None
    type: str | None

    def __init__(self, src: str, sizes: str | None, label: str | None, type: str | None = None) -> None:
        self.src = src
        self.sizes = sizes
        self.type = type
        self.label = label


class Icon(ImageResource):
    """"
    Describes an icon in a web app manifest
    """
    purpose: str

    def __init__(self, src: str, sizes: str, type: str | None = None, label: str | None = None, purpose: str = "any") -> None:
        super().__init__(src, sizes, label, type)
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


class Screenshot(ImageResource):
    """"
    Describes a screenshot in a web app manifest
    """
    form_factor: Literal["wide", "narrow"] | None

    def __init__(self, src: str, sizes: str | None,  type: str | None, label: str | None = None,  form_factor: Literal["wide", "narrow"] | None = None) -> None:
        super().__init__(src, sizes, label, type)
        self.form_factor = form_factor


class ScreenshotSchema(Schema):
    """"
    Describes the schema for a screenshot in a web app manifest
    """
    src = fields.Str()
    sizes = fields.Str()
    type = fields.Str()
    label = fields.Str()
    form_factor = fields.Str()

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
    description: str | None
    start_url: str
    icons: list[Icon]
    categories: list[str]
    screenshots: list[Screenshot]

    def __init__(self, name: str, start_url: str, icons: list[Icon], categories: list[str] = [], screenshots: list[Screenshot] = [], description: str | None = None) -> None:
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
