from urllib.parse import urlparse
from httpx import AsyncClient
from app.github.models import Tree, File
from app.settings import get_settings
from enum import Enum
from fastapi import HTTPException
import logging
import json


logger = logging.getLogger("uvicorn.error")


class GithubURL(str, Enum):
    BASE_URL = "https://api.github.com"
    GET_REPO = "/repos/{owner}/{repo}"
    GET_TREE = "/repos/{owner}/{repo}/git/trees/{tree_sha}"
    GET_BLOB = "/repos/{owner}/{repo}/git/blobs/{file_sha}"


class GithubClient:
    def __init__(self, redis):
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {get_settings().GITHUB_TOKEN}",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        self.client = AsyncClient(headers=headers, base_url=GithubURL.BASE_URL)
        self.redis = redis

    def __aexit__(self):
        self.client.aclose()

    async def get_default_branch(self, owner: str, repo: str) -> str:
        api_url = GithubURL.GET_REPO.format(owner=owner, repo=repo)
        res = await self.client.get(api_url)
        if res.status_code == 404:
            raise HTTPException(
                status_code=400,
                detail=("Could not find the repository. " 
                        "Please check if the supplied url is valid."),
            )
        elif res.status_code != 200:
            raise HTTPException(
                status_code=500,
                detail=("Could not fetch the repository. "
                        "Please check if the supplied url is valid."),
            )

        return res.json().get("default_branch")

    async def get_tree(
        self, owner: str, repo: str, branch: str, recursive=False
    ) -> Tree:
        api_url = GithubURL.GET_TREE.format(
            owner=owner, repo=repo, tree_sha=branch
        )
        res = await self.client.get(api_url, params={"recursive": recursive})
        if res.status_code == 409:
            raise HTTPException(
                status_code=409, detail="The repository is empty."
            )
        if res.status_code != 200:
            raise HTTPException(
                status_code=500,
                detail=("Could not fetch the repository tree. "
                        "Please check if supplied url is still valid."),
            )

        return Tree.model_validate_json(res.text)

    async def get_file(
        self, owner: str, repo: str, file_sha: str, path: str
    ) -> File:
        file_key = f"{owner}/{repo}/{path}/{file_sha}"
        cached_file = await self.redis.get(file_key)
        if cached_file:
            return File.model_validate_json(cached_file)

        api_url = GithubURL.GET_BLOB.format(
            owner=owner, repo=repo, file_sha=file_sha
        )
        res = await self.client.get(api_url)
        if res.status_code != 200:
            raise HTTPException(
                status_code=500,
                detail=("Could not fetch the repository. "
                        "Please check if supplied url is still valid."),
            )

        res = res.json()
        res["path"] = path
        await self.redis.set(file_key, json.dumps(res), ex=60 * 60 * 24)
        return File.model_validate(res)

    @staticmethod
    def parse_url(url: str) -> tuple[str, str]:
        try:
            parsed_url = urlparse(url)
            owner, repo = parsed_url.path.strip("/ ").split("/")
        except Exception as e:
            logger.error(e)
            raise HTTPException(status_code=400, detail="Invalid github url.")

        return (owner, repo)
