from pydantic import BaseModel


class Repo(BaseModel):
    owner: str
    name: str


class TreeItem(BaseModel):
    path: str
    type: str
    sha: str
    url: str


class Tree(BaseModel):
    sha: str
    tree: list[TreeItem]


class File(BaseModel):
    path: str
    sha: str
    content: str
