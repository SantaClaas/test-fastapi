from sqlalchemy import Column, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship, backref

from .database import Base

app_category = Table(
    "app_category",
    Base.metadata,
    Column("app_id", ForeignKey("apps.id"), primary_key=True),
    Column("category_name", ForeignKey("categories.name"), primary_key=True)
)


class App(Base):
    __tablename__ = "apps"

    # id used by us is equal to the app host currently
    # TODO It would be ideal to use same as https://w3c.github.io/manifest/#dfn-identity
    id = Column(String, primary_key=True, index=True)
    # TODO consider refactor to proper normalization as id is part of manifest url
    # Manifest url is not part of the manifest but for us to keep a reference to the orignal source
    manifest_url = Column(String)
    # Required manifest members
    name = Column(String)
    # (icons, in other table)
    icons = relationship("Icon", back_populates="app",
                         cascade="all, delete-orphan")
    start_url = Column(String)
    # (display and/or display_override, currently not needed by us)

    # Optional manifest members
    description = Column(String, nullable=True)
    # Technically also a limited set we should check but don't
    categories = relationship(
        "Category", back_populates="apps", secondary=app_category)

    screenshots = relationship(
        "Screenshot", back_populates="app", cascade="all, delete-orphan")
    # direction = Column(String, default="auto")
    # # The language of the manifests localizable members
    # language = Column(String, nullable=True)
    # short_name = Column(String, nullable=True)
    # scope = Column(String, nullable=True)
    # scope = Column(String, nullable=True)
    # display = Column(String, nullable=True)
    # orientation = Column(String, nullable=True)
    # start_url = Column(String, nullable=True)
    # theme_color = Column(String, nullable=True)
    # background_color = Column(String, nullable=True)

# See https://developer.mozilla.org/en-US/docs/Web/Manifest/icons and https://w3c.github.io/manifest/#icons-member and
# https://w3c.github.io/manifest/#manifest-image-resources and https://www.w3.org/TR/image-resource/#dfn-image-resource


class Icon(Base):
    __tablename__ = "icons"
    id = Column(Integer, primary_key=True, index=True)
    app_id = Column(String, ForeignKey("apps.id"))
    source = Column(String)
    # https://developer.mozilla.org/en-US/docs/Web/HTML/Element/link#sizes
    # Sizes is either a list with sizes separated by spaces or "any". Normalization rules would require this to be in a
    # separate table but we just use the string value because it would be kind of hard to represent "any" or list in a
    # table without allowing invalid state (e.g. have "isAny" to true and multiple sizes)
    sizes = Column(String, nullable=True)
    # This is hard to represent too since it only allows Mime types which is a defined set and not any arbritary string
    # like this field allows
    type = Column(String, nullable=True)
    label = Column(String, nullable=True)
    # Also limited to "monochrome", "maskable" and "any" (default)
    purpose = Column(String, default="any")

    app = relationship("App", back_populates="icons")


class Category(Base):
    __tablename__ = "categories"

    name = Column(String, primary_key=True, index=True)
    apps = relationship("App", back_populates="categories",
                        secondary=app_category)

    def __str__(self):
        return self.name


class Screenshot(Base):
    __tablename__ = "screenshots"

    id = Column(Integer, primary_key=True, index=True)
    app_id = Column(String, ForeignKey("apps.id"))
    source = Column(String)
    # This should be split up later since it is not atomic to follow normalization rules
    sizes = Column(String)
    # This should refer to MIME types
    type = Column(String)

    app = relationship("App", back_populates="screenshots")
