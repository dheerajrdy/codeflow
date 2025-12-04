"""Coding Agent - generates code changes based on design plan."""

import re
from pathlib import Path
from typing import Dict, Optional

from src.models import ModelClient, Message
from src.orchestration.context import TicketInfo, RepoInfo, DesignOutput, CodingOutput
from .prompts import CODING_AGENT_SYSTEM_PROMPT, format_coding_prompt


class CodingAgent:
    """
    Coding Agent turns a design plan into concrete code changes.

    Inputs:
    - Ticket information
    - Design output (problem, approach, plan)
    - Repository info and optional code context (file contents)

    Output:
    - CodingOutput containing diff, files changed, and explanations
    """

    def __init__(self, model_client: ModelClient, temperature: float = 0.2):
        """
        Initialize Coding Agent.

        Args:
            model_client: Model client for LLM interactions
            temperature: Sampling temperature for generation (lower favors determinism)
        """
        self.model_client = model_client
        self.temperature = temperature

    async def run(
        self,
        ticket_info: TicketInfo,
        design_output: DesignOutput,
        repo_info: RepoInfo,
        code_context: Optional[Dict[str, str]] = None,
    ) -> CodingOutput:
        """
        Run the Coding Agent to generate code changes.

        Args:
            ticket_info: Information about the Jira ticket
            design_output: Output from the Design Agent
            repo_info: Repository information
            code_context: Optional mapping of file path -> contents for relevant files

        Returns:
            CodingOutput with diff, files changed, and explanations
        """
        user_prompt = format_coding_prompt(
            ticket_info=ticket_info,
            design_output=design_output,
            repo_info=repo_info,
            code_context=code_context,
        )

        messages = [
            Message(role="system", content=CODING_AGENT_SYSTEM_PROMPT),
            Message(role="user", content=user_prompt),
        ]

        response = await self.model_client.chat(
            messages,
            temperature=self.temperature,
            max_tokens=2048,
        )

        return self._parse_response(response.content, design_output)

    def _parse_response(self, response_text: str, design_output: Optional[DesignOutput]) -> CodingOutput:
        """Parse model response into structured CodingOutput."""
        diff_text = self._extract_diff(response_text)
        files_changed = self._extract_files_changed(response_text, diff_text, design_output)
        explanations = self._extract_explanations(response_text)

        return CodingOutput(
            patches=[diff_text] if diff_text else [],
            diff=diff_text,
            explanations="\n".join(explanations),
            files_changed=files_changed,
        )

    def _extract_diff(self, response_text: str) -> str:
        """
        Extract unified diff from model response.

        Prefers fenced code blocks, but will fall back to raw diff content.
        """
        # Look for fenced code block first
        fenced_match = re.search(r"```(?:diff)?\s*(.*?)```", response_text, re.DOTALL | re.IGNORECASE)
        if fenced_match:
            return fenced_match.group(1).strip()

        # Look for explicit PATCH section
        if "PATCH:" in response_text.upper():
            after_patch = response_text.split("PATCH:", 1)[1]
            # Stop at files/explanations section if present
            stop_tokens = ["FILES CHANGED", "EXPLANATIONS", "FILES:"]
            for token in stop_tokens:
                if token in after_patch.upper():
                    after_patch = after_patch.split(token, 1)[0]
                    break
            return after_patch.strip()

        # Fallback: return lines that look like a diff
        diff_lines = [
            line for line in response_text.splitlines()
            if line.startswith(("+", "-", "@@")) or line.startswith(("diff ", "+++ ", "--- "))
        ]
        if diff_lines:
            return "\n".join(diff_lines).strip()

        return response_text.strip()

    def _extract_files_changed(
        self,
        response_text: str,
        diff_text: str,
        design_output: Optional[DesignOutput],
    ) -> list[str]:
        """Extract files changed from response or diff."""
        # Try to parse FILES CHANGED section
        section = self._extract_section(response_text, ["FILES CHANGED", "FILES"])
        files = self._extract_list(section) if section else []

        # Fallback: parse file paths from diff headers
        if not files and diff_text:
            header_matches = re.findall(r"^\+\+\+\s+[ab/]*([^\s]+)", diff_text, re.MULTILINE)
            files = list(dict.fromkeys(header_matches))  # dedupe while preserving order

        # Final fallback: use design target files if available
        if not files and design_output and design_output.target_files:
            files = design_output.target_files

        return files

    def _extract_explanations(self, response_text: str) -> list[str]:
        """Extract explanations section."""
        section = self._extract_section(response_text, ["EXPLANATIONS", "RATIONALE", "NOTES"])
        return self._extract_list(section) if section else []

    def _extract_section(self, text: str, headers: list[str]) -> str:
        """Extract section content following one of the provided headers."""
        for header in headers:
            pattern = re.compile(rf"{header}\s*:\s*", re.IGNORECASE)
            match = pattern.search(text)
            if match:
                after = text[match.end():]
                subsequent = re.split(r"\n[A-Z][A-Z\s]+:\s*", after, maxsplit=1)
                return subsequent[0].strip()
        return ""

    def _extract_list(self, section_text: str) -> list[str]:
        """Extract bullet/numbered lists from a section of text."""
        items = []
        for line in section_text.splitlines():
            cleaned = re.sub(r"^[-*•]\s*", "", line).strip()
            cleaned = re.sub(r"^\d+\.\s*", "", cleaned)
            if cleaned:
                items.append(cleaned)
        return items

    @staticmethod
    def build_code_context(repo_root: Path, candidate_files: list[str], max_bytes: int = 4000) -> Dict[str, str]:
        """
        Load code context from the repository for the provided candidate files.

        Only includes files that exist; content is truncated to avoid overly large prompts.
        """
        context: Dict[str, str] = {}
        for path in candidate_files:
            file_path = Path(repo_root) / path
            if not file_path.exists() or not file_path.is_file():
                continue
            try:
                content = file_path.read_text(encoding="utf-8")
                if len(content) > max_bytes:
                    suffix = "\n... [truncated]"
                    cutoff = max(0, max_bytes - len(suffix))
                    content = content[:cutoff] + suffix
                context[path] = content
            except OSError:
                continue
        return context
