# File: agents/class_diagram_generator/dynamic_attribute_identifier.py
"""RAG-enhanced Dynamic Attribute Identifier for Class Diagrams"""
import re
from typing import List, Union
from agentscope.agents import LlamaIndexAgent
from agentscope.message import Msg


class DynamicAttributeIdentifier(LlamaIndexAgent):
    """支持知识检索的类属性变更识别智能体"""

    def __init__(
            self,
            name: str,
            model_config_name: str,
            sys_prompt: str,
            knowledge_id_list: List[str],
            recent_n_mem_for_retrieve: int = 3,
    ) -> None:
        sys_prompt = """## 最终属性列表生成规则
            你是一个专业的系统分析师，请根据变更需求和知识库中的最新类属性模型：
            1. 识别变更涉及的属性（新增/修改/删除）
            2. 生成变更后的完整属性列表（格式：类名.属性）
            3. 结果必须使用严格格式：```RESULT\n类名.属性1\n类名.属性2\n...```"""

        super().__init__(
            name=name,
            sys_prompt=sys_prompt,
            model_config_name=model_config_name,
            knowledge_id_list=knowledge_id_list,
            similarity_top_k=3,
            recent_n_mem_for_retrieve=recent_n_mem_for_retrieve,
        )

    def reply(self, x: Union[Msg, List[Msg]]) -> Msg:
        """处理输入并生成最终属性列表"""
        full_prompt = (
            f"{self.sys_prompt}\n\n"
            "请生成格式规范的最终属性列表："
        )
        return Msg(self.name, self.model(full_prompt).text, role="assistant")

    def get_final_attributes(self, original_attributes: List[str], change_request: str) -> List[str]:
        """对外接口：获取变更后属性列表"""
        combined_attrs = list(set(original_attributes))
        return self._extract_attributes(
            self.reply(
                Msg("user",
                    f"参考以下属性生成最新列表:{str(combined_attrs)}; 变更需求:{change_request}",
                    role="assistant")
            ).content
        )

    def _extract_attributes(self, content: str) -> List[str]:
        """解析标准化响应"""
        if match := re.search(r'```RESULT\n(.*?)\n```', content, re.DOTALL):
            return list({x.strip() for x in match.group(1).split('\n') if x.strip() and '.' in x})
        return []