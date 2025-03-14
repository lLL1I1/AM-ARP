# File: agents/class_identifier.py
"""RAG-enhanced Class Identifier"""
import re
from typing import List, Union
from agentscope.agents import LlamaIndexAgent
from agentscope.message import Msg



class ClassIdentifier(LlamaIndexAgent):

    def __init__(
            self,
            name: str,
            model_config_name: str,
            sys_prompt: str,
            knowledge_id_list: List[str],
            recent_n_mem_for_retrieve: int = 3,
    ) -> None:

        sys_prompt = """## Class identification rules
            If you are a professional system architect, please follow the following:
            1. The service scenario entered by the user
            2. Class definition specifications in the knowledge base
            The results must be in the format:```RESULT\nClassName1\nClassName2\n...```"""

        super().__init__(
            name=name,
            sys_prompt=sys_prompt,
            model_config_name=model_config_name,
            knowledge_id_list=knowledge_id_list,
            similarity_top_k=3,
            recent_n_mem_for_retrieve=recent_n_mem_for_retrieve,
        )

    def reply(self, x: Union[Msg, List[Msg]]) -> Msg:
        query = self._extract_query(x)
        related_knowledge = self._retrieve_knowledge(query)

        full_prompt = (
            f"{self.sys_prompt}\n\n"
            f"[Class definition specification]\n{related_knowledge}\n\n"
            f"[business scenario]\n{query}\n\n"
            "list all class names:"
        )

        response_text = self.model(full_prompt).text
        return Msg(self.name, response_text, role="assistant")

    def _extract_query(self, x: Union[Msg, List[Msg]]) -> str:
        if isinstance(x, Msg):
            return x.content
        elif isinstance(x, list) and len(x) > 0:
            return x[-1].content
        return ""

    def _retrieve_knowledge(self, query: str) -> str:
        knowledge_str = ""
        for knowledge in self.knowledge_list:
            nodes = knowledge.retrieve(query, self.similarity_top_k)
            for node in nodes:
                knowledge_str += f"norm：{node.text}\nsource：{node.node.metadata}\n\n"
        return knowledge_str.strip()

    def identify_classes(self, context: str) -> List[str]:

        response = self.reply(Msg("user", context, role="assistant"))
        return self._parse_response(response.content)

    def _parse_response(self, content: str) -> List[str]:

        print('.....................class：.............................');
        print(content)
        # if match := re.search(r'```RESULT\n(.*?)\n```', content, re.DOTALL):
        #     return [x.strip() for x in match.group(1).split('\n') if x.strip()]
        # return list(set(re.findall(r'\b[A-Z][a-zA-Z]+\b', content))) 
        return content