# File: agents/use_case_generator/uc_relationship_identifier.py
"""RAG-enhanced Relationship Identifier"""
import re
from typing import List, Union
from agentscope.agents import LlamaIndexAgent
from agentscope.message import Msg
import utils.util_function as uf

class UCRelationshipIdentifier(LlamaIndexAgent):

    def __init__(
            self,
            name: str,
            model_config_name: str,
            sys_prompt: str,
            knowledge_id_list: List[str],
            recent_n_mem_for_retrieve: int = 3,
    ) -> None:
        sys_prompt = sys_prompt = """## SYSTEM PROMPT
            You are a professional use case relationship identification assistant. Please strictly follow the requirements below:
            1. Identify association relationships between actors and use cases.
            2. Identify include/extend relationships between use cases.
            3. Output the type of relationships in the result!
            3. The result must be returned in the following format:
            ```RESULT
            Actor --association--> UseCase1  type:association
            UseCase1 --include--> UseCase2   type:include
            UseCase3 --extend--> UseCase4    type:extend
            ...
            ```"""

        super().__init__(
            name=name,
            sys_prompt=sys_prompt,
            model_config_name=model_config_name,
            knowledge_id_list=knowledge_id_list,
            similarity_top_k=3,
            recent_n_mem_for_retrieve=recent_n_mem_for_retrieve
        )

    def reply(self, x: Union[Msg, List[Msg]]) -> Msg:
        query = uf._extract_query(x)

        related_rules = uf._retrieve_knowledge(query, self.knowledge_list, self.similarity_top_k)

        full_prompt = (
            f"{self.sys_prompt}\n\n"
            f"[relationship rules:]\n{related_rules}\n\n"
            f"[analytic target]\n{query}\n\n"
            "List all the relationships in the use case model in the analysis:The result must be returned in the following format:RESULTActor --association--> UseCase1  type:associationUseCase1 --include--> UseCase2   type:includeUseCase3 --extend--> UseCase4    type:extend"
        )

        response_text = self.model(full_prompt).text
        return Msg(self.name, response_text, role="assistant")

    def identify_relationships(
            self,
            use_cases: List[str],
            actors: List[str],
            background: str
    ) -> List[str]:
   

        analysis_input = (
            f"background:{background}\n"
            f"actor:{', '.join(actors)}\n"
            f"usecase:{', '.join(use_cases)}"
        )

        response = self.reply(Msg("user", analysis_input, role="assistant"))

        return self._extract_relationships(response.content)

    def _extract_relationships(self, content: str) -> List[str]:
        print('.....................relationship:.............................');
        print(content)

        if match := re.search(r'```RESULT\n(.*?)\n```', content, re.DOTALL):
            return [x.strip() for x in match.group(1).split('\n') if x.strip()]

        return list(set(re.findall(r'.+?(?:-->|—).+', content)))