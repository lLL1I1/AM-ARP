# File: agents/sequence_modeling/dynamic_object_identifier.py
"""RAG-enhanced Dynamic Object Identifier for Sequence Diagrams"""
import re
from typing import List, Union
from agentscope.agents import LlamaIndexAgent
from agentscope.message import Msg


class DynamicObjectIdentifier(LlamaIndexAgent):
    """支持知识检索的顺序图对象变更识别智能体"""

    def __init__(
            self,
            name: str,
            model_config_name: str,
            sys_prompt: str,
            knowledge_id_list: List[str],
            recent_n_mem_for_retrieve: int = 3,
    ) -> None:
        sys_prompt = """## 最终对象列表生成规则
            你是一个专业的系统架构师，请根据变更需求和知识库中的最新顺序图模型：
            1. 识别变更涉及的对象（新增/重命名/删除）
            2. 生成变更后的完整对象列表（格式：对象名称:类型）
            3. 支持的对象类型：Actor、System、Database、Service、Component
            4. 结果必须使用严格格式：```RESULT\n对象1\n对象2\n...```"""

        super().__init__(
            name=name,
            sys_prompt=sys_prompt,
            model_config_name=model_config_name,
            knowledge_id_list=knowledge_id_list,
            similarity_top_k=3,
            recent_n_mem_for_retrieve=recent_n_mem_for_retrieve,
        )

    def reply(self, x: Union[Msg, List[Msg]]) -> Msg:
        """处理输入并生成最终对象列表"""
        full_prompt = (
            f"{self.sys_prompt}\n\n"
            "请生成包含类型标注的对象列表："
        )
        return Msg(self.name, self.model(full_prompt).text, role="assistant")

    def get_final_objects(self, original_objects: List[str], change_request: str) -> List[str]:
        """对外接口：获取变更后对象列表"""
        combined_objs = list(set(original_objects))
        return self._extract_objects(
            self.reply(
                Msg("user",
                    f"参考以下对象生成最新列表:{str(combined_objs)}; 变更需求:{change_request}",
                    role="assistant")
            ).content
        )

    def _extract_objects(self, content: str) -> List[str]:
        """解析标准化响应并验证对象格式"""
        if match := re.search(r'```RESULT\n(.*?)\n```', content, re.DOTALL):
            valid_objects = []
            for item in match.group(1).split('\n'):
                item = item.strip()
                if item and re.match(r"^\w+:(\w+)(\s*#\w+)?$", item):
                    valid_objects.append(item)
            return list(set(valid_objects))
        return []


# 使用示例
if __name__ == "__main__":
    obj_identifier = DynamicObjectIdentifier(
        name="对象识别器",
        model_config_name="gpt-4",
        knowledge_id_list=["seq_objects_knowledge"]
    )

    # 示例场景：支付系统升级
    original = ["User:Actor", "PaymentService:System"]
    change = "1. 新增风控服务组件 2. 拆分支付服务为AlipayService和WechatPayService"

    new_objects = obj_identifier.get_final_objects(original, change)
    # 可能输出：
    # ["User:Actor", "RiskControlService:Component",
    #  "AlipayService:System", "WechatPayService:System"]