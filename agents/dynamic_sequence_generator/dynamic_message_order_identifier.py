# File: agents/sequence_modeling/dynamic_message_order_identifier.py
"""RAG-enhanced Dynamic Message Order Identifier for Sequence Diagrams"""
import re
from typing import List, Union
from agentscope.agents import LlamaIndexAgent
from agentscope.message import Msg


class DynamicMessageOrderIdentifier(LlamaIndexAgent):
    """支持知识检索的消息顺序变更识别智能体"""

    MESSAGE_ORDER_PATTERN = r"^(?:\s*(?:alt|loop|opt)\s+.+?\|?\s*)?\w+\s*->\s*\w+\s*:.*$"

    def __init__(
            self,
            name: str,
            sys_prompt: str,
            model_config_name: str,
            knowledge_id_list: List[str],
            recent_n_mem_for_retrieve: int = 3,
    ) -> None:
        sys_prompt = """## 消息顺序调整规则
            你是一个专业的系统架构师，请根据变更需求和知识库中的流程逻辑：
            1. 识别消息顺序需要调整的位置（前置/后置/并行）
            2. 生成符合业务逻辑的新消息顺序（保持原有消息内容）
            3. 支持顺序调整类型：
               - 插入新步骤
               - 调整步骤顺序
               - 添加条件分支（使用alt/else）
               - 创建循环结构（loop）
            4. 结果必须使用严格格式：```RESULT\n消息流\n...```"""

        super().__init__(
            name=name,
            sys_prompt=sys_prompt,
            model_config_name=model_config_name,
            knowledge_id_list=knowledge_id_list,
            similarity_top_k=3,
            recent_n_mem_for_retrieve=recent_n_mem_for_retrieve,
        )

    def reply(self, x: Union[Msg, List[Msg]]) -> Msg:
        """处理输入并生成顺序调整方案"""
        full_prompt = (
            f"{self.sys_prompt}\n\n"
            "请生成符合UML规范的消息顺序列表："
        )
        return Msg(self.name, self.model(full_prompt).text, role="assistant")

    def get_final_message_order(self, original_messages: List[str], change_request: str) -> List[str]:
        """对外接口：获取调整后的消息顺序"""
        return self._extract_message_order(
            self.reply(
                Msg("user",
                    f"当前消息顺序：\n{chr(10).join(original_messages)}\n变更需求：{change_request}",
                    role="assistant")
            ).content
        )

    def _extract_message_order(self, content: str) -> List[str]:
        """解析带结构化控制的消息顺序"""
        if match := re.search(r'```RESULT\n(.*?)\n```', content, re.DOTALL):
            processed = []
            indent_level = 0
            for line in match.group(1).split('\n'):
                line = line.rstrip()
                if not line:
                    continue

                # 处理结构化控制标签
                if re.match(r"^\s*(alt|loop|opt)\s+", line):
                    processed.append(line)
                    indent_level += 2
                elif re.match(r"^\s*else\s*", line):
                    processed.append(line)
                elif re.match(r"^\s*end\s*", line):
                    indent_level = max(0, indent_level - 2)
                    processed.append(line)
                else:
                    processed.append((" " * indent_level) + line)
            return processed
        return []

    def validate_message_flow(self, messages: List[str]) -> bool:
        """验证消息顺序的合理性"""
        stack = []
        for idx, line in enumerate(messages):
            if re.match(r"^\s*alt\s+", line):
                stack.append(("alt", idx))
            elif re.match(r"^\s*loop\s+", line):
                stack.append(("loop", idx))
            elif re.match(r"^\s*opt\s+", line):
                stack.append(("opt", idx))
            elif "end" in line:
                if not stack:
                    raise ValueError(f"第{idx + 1}行出现多余的end标签")
                stack.pop()
        return len(stack) == 0


# 使用示例
if __name__ == "__main__":
    order_identifier = DynamicMessageOrderIdentifier(
        name="消息顺序识别器",
        model_config_name="gpt-4",
        knowledge_id_list=["seq_flow_knowledge"]
    )

    # 示例场景：支付流程优化
    original = [
        "User->PaymentService: 提交支付请求",
        "PaymentService->BankGateway: 发起支付",
        "BankGateway-->PaymentService: 返回结果",
        "PaymentService-->User: 通知结果"
    ]
    change = "在银行网关返回失败时添加重试机制"

    new_order = order_identifier.get_final_message_order(original, change)
    """
    可能输出：
    [
        "User->PaymentService: 提交支付请求",
        "alt 支付成功",
        "  PaymentService->BankGateway: 发起支付",
        "  BankGateway-->PaymentService: 返回成功",
        "else 支付失败",
        "  loop 3次重试",
        "    PaymentService->BankGateway: 发起支付",
        "    alt 重试成功",
        "      BankGateway-->PaymentService: 返回成功",
        "      break",
        "    else 继续重试",
        "      BankGateway-->PaymentService: 返回失败",
        "  end",
        "end",
        "PaymentService-->User: 通知结果"
    ]
    """

    # 验证流程合理性
    try:
        if order_identifier.validate_message_flow(new_order):
            print("消息顺序验证通过")
    except ValueError as e:
        print(f"流程错误: {str(e)}")