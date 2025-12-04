"""
Minimal example showing structured output with picoagents.

This example demonstrates how to call a model with structured output
using Pydantic models to ensure type-safe responses.
"""

import asyncio
from typing import List, cast

from pydantic import BaseModel, Field

from picoagents.llm import OpenAIChatCompletionClient
from picoagents.messages import Message, UserMessage


class PersonInfo(BaseModel):
    """Structured output model for person information."""

    name: str = Field(description="The person's full name")
    age: int = Field(description="The person's age in years")
    occupation: str = Field(description="The person's job or profession")
    skills: List[str] = Field(description="List of the person's key skills")


async def main():
    """Demonstrate structured output with OpenAI model."""

    # Initialize the OpenAI client
    client = OpenAIChatCompletionClient(model="gpt-4.1-mini")
    # Create a user message asking for person information
    messages: List[Message] = [
        UserMessage(
            content="Create a profile for a software engineer named Alice who is 28 years old and skilled in Python, JavaScript, and machine learning.",
            source="user",
        )
    ]
    # Call the model with structured output
    result = await client.create(
        messages=messages, output_format=PersonInfo  # This ensures structured output
    )

    # The result.structured_output will be a PersonInfo object
    if result.structured_output:
        person = cast(PersonInfo, result.structured_output)
        print("Structured Output:")
        print(f"Name: {person.name}")
        print(f"Age: {person.age}")
        print(f"Occupation: {person.occupation}")
        print(f"Skills: {', '.join(person.skills)}")
    else:
        print("Raw response:", result.message.content)


if __name__ == "__main__":
    asyncio.run(main())
