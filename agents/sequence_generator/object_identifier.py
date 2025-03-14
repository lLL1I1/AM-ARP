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
        sys_prompt = """## 对象识别规则
            你是一个专业的需求分析师，请根据用户输入和知识库：
            1. 识别系统交互对象（类、实体、组件等）
            2. 结果必须使用格式：```RESULT\n对象1\n对象2\n...```"""

        super().__init__(
            name=name,
            sys_prompt=sys_prompt,
            model_config_name=model_config_name,
            knowledge_id_list=knowledge_id_list,
            similarity_top_k=3,
            recent_n_mem_for_retrieve=recent_n_mem_for_retrieve,
        )

    def reply(self, x: Union[Msg, List[Msg]]) -> Msg:
        """覆盖父类方法，确保输入为字符串"""
        query = uf._extract_query(x)
        related_knowledge = uf._retrieve_knowledge(query, self.knowledge_list, self.similarity_top_k)

        full_prompt = (
            f"{self.sys_prompt}\n\n"
            f"[知识库内容]\n{related_knowledge}\n\n"
            f"[分析文本]\n{query}\n\n"
            "请列出所有交互对象："
        )

        response_text = self.model(full_prompt).text
        return Msg(self.name, response_text, role="assistant")

    def identify_objects(self, context: str) -> List[str]:
        """对外接口"""
        response = self.reply(Msg("user", context, role="assistant"))
        return self._parse_response(response.content)

    def _parse_response(self, content: str) -> List[str]:
        """解析响应内容"""
        print('.....................所识别的对象：.............................');
        print(content)
        if match := re.search(r'```RESULT\n(.*?)\n```', content, re.DOTALL):
            return [x.strip() for x in match.group(1).split('\n') if x.strip()]
        return list(set(re.findall(r'\d+\.\s*(.*?)(?:\n|$)', content)))