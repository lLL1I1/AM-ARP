# File: agents/class_diagram_generator/dynamic_method_identifier.py
"""RAG-enhanced Dynamic Method Identifier for Class Diagrams"""
import re
from typing import List, Union
from agentscope.agents import LlamaIndexAgent
from agentscope.message import Msg


class DynamicMethodIdentifier(LlamaIndexAgent):

    def __init__(
            self,
            name: str,
            model_config_name: str,
            sys_prompt: str,
            knowledge_id_list: List[str],
            recent_n_mem_for_retrieve: int = 3,
    ) -> None:
        sys_prompt = """## Final method list generation rule
        If you are a professional system analyst, please follow the change requirements and the latest class method model in the knowledge base:
        1. Identify the method involved in the change (add/modify parameters/rename/delete)
        2. Generate the complete list of changed methods (format: class name. Method name (parameter))
        3. The method signature must contain the required parameter types
        4. Results must be in a strict format:```RESULT\nclass.function1\nclass.function2\n...```"""

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
            "Generate a final list of methods with full method signatures:"
        )
        return Msg(self.name, self.model(full_prompt).text, role="assistant")

    def get_final_methods(self, original_methods: List[str], change_request: str) -> List[str]:
        combined_methods = list(set(original_methods))
        return self._extract_methods(
            self.reply(
                Msg("user",
                    f"Refer to the following method to generate the latest list:{str(combined_methods)}; Collecting and changing the requirements:{change_request}",
                    role="assistant")
            ).content
        )

    def _extract_methods(self, content: str) -> List[str]:
        if match := re.search(r'```RESULT\n(.*?)\n```', content, re.DOTALL):
            valid_methods = []
            for item in match.group(1).split('\n'):
                item = item.strip()
                if not item:
                    continue

                if re.match(r"^\w+\.\w+$([\w: ,]*)$$", item):
                    valid_methods.append(item)
            return list(set(valid_methods))
        return []