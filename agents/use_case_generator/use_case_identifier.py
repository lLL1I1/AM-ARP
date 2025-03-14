# File: agents/use_case_generator/use_case_identifier.py
"""RAG-enhanced UseCase Identifier"""
import re
from typing import List, Union
from agentscope.agents import LlamaIndexAgent
from agentscope.message import Msg
import utils.util_function as uf


class UseCaseIdentifier(LlamaIndexAgent):
    """支持模式库检索的用例识别智能体"""

    def __init__(
            self,
            name: str,
            model_config_name: str,
            sys_prompt: str,
            knowledge_id_list: List[str],
            recent_n_mem_for_retrieve: int = 3,
    ) -> None:
        # 固化系统提示
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
        """覆盖父类方法，确保输入为字符串"""
        # 提取输入内容
        query = uf._extract_query(x)

        # 知识检索
        related_knowledge = self._retrieve_knowledge(query)

        # 构建完整提示
        full_prompt = (
            f"{self.sys_prompt}\n\n"
            f"[the content of knowledge bank:]\n{related_knowledge}\n\n"
            f"[user input:]\n{query}\n\n"
            "Please list all system use cases："
        )

        # 调用模型生成
        response_text = self.model(full_prompt).text
        return Msg(self.name, response_text, role="assistant")

    def _retrieve_knowledge(self, query: str) -> str:
        """执行知识检索"""
        knowledge_str = ""
        for knowledge in self.knowledge_list:
            nodes = knowledge.retrieve(query, self.similarity_top_k)
            for node in nodes:
                knowledge_str += f"来源：{node.node.metadata}\n内容：{node.text}\n\n"
        return knowledge_str.strip()

    def identify_use_cases(self, background: str) -> List[str]:
        """对外接口"""
        response = self.reply(Msg("user", background, role="assistant"))

        return self._extract_use_cases(response.content)

    def _extract_use_cases(self, content: str) -> List[str]:
        """解析响应内容"""
        print('.....................所识别的用例：.............................');
        print(content);
        # 严格模式匹配代码块
        if match := re.search(r'```RESULT\n(.*?)\n```', content, re.DOTALL):
            return [x.strip() for x in match.group(1).split('\n') if x.strip()]

        # 降级解析带编号列表
        return list(set(re.findall(r'\d+\.\s*(.*?)(?:\n|$)', content)))