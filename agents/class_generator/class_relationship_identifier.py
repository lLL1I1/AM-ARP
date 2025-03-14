# File: agents/relationship_identifier.py
"""RAG-enhanced Relationship Identifier"""
import json
import re
from typing import List, Union, Dict
from agentscope.agents import LlamaIndexAgent
from agentscope.message import Msg
import utils.util_function as uf


class ClassRelationshipIdentifier(LlamaIndexAgent):

    def __init__(
            self,
            name: str,
            model_config_name: str,
            sys_prompt: str,
            knowledge_id_list: List[str],
            recent_n_mem_for_retrieve: int = 3,
    ) -> None:
        sys_prompt = """## Relationship identification rules
            If you are a professional architect, please base on:
            1. Classes and their methods
            2. Relational mode in the knowledge base
            The RESULT must use the format: RESULT\n Class A-- relation type --> Class B\n... ` ` `"""

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
        related_patterns = uf._retrieve_knowledge(query, self.knowledge_list, self.similarity_top_k)

        full_prompt = (
            f"{self.sys_prompt}\n\n"
            f"[norm]\n{related_patterns}\n\n"
            f"[analysis object:]\n{query}\n\n"
            "list all relationship of class："
        )

        response_text = self.model(full_prompt).text
        return Msg(self.name, response_text, role="assistant")

    def identify_relationships(self, functions: Dict[str, List[str]], context: str) -> List[str]:
        analysis_input = f"function：{json.dumps(functions, ensure_ascii=False)}\ncontext：{context}"
        response = self.reply(Msg("user", analysis_input, role="assistant"))
        return self._parse_response(response.content)

    def _parse_response(self, content: str) -> List[str]:
        print('.....................relationship：.............................');
        print(content);
        if match := re.search(r'```RESULT\n(.*?)\n```', content, re.DOTALL):
            return [x.strip() for x in match.group(1).split('\n') if x.strip()]
        # return list(set(re.findall(r'.+?--.+?-->.*', content)))  
        return content