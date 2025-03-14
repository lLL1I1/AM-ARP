# File: agents/class_diagram_generator/dynamic_method_identifier.py
"""RAG-enhanced Dynamic Method Identifier for Class Diagrams"""
import re
from typing import List, Union
from agentscope.agents import LlamaIndexAgent
from agentscope.message import Msg


class DynamicMethodIdentifier(LlamaIndexAgent):
    """支持知识检索的类方法变更识别智能体"""

    def __init__(
            self,
            name: str,
            model_config_name: str,
            sys_prompt: str,
            knowledge_id_list: List[str],
            recent_n_mem_for_retrieve: int = 3,
    ) -> None:
        sys_prompt = """## 最终方法列表生成规则
            你是一个专业的系统分析师，请根据变更需求和知识库中的最新类方法模型：
            1. 识别变更涉及的方法（新增/修改参数/重命名/删除）
            2. 生成变更后的完整方法列表（格式：类名.方法名(参数)）
            3. 方法签名需包含必要的参数类型
            4. 结果必须使用严格格式：```RESULT\n类名.方法1\n类名.方法2\n...```"""

        super().__init__(
            name=name,
            sys_prompt=sys_prompt,
            model_config_name=model_config_name,
            knowledge_id_list=knowledge_id_list,
            similarity_top_k=3,
            recent_n_mem_for_retrieve=recent_n_mem_for_retrieve,
        )

    def reply(self, x: Union[Msg, List[Msg]]) -> Msg:
        """处理输入并生成最终方法列表"""
        full_prompt = (
            f"{self.sys_prompt}\n\n"
            "请生成包含完整方法签名的最终方法列表："
        )
        return Msg(self.name, self.model(full_prompt).text, role="assistant")

    def get_final_methods(self, original_methods: List[str], change_request: str) -> List[str]:
        """对外接口：获取变更后方法列表"""
        combined_methods = list(set(original_methods))
        return self._extract_methods(
            self.reply(
                Msg("user",
                    f"参考以下方法生成最新列表:{str(combined_methods)}; 变更需求:{change_request}",
                    role="assistant")
            ).content
        )

    def _extract_methods(self, content: str) -> List[str]:
        """解析标准化响应并验证方法签名"""
        if match := re.search(r'```RESULT\n(.*?)\n```', content, re.DOTALL):
            valid_methods = []
            for item in match.group(1).split('\n'):
                item = item.strip()
                if not item:
                    continue
                # 验证格式：类名.方法名(参数类型)
                if re.match(r"^\w+\.\w+$([\w: ,]*)$$", item):
                    valid_methods.append(item)
            return list(set(valid_methods))
        return []