# File: agents/object_identifier.py
"""对象识别智能体"""
import re
from typing import List, Union
from agentscope.agents import LlamaIndexAgent
from agentscope.message import Msg
import utils.util_function as uf


class ObjectIdentifier(LlamaIndexAgent):
    """支持知识检索的对象识别智能体"""

    def __init__(
            self,
            name: str,
            model_config_name: str,
            knowledge_id_list: List[str],
            recent_n_mem_for_retrieve: int = 3,
    ) -> None:
        # 固化系统提示
        sys_prompt = """## Object recognition rules
            You are a professional demand analyst, based on user input and knowledge base:
            1. Identify system interaction objects (classes, entities, components, etc.)
            2. The RESULT must use the format: RESULT\n object 1\n object 2\n... ` ` `"""

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
        related_knowledge = uf._retrieve_knowledge(query, self.knowledge_list, self.similarity_top_k)

        full_prompt = (
            f"{self.sys_prompt}\n\n"
            f"[knowledge content]\n{related_knowledge}\n\n"
            f"[analysis content:]\n{query}\n\n"
            "list all object:"
        )

        response_text = self.model(full_prompt).text
        return Msg(self.name, response_text, role="assistant")

    def identify_objects(self, context: str) -> List[str]:
        response = self.reply(Msg("user", context, role="assistant"))
        return self._parse_response(response.content)

    def _parse_response(self, content: str) -> List[str]:"
        print('.....................object:.............................');
        print(content)
        if match := re.search(r'```RESULT\n(.*?)\n```', content, re.DOTALL):
            return [x.strip() for x in match.group(1).split('\n') if x.strip()]
        return list(set(re.findall(r'\d+\.\s*(.*?)(?:\n|$)', content)))