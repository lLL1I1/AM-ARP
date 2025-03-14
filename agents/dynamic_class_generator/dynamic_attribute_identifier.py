# File: agents/class_diagram_generator/dynamic_attribute_identifier.py
"""RAG-enhanced Dynamic Attribute Identifier for Class Diagrams"""
import re
from typing import List, Union
from agentscope.agents import LlamaIndexAgent
from agentscope.message import Msg


class DynamicAttributeIdentifier(LlamaIndexAgent):

    def __init__(
            self,
            name: str,
            model_config_name: str,
            sys_prompt: str,
            knowledge_id_list: List[str],
            recent_n_mem_for_retrieve: int = 3,
    ) -> None:
        sys_prompt = """## Final attribute list generation rule
        If you are a professional system analyst, please follow the change requirements and the latest class attribute model in the knowledge base:
        1. Identify the properties involved in the change (new/modified/deleted)
        2. Generate the complete list of properties after the change (format: class name. Stats)
        3. Results must be in a strict format:```RESULT\nClass name. Attribute 1\n class name. Attribute 2\n... ` ` ` """

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
            "Generate the final attribute list for the format specification:"
        )
        return Msg(self.name, self.model(full_prompt).text, role="assistant")

    def get_final_attributes(self, original_attributes: List[str], change_request: str) -> List[str]:
        combined_attrs = list(set(original_attributes))
        return self._extract_attributes(
            self.reply(
                Msg("user",
                    f"Refer to the following properties to generate the latest list:{str(combined_attrs)}; Change requirements:{change_request}",
                    role="assistant")
            ).content
        )

    def _extract_attributes(self, content: str) -> List[str]:
        if match := re.search(r'```RESULT\n(.*?)\n```', content, re.DOTALL):
            return list({x.strip() for x in match.group(1).split('\n') if x.strip() and '.' in x})
        return []