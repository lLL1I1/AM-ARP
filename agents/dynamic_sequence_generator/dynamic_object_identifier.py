# File: agents/sequence_modeling/dynamic_object_identifier.py
"""RAG-enhanced Dynamic Object Identifier for Sequence Diagrams"""
import re
from typing import List, Union
from agentscope.agents import LlamaIndexAgent
from agentscope.message import Msg


class DynamicObjectIdentifier(LlamaIndexAgent):
    """Sequence diagram object change identification agent with knowledge retrieval support"""

    def __init__(
            self,
            name: str,
            model_config_name: str,
            sys_prompt: str,
            knowledge_id_list: List[str],
            recent_n_mem_for_retrieve: int = 3,
    ) -> None:
        sys_prompt = """## Final Object List Generation Rules
            You are a professional system architect. Based on the change request and the latest sequence diagram model in the knowledge base:
            1. Identify objects involved in the changes (addition/rename/deletion)
            2. Generate a complete list of objects after the change (format: object_name:type)
            3. Supported object types: Actor, System, Database, Service, Component
            4. The result must use the strict format: ```RESULT\nobject1\nobject2\n...```"""

        super().__init__(
            name=name,
            sys_prompt=sys_prompt,
            model_config_name=model_config_name,
            knowledge_id_list=knowledge_id_list,
            similarity_top_k=3,
            recent_n_mem_for_retrieve=recent_n_mem_for_retrieve,
        )

    def reply(self, x: Union[Msg, List[Msg]]) -> Msg:
        """Process input and generate the final object list"""
        full_prompt = (
            f"{self.sys_prompt}\n\n"
            "Please generate a list of objects with type annotations:"
        )
        return Msg(self.name, self.model(full_prompt).text, role="assistant")

    def get_final_objects(self, original_objects: List[str], change_request: str) -> List[str]:
        """Public interface: Get the list of objects after changes"""
        combined_objs = list(set(original_objects))
        return self._extract_objects(
            self.reply(
                Msg("user",
                    f"Refer to the following objects to generate the latest list:{str(combined_objs)}; Change request:{change_request}",
                    role="assistant")
            ).content
        )

    def _extract_objects(self, content: str) -> List[str]:
        """Parse standardized responses and validate object formats"""
        if match := re.search(r'```RESULT\n(.*?)\n```', content, re.DOTALL):
            valid_objects = []
            for item in match.group(1).split('\n'):
                item = item.strip()
                if item and re.match(r"^\w+:(\w+)(\s*#\w+)?$", item):
                    valid_objects.append(item)
            return list(set(valid_objects))
        return []


# Usage example
if __name__ == "__main__":
    obj_identifier = DynamicObjectIdentifier(
        name="Object Identifier",
        model_config_name="gpt-4",
        knowledge_id_list=["seq_objects_knowledge"]
    )

    # Example scenario: Payment system upgrade
    original = ["User:Actor", "PaymentService:System"]
    change = "1. Add Risk Control Service Component 2. Split PaymentService into AlipayService and WechatPayService"

    new_objects = obj_identifier.get_final_objects(original, change)
    # Possible output:
    # ["User:Actor", "RiskControlService:Component",
    #  "AlipayService:System", "WechatPayService:System"]