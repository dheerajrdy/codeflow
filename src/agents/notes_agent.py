"""Notes/Metadata Agent - summarizes workflow runs and captures learnings."""

import re
from typing import List

from src.models import ModelClient, Message
from src.orchestration.context import NotesOutput
from .prompts import NOTES_AGENT_SYSTEM_PROMPT, format_notes_prompt


class NotesAgent:
    """Generates summaries, lessons, and tags for a workflow run."""

    def __init__(self, model_client: ModelClient):
        self.model_client = model_client

    async def run(
        self,
        ticket_summary: str,
        design_summary: str,
        coding_summary: str,
        test_summary: str,
        review_summary: str,
        pr_summary: str,
        logs: str,
    ) -> NotesOutput:
        """Invoke the model to generate notes."""
        prompt = format_notes_prompt(
            ticket_summary=ticket_summary,
            design_summary=design_summary,
            coding_summary=coding_summary,
            test_summary=test_summary,
            review_summary=review_summary,
            pr_summary=pr_summary,
            logs=logs,
        )

        messages = [
            Message(role="system", content=NOTES_AGENT_SYSTEM_PROMPT),
            Message(role="user", content=prompt),
        ]

        response = await self.model_client.chat(messages, temperature=0.3, max_tokens=800)
        return self._parse_response(response.content)

    def _parse_response(self, text: str) -> NotesOutput:
        """Parse structured response into NotesOutput."""
        sections = self._split_sections(text)

        summary = "\n".join(self._extract_list(sections.get("SUMMARY", "")))
        lessons = self._extract_list(sections.get("LESSONS", ""))
        suggestions = self._extract_list(sections.get("SUGGESTIONS", ""))
        tags = self._extract_list(sections.get("TAGS", ""))

        return NotesOutput(
            summary=summary.strip(),
            lessons_learned=lessons,
            suggestions=suggestions,
            tags=tags,
        )

    def _split_sections(self, text: str) -> dict:
        """Split text into sections keyed by header."""
        sections = {}
        current = None
        buffer: List[str] = []

        for line in text.splitlines():
            if line.strip().endswith(":") and line.strip()[:-1].isupper():
                if current:
                    sections[current] = "\n".join(buffer)
                current = line.strip()[:-1]
                buffer = []
            else:
                if current:
                    buffer.append(line)
        if current:
            sections[current] = "\n".join(buffer)

        return sections

    def _extract_list(self, section_text: str) -> list[str]:
        """Extract bullet/numbered list items."""
        items = []
        for line in section_text.splitlines():
            cleaned = re.sub(r"^[-*•]\s*", "", line).strip()
            cleaned = re.sub(r"^\d+\.\s*", "", cleaned)
            if cleaned:
                items.append(cleaned)
        return items
