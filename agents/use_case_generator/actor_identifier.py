# File: agents/use_case_generator/actor_identifier.py
"""RAG-enhanced Actor Identifier"""
import re
from typing import List, Union
from agentscope.agents import LlamaIndexAgent
from agentscope.message import Msg
import utils.util_function as uf


class ActorIdentifier(LlamaIndexAgent):
    """支持知识检索的参与者识别智能体"""

    def __init__(
            self,
            name: str,
            model_config_name: str,
            sys_prompt: str,
            knowledge_id_list: List[str],
            recent_n_mem_for_retrieve: int = 3,
    ) -> None:
        sys_prompt ="""## Actor Identification Rules
            You are a professional requirements analyst. Based on user input and the rules from the knowledge base:
            
            Identify all user roles and external systems.
            The result must use the format: RESULT\nActor 1\nActor 2\n..."""

        super().__init__(
            name=name,
            sys_prompt=sys_prompt,
            model_config_name=model_config_name,
            knowledge_id_list=knowledge_id_list,
            similarity_top_k=3,
            recent_n_mem_for_retrieve=recent_n_mem_for_retrieve,
        )

    def reply(self, x: Union[Msg, List[Msg]]) -> Msg:
        """处理输入并返回响应"""
        # 提取输入内容
        query = uf._extract_query(x)

        # 知识检索
        related_knowledge = uf._retrieve_knowledge(query, self.knowledge_list, self.similarity_top_k)

        # 构建提示
        full_prompt = (
            f"{self.sys_prompt}\n\n"
            f"[知识库内容]\n{related_knowledge}\n\n"
            f"[用户输入]\n{query}\n\n"
            "请列出所有参与者："
        )

        # 调用模型生成
        response_text = self.model(full_prompt).text
        return Msg(self.name, response_text, role="assistant")

    def identify_actors(self, background: str) -> List[str]:
        """对外接口"""
        response = self.reply(Msg("user", background, role="assistant"))

        return self._extract_actors(response.content)

    def _extract_actors(self, content: str) -> List[str]:
        """解析响应内容"""
        print('.....................所识别的参与者：.............................');
        print(content);
        if match := re.search(r'```RESULT\n(.*?)\n```', content, re.DOTALL):
            return [x.strip() for x in match.group(1).split('\n') if x.strip()]
        return list(set(re.findall(r'\d+\.\s*(.*?)(?:\n|$)', content)))