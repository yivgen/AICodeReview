from fastapi import FastAPI
from app.models import ReviewRequest
from app.github.client import GithubClient
from app.github.models import File
from app.openai.client import OpenAIClient
import logging
import asyncio
import aioredis


app = FastAPI()
logger = logging.getLogger("uvicorn.error")
redis = aioredis.from_url("redis://redis", decode_responses=True)


@app.post("/review")
async def review(review_request: ReviewRequest):
    github_client = GithubClient(redis)
    owner, repo = github_client.parse_url(review_request.github_repo_url)
    default_branch = await github_client.get_default_branch(owner, repo)
    tree = await github_client.get_tree(
        owner, repo, default_branch, recursive=True
    )
    blobs = [i for i in tree.tree if i.type == "blob"]
    tasks = [
        github_client.get_file(owner, repo, blob.sha, blob.path)
        for blob in blobs
    ]
    blobs: list[File] = await asyncio.gather(*tasks)

    openai_client = OpenAIClient()
    review = await openai_client.generate_review(review_request, blobs)

    return {
        "found_files": [blob.path for blob in blobs],
        **review.model_dump(),
    }
