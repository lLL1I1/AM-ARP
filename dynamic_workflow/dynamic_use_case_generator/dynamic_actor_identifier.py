# File: agents/use_case_generator/updated_actor_lister.py
"""RAG-enhanced Updated Actor Lister"""
import re
from typing import List, Union
from agentscope.agents import LlamaIndexAgent
from agentscope.message import Msg


class DynamicActorIdentifier(LlamaIndexAgent):

    def __init__(
            self,
            name: str,
            model_config_name: str,
            sys_prompt: str,
            knowledge_id_list: List[str],
            recent_n_mem_for_retrieve: int = 3,
    ) -> None:
        sys_prompt = """## Final participant list generation rule
        You are a professional requirements analyst, based on the change requirements and the latest participant model in the knowledge base:
        1. Generate a complete list of participants after the change
        2. Results must be in a strict format:```RESULT\nparticipant 1\nparticipant 2\n...```"""

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
            "Generate a list of final participants for the format specification:"
        )

        return Msg(self.name, self.model(full_prompt).text, role="assistant")

    def get_final_actors(self, original_actors: List[str], change_request: str) -> List[str]:

        combined_actors = list(set(original_actors))
        return self._extract_actors(self.reply(Msg("user", "Refer to the following to generate an updated list of participants:" + str(combined_actors) + ";Collecting and changing the requirements:" + change_request, role="assistant")).content)

    def _extract_actors(self, content: str) -> List[str]:
        if match := re.search(r'```RESULT\n(.*?)\n```', content, re.DOTALL):
            return list({x.strip() for x in match.group(1).split('\n') if x.strip()})
        return []