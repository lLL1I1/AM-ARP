# File: agents/sequence_modeling/dynamic_message_identifier.py
"""RAG-enhanced Dynamic Message Identifier for Sequence Diagrams"""
import re
from typing import List, Union
from agentscope.agents import LlamaIndexAgent
from agentscope.message import Msg


class DynamicMessageIdentifier(LlamaIndexAgent):
    """支持知识检索的顺序图消息变更识别智能体"""

    MESSAGE_PATTERN = r"^\w+\s*->\s*\w+\s*:\s*.+$"  # 匹配消息格式：Sender->Receiver: Message

    def __init__(
            self,
            name: str,
            sys_prompt: str,
            model_config_name: str,
            knowledge_id_list: List[str],
            recent_n_mem_for_retrieve: int = 3,
    ) -> None:
        sys_prompt = """## 最终消息列表生成规则
            你是一个专业的系统架构师，请根据变更需求和知识库中的最新顺序图模型：
            1. 识别变更涉及的消息流（新增/修改/删除）
            2. 生成变更后的完整消息列表（格式：发送对象->接收对象: 消息内容）
            3. 支持的消息类型：同步调用、异步消息、返回消息
            4. 结果必须使用严格格式：```RESULT\n消息1\n消息2\n...```"""

        super().__init__(
            name=name,
            sys_prompt=sys_prompt,
            model_config_name=model_config_name,
            knowledge_id_list=knowledge_id_list,
            similarity_top_k=3,
            recent_n_mem_for_retrieve=recent_n_mem_for_retrieve,
        )

    def reply(self, x: Union[Msg, List[Msg]]) -> Msg:
        """处理输入并生成最终消息列表"""
        full_prompt = (
            f"{self.sys_prompt}\n\n"
            "请生成符合UML规范的消息流列表："
        )
        return Msg(self.name, self.model(full_prompt).text, role="assistant")

    def get_final_messages(self, original_messages: List[str], change_request: str) -> List[str]:
        """对外接口：获取变更后消息列表"""
        combined_msgs = list(set(original_messages))
        return self._extract_messages(
            self.reply(
                Msg("user",
                    f"参考以下消息流生成最新列表:{str(combined_msgs)}; 变更需求:{change_request}",
                    role="assistant")
            ).content
        )

    def _extract_messages(self, content: str) -> List[str]:
        """解析标准化响应并验证消息格式"""
        if match := re.search(r'```RESULT\n(.*?)\n```', content, re.DOTALL):
            valid_messages = []
            for item in match.group(1).split('\n'):
                item = item.strip()
                if item and re.match(self.MESSAGE_PATTERN, item):
                    valid_messages.append(self._normalize_message(item))
            return list(set(valid_messages))
        return []

    def _normalize_message(self, message: str) -> str:
        """统一消息格式（去除多余空格）"""
        return re.sub(r'\s*->\s*', '->', message).replace(' : ', ': ')


# 使用示例
if __name__ == "__main__":
    msg_identifier = DynamicMessageIdentifier(
        name="消息识别器",
        model_config_name="gpt-4",
        knowledge_id_list=["seq_messages_knowledge"]
    )

    # 示例场景：支付流程优化
    original = [
        "User->PaymentService: 提交支付请求",
        "PaymentService->BankGateway: 发起支付"
    ]
    change = "1. 增加支付结果校验步骤 2. 添加支付超时重试机制"

    new_messages = msg_identifier.get_final_messages(original, change)
    """
    可能输出：
    [
        "User->PaymentService: 提交支付请求",
        "PaymentService->BankGateway: 发起支付",
        "BankGateway-->PaymentService: 支付结果",
        "PaymentService->PaymentService: 重试校验",
        "PaymentService-->User: 支付结果通知"
    ]
    """