# File: agents/function_identifier.py
"""RAG-enhanced Function Identifier"""
import re
import json
from typing import Dict, List, Union
from agentscope.agents import LlamaIndexAgent
from agentscope.message import Msg
import utils.util_function as uf

class FunctionIdentifier(LlamaIndexAgent):

    def __init__(
            self,
            name: str,
            model_config_name: str,
            sys_prompt: str,
            knowledge_id_list: List[str],
            recent_n_mem_for_retrieve: int = 3,
    ) -> None:
        sys_prompt = """## Method identification rules
        If you are a professional system designer, please base on:
        1. Classes and their attributes
        2. Method specifications in the knowledge base
        Results must be using JSON format: ` ` ` RESULT \ n {" name of the class ": [1 ()" method ", "method 2 ()"]} ` ` `"""

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
            f"[function rules:]\n{related_rules}\n\n"
            f"[analysis object:]\n{query}\n\n"
            "list all function of class："
        )

        response_text = self.model(full_prompt).text
        return Msg(self.name, response_text, role="assistant")
    def identify_functions(self, attributes: Dict[str, List[str]], context: str) -> Dict[str, List[str]]:
        analysis_input = f"attribute：{json.dumps(attributes, ensure_ascii=False)}\ncontext：{context}"
        response = self.reply(Msg("user", analysis_input, role="assistant"))
        return self._parse_response(response.content)

    def _parse_response(self, content: str) -> Dict[str, List[str]]:
        print('.....................function：.............................');
        print(content)
        try:
            if match := re.search(r'```RESULT\n(.*?)\n```', content, re.DOTALL):
                return json.loads(match.group(1))
        except Exception:
            pass


        functions = {}
        current_class = None
        for line in content.split('\n'):
            if "function" in line and "：" in line:
                current_class = line.split("：")[0].strip()
                functions[current_class] = []
            elif line.strip().startswith("- ") and "()" in line:
                functions[current_class].append(line.strip()[2:].split("(")[0] + "()")
        # return functions
        return content