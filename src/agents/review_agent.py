"""Review Agent - evaluates code changes against acceptance criteria."""

import re
from typing import Optional

from src.models import ModelClient, Message
from src.orchestration.context import TicketInfo, DesignOutput, TestOutput, ReviewOutput
from .prompts import REVIEW_AGENT_SYSTEM_PROMPT, format_review_prompt


class ReviewAgent:
    """
    Review Agent evaluates code changes against acceptance criteria.

    Outputs:
    - Decision (approved/rejected)
    - Review comments
    - Suggestions for improvement
    """

    def __init__(self, model_client: ModelClient):
        """
        Initialize Review Agent.

        Args:
            model_client: Model client for LLM interactions
        """
        self.model_client = model_client

    async def run(
        self,
        ticket_info: TicketInfo,
        design_output: DesignOutput,
        diff: str,
        test_output: TestOutput,
    ) -> ReviewOutput:
        """
        Run the Review Agent to evaluate code changes.

        Args:
            ticket_info: Information about the Jira ticket
            design_output: Output from the Design Agent
            diff: Code changes diff
            test_output: Test execution results

        Returns:
            ReviewOutput with decision and comments
        """
        # Format the prompt
        user_prompt = format_review_prompt(
            ticket_info,
            design_output,
            diff,
            test_output,
        )

        # Call the model
        messages = [
            Message(role="system", content=REVIEW_AGENT_SYSTEM_PROMPT),
            Message(role="user", content=user_prompt),
        ]

        response = await self.model_client.chat(messages)

        # Parse the response
        review_output = self._parse_response(response.content)

        return review_output

    def _parse_response(self, response_text: str) -> ReviewOutput:
        """
        Parse the model's response into structured ReviewOutput.

        Expected format:
        DECISION: [APPROVED or REJECTED]

        REVIEW COMMENTS:
        - [comment 1]
        - [comment 2]

        SUGGESTIONS (optional improvements):
        - [suggestion 1]
        - [suggestion 2]
        """
        # Initialize with defaults
        decision = "pending"
        comments = []
        suggestions = []

        # Split response into sections
        sections = self._split_into_sections(response_text)

        # Extract decision
        if "DECISION" in sections:
            decision_text = sections["DECISION"].strip().upper()
            if "APPROVED" in decision_text:
                decision = "approved"
            elif "REJECTED" in decision_text or "REJECT" in decision_text:
                decision = "rejected"

        # Extract review comments
        if "REVIEW COMMENTS" in sections:
            comments_text = sections["REVIEW COMMENTS"].strip()
            comments = self._extract_list_items(comments_text)

        # Extract suggestions
        if "SUGGESTIONS" in sections:
            suggestions_text = sections["SUGGESTIONS"].strip()
            suggestions = self._extract_list_items(suggestions_text)

        return ReviewOutput(
            decision=decision,
            comments=comments,
            suggestions=suggestions,
        )

    def _extract_list_items(self, text: str) -> list:
        """Extract list items from text (bullets or numbered)."""
        items = []

        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue

            # Remove bullet points or numbers
            line = re.sub(r'^[-*•]\s*', '', line)  # Bullet points
            line = re.sub(r'^\d+\.\s*', '', line)  # Numbered lists
            line = line.strip()

            if line and not line.startswith('['):
                items.append(line)

        return items

    def _split_into_sections(self, text: str) -> dict:
        """Split response text into sections based on headers."""
        sections = {}
        current_section = None
        current_content = []

        for line in text.split('\n'):
            # Check if this is a section header
            # Format: "SECTION NAME:" or "SECTION NAME (details):"
            upper_line = line.strip().upper()
            if ':' in upper_line and any(
                keyword in upper_line
                for keyword in ['DECISION', 'REVIEW COMMENTS', 'COMMENTS', 'SUGGESTIONS']
            ):
                # Save previous section
                if current_section:
                    sections[current_section] = '\n'.join(current_content)

                # Start new section
                # Extract the key part (before colon or parenthesis)
                section_name = line.split(':')[0].strip().upper()
                section_name = section_name.split('(')[0].strip()
                current_section = section_name
                current_content = []

                # Check if decision is on same line
                if ':' in line:
                    remainder = line.split(':', 1)[1].strip()
                    if remainder:
                        current_content.append(remainder)
            else:
                # Add to current section
                if current_section:
                    current_content.append(line)

        # Save last section
        if current_section:
            sections[current_section] = '\n'.join(current_content)

        return sections
