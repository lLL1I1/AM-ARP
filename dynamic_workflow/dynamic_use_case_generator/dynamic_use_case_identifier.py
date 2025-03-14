# File: agents/use_case_generator/dynamic_use_case_identifier.py
"""RAG-enhanced Dynamic Use Case Identifier"""
import re
from typing import List, Union, Dict
from agentscope.agents import LlamaIndexAgent
from agentscope.message import Msg


class DynamicUseCaseIdentifier(LlamaIndexAgent):
    def __init__(
            self,
            name: str,
            model_config_name: str,
            sys_prompt: str,
            knowledge_id_list: List[str],
            recent_n_mem_for_retrieve: int = 5,  
    ) -> None:
        sys_prompt = """## use-case analysis rules
            As a senior business analyst, generate a list of changed use cases based on the following elements:
            1. List of current participants: {actors}
            2. Change request Description: {change_request}
            3. Service process rules in the knowledge base
            4. Output format:```RESULT\nusecase1\nusecase2\n...```"""

        super().__init__(
            name=name,
            sys_prompt=sys_prompt,
            model_config_name=model_config_name,
            knowledge_id_list=knowledge_id_list,
            similarity_top_k=5,  
            recent_n_mem_for_retrieve=recent_n_mem_for_retrieve,
        )

    def reply(self, x: Union[Msg, List[Msg]]) -> Msg:
        return Msg(
            self.name,
            self._format_response(self.model(self._build_prompt(x)).text),
            role="assistant"
        )

    def get_final_use_cases(
            self,
            current_actors: List[str],
            change_request: str,
            original_use_cases: List[str] = None
    ) -> Dict[str, List[str]]:
        """External interface: Generate a list of post-change use cases
            Return format: {" Add ": [], "Modify ": []," Delete": []}
        """
        prompt = (
            f"Current Participants:{', '.join(current_actors)}\n"
            f"Change requirements:{change_request}\n"
            f"Original use case:{original_use_cases or 'none'}"
        )
        response = self.reply(Msg("user", prompt, role="assistant"))
        return self._analyze_changes(response.content, original_use_cases)

    def _build_prompt(self, msg: Union[Msg, List[Msg]]) -> str:

        base_prompt = super().reply(msg).content


        return f"{base_prompt}\nPlease output in the following categories: Add/Modify/Delete Use cases"

    def _format_response(self, raw_text: str) -> str:
        if "```RESULT" not in raw_text:
            return f"```RESULT\n{raw_text}\n```"
        return raw_text

    def _analyze_changes(
            self,
            response: str,
            original_cases: List[str]
    ) -> Dict[str, List[str]]:
        new_cases = self._extract_use_cases(response)

        result = {"add": [], "alter": [], "delete": []}
        if original_cases:
            result["add"] = [uc for uc in new_cases if uc not in original_cases]
            result["delete"] = [uc for uc in original_cases if uc not in new_cases]
        else:
            result["add"] = new_cases
        return result

    def _extract_use_cases(self, content: str) -> List[str]:
        if match := re.search(r'```RESULT\n(.*?)\n```', content, re.DOTALL):
            return list({
                self._clean_use_case_name(line.strip())
                for line in match.group(1).split('\n')
                if line.strip()
            })
        return []

    def _clean_use_case_name(self, name: str) -> str:
        return re.sub(r'[【】$$$$()<>「」]', '', name).strip()