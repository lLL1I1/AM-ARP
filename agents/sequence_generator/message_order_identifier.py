# File: agents/message_order_identifier.py

import re
from typing import List, Union
from agentscope.agents import LlamaIndexAgent
from agentscope.message import Msg
import utils.util_function as uf


class MessageOrderIdentifier(LlamaIndexAgent):

    def __init__(
            self,
            name: str,
            model_config_name: str,
            knowledge_id_list: List[str],
            recent_n_mem_for_retrieve: int = 3,
    ) -> None:
        sys_prompt = """## Message sequence identification rules
            You are a professional process analyst based on:
            1. Message list
            2. Process specifications in the knowledge base
            3. Enter a scenario
            Results must be formatted:```RESULT\n1. message1\n2. message2\n...```"""

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
            f"[analysis content]\n{query}\n\n"
            "Determines the order in which messages are executed:"
        )

        response_text = self.model(full_prompt).text
        return Msg(self.name, response_text, role="assistant")

    def identify_sequence(self, messages: List[str], context: str) -> List[str]:
        analysis_input = f"message list:\n" + "\n".join(messages) + f"\n context:{context}"
        response = self.reply(Msg("user", analysis_input, role="assistant"))

        return self._parse_response(response.content)

    def _parse_response(self, content: str) -> List[str]:
        print('.....................results:.............................');
        print(content);
        if match := re.search(r'```RESULT\n(.*?)\n```', content, re.DOTALL):
            return [x.strip() for x in match.group(1).split('\n') if x.strip()]
        # return list(set(re.findall(r'\d+\.\s*.+', content)))
        return content