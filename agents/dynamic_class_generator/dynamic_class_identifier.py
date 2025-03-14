# File: agents/use_case_generator/dynamic_class_identifier.py
"""RAG-enhanced Dynamic Class Identifier for Class Diagrams"""
import re
from typing import List, Union
from agentscope.agents import LlamaIndexAgent
from agentscope.message import Msg


class DynamicClassIdentifier(LlamaIndexAgent):
    """支持知识检索的类图变更识别智能体"""

    def __init__(
            self,
            name: str,
            model_config_name: str,
            sys_prompt: str,
            knowledge_id_list: List[str],
            recent_n_mem_for_retrieve: int = 3,
    ) -> None:
        sys_prompt = """## 最终类列表生成规则
            你是一个专业的系统分析师，请根据变更需求和知识库中的最新类模型：
            1. 识别变更涉及的类（新增/修改/删除）
            2. 生成变更后的完整类列表
            3. 结果必须使用严格格式：```RESULT\n类名1\n类名2\n...```"""

        super().__init__(
            name=name,
            sys_prompt=sys_prompt,
            model_config_name=model_config_name,
            knowledge_id_list=knowledge_id_list,
            similarity_top_k=3,
            recent_n_mem_for_retrieve=recent_n_mem_for_retrieve,
        )

    def reply(self, x: Union[Msg, List[Msg]]) -> Msg:
        """处理输入并生成最终类列表"""
        full_prompt = (
            f"{self.sys_prompt}\n\n"
            "请生成格式规范的最终类列表："
        )
        return Msg(self.name, self.model(full_prompt).text, role="assistant")

    def get_final_classes(self, original_classes: List[str], change_request: str) -> List[str]:
        """对外接口：获取变更后类列表"""
        combined_classes = list(set(original_classes))
        return self._extract_classes(
            self.reply(
                Msg("user",
                    f"参考以下类生成最新类列表:{str(combined_classes)}; 变更需求:{change_request}",
                    role="assistant")
            ).content
        )

    def _extract_classes(self, content: str) -> List[str]:
        """解析标准化响应"""
        if match := re.search(r'```RESULT\n(.*?)\n```', content, re.DOTALL):
            return list({x.strip() for x in match.group(1).split('\n') if x.strip()})
        return []