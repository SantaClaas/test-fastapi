from pydantic import BaseModel


# class IconBase(BaseModel):
#     pass


# class IconCreate(IconBase):
#     app: str


# class Icon(IconBase):
#     class Config:
#         orm_model = True


class AppBase(BaseModel):
    id: str
    name: str
    # icons: list[IconBase] = []
    start_url: str

    description: str | None = None


class AppCreate(AppBase):
    pass


class App(AppBase):
    class Config:
        orm_model = True
