# File: agents/use_case_generator/use_case_identifier.py
"""RAG-enhanced UseCase Identifier"""
import re
from typing import List, Union
from agentscope.agents import LlamaIndexAgent
from agentscope.message import Msg
import utils.util_function as uf


class UseCaseIdentifier(LlamaIndexAgent):

    def __init__(
            self,
            name: str,
            model_config_name: str,
            sys_prompt: str,
            knowledge_id_list: List[str],
            recent_n_mem_for_retrieve: int = 3,
    ) -> None:
        sys_prompt = """## Use Case Identification Rules
                You are a professional requirements analyst. Based on user input and patterns from the knowledge base:
                
                Identify all functional use cases of the system.
                The result must use the format: RESULT\nUse Case 1\nUse Case 2\n..."""

        super().__init__(
            name=name,
            sys_prompt=sys_prompt,
            model_config_name=model_config_name,
            knowledge_id_list=knowledge_id_list,
            similarity_top_k=2,
            recent_n_mem_for_retrieve=recent_n_mem_for_retrieve
        )

    def reply(self, x: Union[Msg, List[Msg]]) -> Msg:

        query = uf._extract_query(x)

        related_knowledge = self._retrieve_knowledge(query)

        full_prompt = (
            f"{self.sys_prompt}\n\n"
            f"[the content of knowledge bank:]\n{related_knowledge}\n\n"
            f"[user input:]\n{query}\n\n"
            "Please list all system use cases："
        )


        response_text = self.model(full_prompt).text
        return Msg(self.name, response_text, role="assistant")

    def _retrieve_knowledge(self, query: str) -> str:

        knowledge_str = ""
        for knowledge in self.knowledge_list:
            nodes = knowledge.retrieve(query, self.similarity_top_k)
            for node in nodes:
                knowledge_str += f"source：{node.node.metadata}\ncontent：{node.text}\n\n"
        return knowledge_str.strip()

    def identify_use_cases(self, background: str) -> List[str]:

        response = self.reply(Msg("user", background, role="assistant"))

        return self._extract_use_cases(response.content)

    def _extract_use_cases(self, content: str) -> List[str]:

        print('.....................the result of usecase:.............................');
        print(content);

        if match := re.search(r'```RESULT\n(.*?)\n```', content, re.DOTALL):
            return [x.strip() for x in match.group(1).split('\n') if x.strip()]


        return list(set(re.findall(r'\d+\.\s*(.*?)(?:\n|$)', content)))