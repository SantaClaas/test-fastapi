from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship, mapped_column

from .database import Base


class App(Base):
    __tablename__ = "Apps"

    # id used by us is equal to the app host currently
    id = Column(String, primary_key=True, index=True)
    # Required manifest members
    name = Column(String)
    # (icons, in other table)
    # icons= relationship("Icon", back_populates=True)
    start_url = Column(String)
    # (display and/or display_override, currently not needed by us)

    # Optional manifest members
    description = Column(String, nullable=True)

# TODO Web App icon table


# class Icon(Base):
#     __tablename__ = "icons"

#     id = Column(Integer, primary_key=True, index=True)
#     web_app = relationship("App", back_populates=True)
    # sizes = relationship("Size", back_populates=True)

# class Size(Base):
#     __tablename__ = "sizes"
#     id = Column(Integer, primary_key=True, index=True)

#     icon = relationship("Icon", )
