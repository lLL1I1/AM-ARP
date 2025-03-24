# File: agents/use_case_generator/dynamic_class_identifier.py
"""RAG-enhanced Dynamic Class Identifier for Class Diagrams"""
import re
from typing import List, Union
from agentscope.agents import LlamaIndexAgent
from agentscope.message import Msg


class DynamicClassIdentifier(LlamaIndexAgent):

    def __init__(
            self,
            name: str,
            model_config_name: str,
            sys_prompt: str,
            knowledge_id_list: List[str],
            recent_n_mem_for_retrieve: int = 3,
    ) -> None:
        sys_prompt = """## Final class list generation rule
            If you are a professional system analyst, please follow the change requirements and the latest class model in the knowledge base:
            1. Identify the class involved in the change (new/modified/deleted)
            2. Generate the complete class list after the change
            3. Results must be in a strict format:```RESULT\nclass1\nclass2\n...```"""

        super().__init__(
            name=name,
            sys_prompt=sys_prompt,
            model_config_name=model_config_name,
            knowledge_id_list=knowledge_id_list,
            similarity_top_k=3,
            recent_n_mem_for_retrieve=recent_n_mem_for_retrieve,
        )

    def reply(self, x: Union[Msg, List[Msg]]) -> Msg:
        full_prompt = (
            f"{self.sys_prompt}\n\n"
            "Generate the final class list of the format specification:"
        )
        return Msg(self.name, self.model(full_prompt).text, role="assistant")

    def get_final_classes(self, original_classes: List[str], change_request: str) -> List[str]:
        combined_classes = list(set(original_classes))
        return self._extract_classes(
            self.reply(
                Msg("user",
                    f"Refer to the following classes to generate an up-to-date list of classes:{str(combined_classes)}; Collecting and changing the requirements:{change_request}",
                    role="assistant")
            ).content
        )

    def _extract_classes(self, content: str) -> List[str]:
        if match := re.search(r'```RESULT\n(.*?)\n```', content, re.DOTALL):
            return list({x.strip() for x in match.group(1).split('\n') if x.strip()})
        return []