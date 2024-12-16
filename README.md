# Get a detailed AI review of your Github repository.

A FastAPI web service that generates a comprehensive code review, given the assignment description (i.e. what is the purpose of this code), candidate level and the link to your github repository.

## Features:
 - Uses [gpt-4-turbo](https://help.openai.com/en/articles/8555510-gpt-4-turbo-in-the-openai-api) for code analysis and review.
 - Github API integration with appropriate error handling.
 - Caching with Redis to reduce the number of API calls.
 - Easily deployed with Docker

## Prerequisites
- Docker and Docker Compose.
- Python 3.10 or higher.
- [Github access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens).
- [OpenAI API key](https://platform.openai.com/docs/api-reference/authentication).

## Getting started
1. Create your `.env` file at the root of the project. Use `.env.example` as the template.
2. Build and start the containers with:
    ```bash
    docker compose up --build
    ```
3. Access auto-generated documentation at http://localhost:5500/docs or send requests directly to http://localhost:5500/review.