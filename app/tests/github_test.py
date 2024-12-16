import pytest
from app.github.client import GithubClient, GithubURL
from fastapi import HTTPException
from app.github.models import File, Repo
import respx
from httpx import Response


pytest_plugins = ("pytest_asyncio",)


class TestGithubClient:
    @pytest.fixture
    def redis_client(self):
        import fakeredis

        return fakeredis.FakeAsyncRedis()

    @pytest.fixture
    def github_client(self, redis_client):
        github_client = GithubClient(redis_client)
        return github_client

    @pytest.fixture
    def test_file(self):
        return File(path="test_file", sha="test_sha", content="Test file")

    @pytest.fixture
    def test_repo(self):
        return Repo(name="test_repo", owner="test")

    @pytest.mark.asyncio
    @respx.mock(base_url=GithubURL.BASE_URL)
    async def test_invalid_url(
        self, github_client: GithubClient, test_repo: Repo, respx_mock
    ):
        respx_mock.get(
            GithubURL.GET_REPO.format(
                owner=test_repo.owner, repo=test_repo.name
            )
        ).mock(return_value=Response(404, text="Page not found"))

        with pytest.raises(HTTPException) as exc_info:
            await github_client.get_default_branch(
                test_repo.owner, repo=test_repo.name
            )

        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    @respx.mock(base_url=GithubURL.BASE_URL)
    async def test_empty_repo(
        self, github_client: GithubClient, test_repo: Repo, respx_mock
    ):
        respx_mock.get(
            GithubURL.GET_TREE.format(
                owner=test_repo.owner,
                repo=test_repo.name,
                tree_sha="empty_branch",
            )
        ).mock(return_value=Response(409, text="The repo is empty"))

        with pytest.raises(HTTPException) as exc_info:
            await github_client.get_tree(
                owner=test_repo.owner,
                repo=test_repo.name,
                branch="empty_branch",
            )

        assert exc_info.value.status_code == 409

    @pytest.mark.asyncio
    @respx.mock(base_url=GithubURL.BASE_URL)
    async def test_cache_file(
        self,
        github_client: GithubClient,
        test_repo: Repo,
        test_file: File,
        respx_mock,
    ):
        respx_mock.get(
            GithubURL.GET_BLOB.format(
                owner=test_repo.owner,
                repo=test_repo.name,
                file_sha=test_file.sha,
            )
        ).mock(
            return_value=Response(
                200, json={"content": test_file.content, "sha": test_file.sha}
            )
        )

        uncached_file = await github_client.get_file(
            owner=test_repo.owner,
            repo=test_repo.name,
            file_sha=test_file.sha,
            path=test_file.path,
        )
        cached_file = await github_client.get_file(
            owner=test_repo.owner,
            repo=test_repo.name,
            file_sha=test_file.sha,
            path=test_file.path,
        )

        assert respx_mock.calls.call_count == 1
        assert cached_file == uncached_file == test_file
