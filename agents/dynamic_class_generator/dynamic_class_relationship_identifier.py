# File: agents/class_diagram_generator/dynamic_relation_identifier.py
"""RAG-enhanced Dynamic Relation Identifier for Class Diagrams"""
import re
from typing import List, Union
from agentscope.agents import LlamaIndexAgent
from agentscope.message import Msg


class DynamicRelationIdentifier(LlamaIndexAgent):

    RELATION_PATTERN = r"^\w+\s*(<|:)\s*\w+\s*(>|:)\s*\w+$"  # 支持 <继承> 和 :association> 两种格式

    def __init__(
            self,
            name: str,
            model_config_name: str,
            sys_prompt: str,
            knowledge_id_list: List[str],
            recent_n_mem_for_retrieve: int = 3,
    ) -> None:
        sys_prompt = """## Final relationship list generation rule
            If you are a professional system architect, please follow the change requirements and the latest class relationship model in the knowledge base:
            1. Identify the class relationship involved in the change (new/modified/deleted)
            2. Generate a complete list of changed relationships (format: class name 1 < Relationship type > Class name 2)
            3. Supported relationship types :inheritance (<:inheritance>), composition (<:composition>), aggregation (<:aggregation>), association (<:association>), dependency (<:dependency>)
            4. Results must be in a strict format:```RESULT\nrelationship1\nrelationship2\n...```"""

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
            "Generate a standardized list of class relationships:"
        )
        return Msg(self.name, self.model(full_prompt).text, role="assistant")

    def get_final_relations(self, original_relations: List[str], change_request: str) -> List[str]:
        combined_relations = list(set(original_relations))
        return self._extract_relations(
            self.reply(
                Msg("user",
                    f"Refer to the following relationships to generate the latest list:{str(combined_relations)}; Change requirements:{change_request}",
                    role="assistant")
            ).content
        )

    def _extract_relations(self, content: str) -> List[str]:
        if match := re.search(r'```RESULT\n(.*?)\n```', content, re.DOTALL):
            valid_relations = []
            for item in match.group(1).split('\n'):
                item = self._normalize_relation(item.strip())
                if item and re.match(self.RELATION_PATTERN, item):
                    valid_relations.append(item)
            return list(set(valid_relations))
        return []

    def _normalize_relation(self, relation: str) -> str:
        replacements = {
            "<extend>": "<:inheritance>",
            "<composition>": "<:composition>",
            "<aggregation>": "<:aggregation>",
            "<correlation>": "<:association>",
            "<Dependency>": "<:dependency>"
        }
        for chi, eng in replacements.items():
            relation = relation.replace(chi, eng)
        return relation.replace(" ", "")  


if __name__ == "__main__":
    relation_identifier = DynamicRelationIdentifier(
        name="Relation identifier",
        model_config_name="gpt-4",
        knowledge_id_list=["class_relations_knowledge"]
    )

    original = ["User <extend> Admin", "Order <Association> Product"]
    change = "1. split Admin to SystemAdmin and ContentAdmin 2. add user hierarchy."

    new_relations = relation_identifier.get_final_relations(original, change)
    # output：
    # ["User<:inheritance>SystemAdmin", "User<:inheritance>ContentAdmin",
    #  "Order<:association>Product", "User<:association>UserLevel"]