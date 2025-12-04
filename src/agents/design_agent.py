"""Design Agent - analyzes tickets and proposes implementation approach."""

import re
from typing import Optional

from src.models import ModelClient, Message
from src.orchestration.context import TicketInfo, RepoInfo, DesignOutput
from .prompts import DESIGN_AGENT_SYSTEM_PROMPT, format_design_prompt


class DesignAgent:
    """
    Design Agent analyzes tickets and repository information to propose
    an implementation approach.

    Outputs:
    - Problem understanding
    - Proposed approach
    - Target files to modify/create
    - Step-by-step implementation plan
    """

    def __init__(self, model_client: ModelClient):
        """
        Initialize Design Agent.

        Args:
            model_client: Model client for LLM interactions
        """
        self.model_client = model_client

    async def run(
        self,
        ticket_info: TicketInfo,
        repo_info: RepoInfo,
    ) -> DesignOutput:
        """
        Run the Design Agent to create an implementation plan.

        Args:
            ticket_info: Information about the Jira ticket
            repo_info: Information about the repository

        Returns:
            DesignOutput with implementation plan
        """
        # Format the prompt
        user_prompt = format_design_prompt(ticket_info, repo_info)

        # Call the model
        messages = [
            Message(role="system", content=DESIGN_AGENT_SYSTEM_PROMPT),
            Message(role="user", content=user_prompt),
        ]

        response = await self.model_client.chat(messages)

        # Parse the response
        design_output = self._parse_response(response.content)

        return design_output

    def _parse_response(self, response_text: str) -> DesignOutput:
        """
        Parse the model's response into structured DesignOutput.

        Expected format:
        PROBLEM UNDERSTANDING:
        [text]

        PROPOSED APPROACH:
        [text]

        TARGET FILES:
        [list of files]

        STEP-BY-STEP PLAN:
        1. [step]
        2. [step]
        """
        # Initialize with defaults
        problem_understanding = ""
        proposed_approach = ""
        target_files = []
        step_by_step_plan = []

        # Split response into sections
        sections = self._split_into_sections(response_text)

        # Extract problem understanding
        if "PROBLEM UNDERSTANDING" in sections:
            problem_understanding = sections["PROBLEM UNDERSTANDING"].strip()

        # Extract proposed approach
        if "PROPOSED APPROACH" in sections:
            proposed_approach = sections["PROPOSED APPROACH"].strip()

        # Extract target files
        if "TARGET FILES" in sections:
            files_text = sections["TARGET FILES"].strip()
            # Extract file paths (anything that looks like a file path)
            target_files = [
                line.strip().lstrip('-').lstrip('*').strip()
                for line in files_text.split('\n')
                if line.strip() and not line.strip().startswith('[')
            ]

        # Extract step-by-step plan
        if "STEP-BY-STEP PLAN" in sections or "STEP BY STEP PLAN" in sections:
            plan_text = sections.get("STEP-BY-STEP PLAN", sections.get("STEP BY STEP PLAN", ""))
            # Extract numbered steps
            steps = re.findall(r'^\d+\.\s*(.+)$', plan_text, re.MULTILINE)
            if steps:
                step_by_step_plan = steps
            else:
                # Fallback: split by lines and filter
                step_by_step_plan = [
                    line.strip().lstrip('-').lstrip('*').strip()
                    for line in plan_text.split('\n')
                    if line.strip() and not line.strip().startswith('[')
                ]

        return DesignOutput(
            problem_understanding=problem_understanding,
            proposed_approach=proposed_approach,
            target_files=target_files,
            step_by_step_plan=step_by_step_plan,
        )

    def _split_into_sections(self, text: str) -> dict:
        """Split response text into sections based on headers."""
        sections = {}
        current_section = None
        current_content = []

        for line in text.split('\n'):
            # Check if this is a section header (all caps followed by colon)
            if line.strip() and line.strip().endswith(':') and line.strip()[:-1].isupper():
                # Save previous section
                if current_section:
                    sections[current_section] = '\n'.join(current_content)

                # Start new section
                current_section = line.strip()[:-1]  # Remove the colon
                current_content = []
            else:
                # Add to current section
                if current_section:
                    current_content.append(line)

        # Save last section
        if current_section:
            sections[current_section] = '\n'.join(current_content)

        return sections
