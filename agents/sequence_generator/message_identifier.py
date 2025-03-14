# File: agents/message_identifier.py

import re
from typing import List, Union
from agentscope.agents import LlamaIndexAgent
from agentscope.message import Msg
import utils.util_function as uf


class MessageIdentifier(LlamaIndexAgent):

    def __init__(
            self,
            name: str,
            model_config_name: str,
            knowledge_id_list: List[str],
            recent_n_mem_for_retrieve: int = 3,
    ) -> None:

        sys_prompt = """## Message identification rules
            If you are a professional system architect, please follow the following:
            1. Object list
            2. Interaction modes in the knowledge base
            3. Enter a scenario
            The results must be in the format:```RESULT\nobjectA->objectB:message\n...```"""

        super().__init__(
            name=name,
            sys_prompt=sys_prompt,
            model_config_name=model_config_name,
            knowledge_id_list=knowledge_id_list,
            similarity_top_k=3,
            recent_n_mem_for_retrieve=recent_n_mem_for_retrieve,
        )

    def reply(self, x: Union[Msg, List[Msg]]) -> Msg:
        query = uf._extract_query(x)
        related_rules = uf._retrieve_knowledge(query, self.knowledge_list, self.similarity_top_k)

        full_prompt = (
            f"{self.sys_prompt}\n\n"
            f"[rules:]\n{related_rules}\n\n"
            f"[analysis scene:]\n{query}\n\n"
            "Lists all messages:"
        )

        response_text = self.model(full_prompt).text
        return Msg(self.name, response_text, role="assistant")
    def identify_messages(self, objects: List[str], context: str) -> List[str]:
        analysis_input = f"object list:{', '.join(objects)}\ncontext:{context}"
        response = self.reply(Msg("user", analysis_input, role="assistant"))
        return self._parse_response(response.content)

    def _parse_response(self, content: str) -> List[str]:
        print('.....................message:.............................')
        print(content)
        if match := re.search(r'```RESULT\n(.*?)\n```', content, re.DOTALL):
            return [x.strip() for x in match.group(1).split('\n') if x.strip()]
        # return list(set(re.findall(r'.+?->.+?:.+', content)))
        return content