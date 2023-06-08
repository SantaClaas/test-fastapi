from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship, mapped_column

from .database import Base


class App(Base):
    __tablename__ = "apps"

    # id used by us is equal to the app host currently
    id = Column(String, primary_key=True, index=True)
    # TODO consider refactor to proper normalization as id is part of manifest url
    # Manifest url is not part of the manifest but for us to keep a reference to the orignal source
    manifest_url = Column(String)
    # Required manifest members
    name = Column(String)
    # (icons, in other table)
    icons = relationship("Icon", back_populates="app")
    start_url = Column(String)
    # (display and/or display_override, currently not needed by us)

    # Optional manifest members
    description = Column(String, nullable=True)

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
