# File: agents/relationship_analyzer/dynamic_relation_identifier.py
"""RAG-enhanced Dynamic Relationship Identifier"""
import re
from typing import List, Dict, Union
from agentscope.agents import LlamaIndexAgent
from agentscope.message import Msg


class DynamicUCRelationshipIdentifier(LlamaIndexAgent):

    def __init__(
            self,
            name: str,
            model_config_name: str,
            sys_prompt: str,
            knowledge_id_list: List[str],
            recent_n_mem_for_retrieve: int = 5,
    ) -> None:
        sys_prompt = """## Relationship Change rules
            As a system architect, analyze the following elements:
            1. Current Participants: {actors}
            2. Current use cases: {use_cases}
            3. Change requirement: {change_request}
            4. Analyze relationship changes based on business rules

            Generation format:
            ```RESULT
            New:
            Subject -> Object
            ...
            Edited:
            Old Relationship -> New Relationship
            ...
            Removed:
            Subject -> Object
            ...```"""

        super().__init__(
            name=name,
            sys_prompt=sys_prompt,
            model_config_name=model_config_name,
            knowledge_id_list=knowledge_id_list,
            similarity_top_k=5,
            recent_n_mem_for_retrieve=recent_n_mem_for_retrieve,
        )

    def get_final_relations(
            self,
            current_actors: List[str],
            current_cases: List[str],
            change_request: str,
            original_relations: List[str] = None
    ) -> Dict[str, List[str]]:
        """ Gets relationship change analysis results
        Return: {" Add ": [], "Modify ": []," Delete ": []}
        """
        context = (
            f"participant:{', '.join(current_actors)}\n"
            f"use case:{', '.join(current_cases)}\n"
            f"Collecting and changing the requirements:{change_request}"
        )
        response = self.reply(Msg("user", context, role="user"))
        return self._analyze_changes(response.content, original_relations or [])

    def reply(self, x: Union[Msg, List[Msg]]) -> Msg:
        processed = self._format_response(super().reply(x).content)
        return Msg(self.name, processed, role="assistant")

    def _analyze_changes(
            self,
            response: str,
            original: List[str]
    ) -> Dict[str, List[str]]:
        changes = {
            "add": self._extract_section(response, "add"),
            "alter": self._parse_modifications(response),
            "delete": self._extract_section(response, "delete")
        }

        changes["delete"] = [r for r in changes["delete"] if r in original]
        return changes

    def _extract_section(self, text: str, section: str) -> List[str]:
        pattern = rf"{section}:\n((?:.+\n)*?)(?=\n\w+:|$)"
        if match := re.search(pattern, text, re.MULTILINE):
            return [line.strip() for line in match.group(1).split('\n') if line.strip()]
        return []

    def _parse_modifications(self, text: str) -> List[str]:
        mods = []
        pattern = r"alter:\n((?:.+\n)*?)(?=\n\w+:|$)"
        if match := re.search(pattern, text, re.MULTILINE):
            for line in match.group(1).split('\n'):
                if '->' in line and '=>' in line:
                    old, new = line.split('=>', 1)
                    mods.append(f"{old.strip()}->{new.strip()}")
        return mods

    def _format_response(self, raw: str) -> str:
        if "```RESULT" not in raw:
            return f"```RESULT\n{raw}\n```"
        return raw