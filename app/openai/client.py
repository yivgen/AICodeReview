from openai import AsyncOpenAI
from app.settings import get_settings
from app.models import ReviewRequest, ReviewResponse
from app.github.models import File
import json
from fastapi import HTTPException


REVIEW_PROMPT = """
Given assignment description, candidate level and the contents of a github 
repository, produce a comprehensive review of the code

# Guidelines

- Understand the assignment: Grasp the objective, goals, constraints, 
requirements and expected result.
- Analyze code quality: indetify potential issues and suggest improvements.
- Clarity and Conciseness: Use clear, specific language. 
- Avoid unnecessary instructions or bland statements. Provide examples.
- Consider candidate level when reviewing the code.
- Your output should contain:
    - Comments and downsides of the code.
    - Overall rating which indicates the quality of the code.
    - Conclusion which should inlude an overview of candidate's performance.

# Input Format (json):
{
    "assignment_description": {
        "type": "string",
        "description": "Goals, requirements, constraints, expected result"
    }
    "candidate_level": {
        "type": "string",
        "description": "Candidate level: can be junior, middle or senior"
    }
    "files": [
        {
            "path": {
                "type": "string",
                "description": "A relative path to the file"
            },
            "content": {
                "type": "string",
                "description": "Content of the file"
            }
        }
    ]
}

# Output Format (json):
{
    "comments": {
        "description": "Comments and downsides of the code",
        "type": "string"
    },
    "rating": {
        "description": "Overall rating indicates the quality of the code",
        "type": "number",
        "minimum": 1,
        "maximum": 5
    },
    "conclusion": {
        "description": "Should inlude an overview of candidate's performance",
        "type": "string"
    },
}
"""


class OpenAIClient:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=get_settings().OPENAI_KEY)

    async def generate_review(
        self, review_request: ReviewRequest, files: list[File]
    ) -> ReviewResponse:
        completion = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": REVIEW_PROMPT,
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            **review_request.model_dump(
                                include={
                                    "assignment_description",
                                    "candidate_level",
                                }
                            ),
                            "files": [
                                f.model_dump(include={"path", "content"})
                                for f in files
                            ],
                        },
                        indent=4,
                    ),
                },
            ],
            response_format={"type": "json_object"},
        )
        if completion.choices[0].message.finish_reason == "length":
            raise HTTPException(500, detail="OpenAI review is too long.")
        if completion.choices[0].message[0].get("refusal"):
            raise HTTPException(
                500,
                detail=(f"OpenAI safety system refused the request: "
                        f"{completion.choices[0].message[0]["refusal"]}"),
            )
        if completion.choices[0].message.finish_reason == "content_filter":
            raise HTTPException(
                500, detail="The review contained restricted content."
            )
        if completion.choices[0].message.finish_reason == "stop":
            return ReviewResponse.model_validate_json(
                completion.choices[0].message.content
            )
        else:
            raise HTTPException(
                500, detail="An error occurred during review generation."
            )
