# File: agents/class_identifier.py
"""RAG-enhanced Class Identifier"""
import re
from typing import List, Union
from agentscope.agents import LlamaIndexAgent
from agentscope.message import Msg



class ClassIdentifier(LlamaIndexAgent):
    """支持知识检索的类识别智能体"""

    def __init__(
            self,
            name: str,
            model_config_name: str,
            sys_prompt: str,
            knowledge_id_list: List[str],
            recent_n_mem_for_retrieve: int = 3,
    ) -> None:
        # 固化系统提示
        sys_prompt = """## 类识别规则
            你是一个专业的系统架构师，请根据以下内容：
            1. 用户输入的业务场景
            2. 知识库中的类定义规范
            结果必须使用格式：```RESULT\nClassName1\nClassName2\n...```"""

        super().__init__(
            name=name,
            sys_prompt=sys_prompt,
            model_config_name=model_config_name,
            knowledge_id_list=knowledge_id_list,
            similarity_top_k=3,
            recent_n_mem_for_retrieve=recent_n_mem_for_retrieve,
        )

    def reply(self, x: Union[Msg, List[Msg]]) -> Msg:
        """处理输入并生成响应"""
        query = self._extract_query(x)
        related_knowledge = self._retrieve_knowledge(query)

        full_prompt = (
            f"{self.sys_prompt}\n\n"
            f"[类定义规范]\n{related_knowledge}\n\n"
            f"[业务场景]\n{query}\n\n"
            "请列出所有类名："
        )

        response_text = self.model(full_prompt).text
        return Msg(self.name, response_text, role="assistant")

    def _extract_query(self, x: Union[Msg, List[Msg]]) -> str:
        """提取查询内容"""
        if isinstance(x, Msg):
            return x.content
        elif isinstance(x, list) and len(x) > 0:
            return x[-1].content
        return ""

    def _retrieve_knowledge(self, query: str) -> str:
        """执行知识检索"""
        knowledge_str = ""
        for knowledge in self.knowledge_list:
            nodes = knowledge.retrieve(query, self.similarity_top_k)
            for node in nodes:
                knowledge_str += f"规范：{node.text}\n来源：{node.node.metadata}\n\n"
        return knowledge_str.strip()

    def identify_classes(self, context: str) -> List[str]:
        """对外接口"""
        response = self.reply(Msg("user", context, role="assistant"))
        return self._parse_response(response.content)

    def _parse_response(self, content: str) -> List[str]:
        """解析响应内容"""
        print('.....................所识别的类：.............................');
        print(content);
        if match := re.search(r'```RESULT\n(.*?)\n```', content, re.DOTALL):
            return [x.strip() for x in match.group(1).split('\n') if x.strip()]
        return list(set(re.findall(r'\b[A-Z][a-zA-Z]+\b', content)))  # 匹配大写开头的单词