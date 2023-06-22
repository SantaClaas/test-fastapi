"""
A module to contain all models that describe the database structure
"""

from sqlalchemy import Column, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship

from wappstore.url import ensure_is_absolute
from .database import Base


# A join table connecting Apps and Categories as it is a many to many relationship
app_category = Table(
    "app_category",
    Base.metadata,
    Column("app_id", ForeignKey("apps.id", ondelete="CASCADE"), primary_key=True),
    Column("category_name", ForeignKey(
        "categories.name", ondelete="CASCADE"), primary_key=True)
)


class App(Base):
    """
    Describes the table to persist a web app. Contains mostly contents from the webmanifest file
    """
    __tablename__ = "apps"

    """
    The id is the host or url for the app
    """
    id = Column(String, primary_key=True, index=True)
    """
    Where we loaded the manifest from
    Manifest url is not part of the manifest but for us to keep a reference to the orignal source
    """
    manifest_url = Column(String)

    # Required manifest members
    """
    Name of the app
    """
    name = Column(String)
    """
    Where the app starts from
    """
    start_url = Column(String)
    # (Other properties like display and/or display_override, currently not needed by us)

    # Optional manifest members
    """
    Description of the app
    """
    description = Column(String, nullable=True)

    # Relationships to load data from other tables
    categories = relationship(
        "Category", back_populates="apps", secondary=app_category)

    screenshots = relationship(
        "Screenshot", cascade="all, delete-orphan", passive_deletes=True)

    icons = relationship("Icon", cascade="all, delete-orphan")

    def get_primary_icon_url(self):
        """
        Get the icon that should be used as primary icon as defined by spec
        """
        # We use the last one declared that is appropiate as per spec https://w3c.github.io/manifest/#icons-member
        # Appropiate for us in this case is purpose not monochrome and maskable
        icon = list(
            filter(lambda icon: "any" in icon.purpose.split(), self.icons))[-1]

        return ensure_is_absolute(icon.source, self.id)

# See https://developer.mozilla.org/en-US/docs/Web/Manifest/icons and https://w3c.github.io/manifest/#icons-member and
# https://w3c.github.io/manifest/#manifest-image-resources and https://www.w3.org/TR/image-resource/#dfn-image-resource


class Icon(Base):
    """
    Describes the table for an icon resource as described in the webmanifest. Is linked to app table as an app can have
    multiple icons
    """
    __tablename__ = "icons"

    """
    Id created by us just as a unique identifier
    """
    id = Column(Integer, primary_key=True, index=True)

    """
    The id of the app the icon belongs to
    """
    app_id = Column(String, ForeignKey("apps.id", ondelete="CASCADE"))

    """
    The source or "src" where the icon can be loaded from
    """
    source = Column(String)

    """"
    Sizes of the icon.
    Sizes is either a list with sizes separated by spaces or "any". Normalization rules would require this to be in a
    separate table but we just use the string value because it would be kind of hard to represent "any" or list in a
    table without allowing invalid state (e.g. have "isAny" to true and multiple sizes)
    See: https://developer.mozilla.org/en-US/docs/Web/HTML/Element/link#sizes
    """
    sizes = Column(String, nullable=True)

    """"
    The MIME type of the image
    This is hard to represent too since it only allows Mime types which is a defined set and not any arbritary string
    like this field allows
    """
    type = Column(String, nullable=True)

    """
    The label is used for by screenreaders or other assistive technologies
    """
    label = Column(String, nullable=True)

    """
    What the icon should be used for
    Can also be list separated by spaces
    Technically limited to "monochrome", "maskable" and "any" (default) but we don't enforce that yet
    """
    purpose = Column(String, default="any")


class Category(Base):
    """"
    The categories of the web app as defined in the webmanifest
    Is only a string but can be used by multiple apps
    """

    __tablename__ = "categories"

    """
    The name of the category. By specification technically limited to certain values but currently not enforced
    """
    name = Column(String, primary_key=True, index=True)

    """
    Loads apps in this category
    """
    apps = relationship("App", back_populates="categories",
                        secondary=app_category)

    def __str__(self):
        return self.name


class Screenshot(Base):
    """
    Represents a screenshot of a web app as defined in the webmanifest
    """
    __tablename__ = "screenshots"

    """
    Id created by us just as a unique identifier
    """
    id = Column(Integer, primary_key=True, index=True)

    """
    The id of the app the icon belongs to
    """
    app_id = Column(String, ForeignKey("apps.id", ondelete="CASCADE"))

    """
    The source or "src" where the icon can be loaded from
    """
    source = Column(String)

    """"
    Sizes of the Screenshot.
    Sizes is either a list with sizes separated by spaces or "any". Normalization rules would require this to be in a
    separate table but we just use the string value because it would be kind of hard to represent "any" or list in a
    table without allowing invalid state (e.g. have "isAny" to true and multiple sizes)
    See: https://developer.mozilla.org/en-US/docs/Web/HTML/Element/link#sizes
    """
    sizes = Column(String)

    """"
    The MIME type of the image
    This is hard to represent too since it only allows Mime types which is a defined set and not any arbritary string
    like this field allows
    """
    type = Column(String)
