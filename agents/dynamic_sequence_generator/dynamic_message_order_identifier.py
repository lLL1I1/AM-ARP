# File: agents/sequence_modeling/dynamic_message_order_identifier.py
"""RAG-enhanced Dynamic Message Order Identifier for Sequence Diagrams"""
import re
from typing import List, Union
from agentscope.agents import LlamaIndexAgent
from agentscope.message import Msg


class DynamicMessageOrderIdentifier(LlamaIndexAgent):
    """Agent supporting knowledge retrieval for message order changes identification"""

    MESSAGE_ORDER_PATTERN = r"^(?:\s*(?:alt|loop|opt)\s+.+?\|?\s*)?\w+\s*->\s*\w+\s*:.*$"

    def __init__(
            self,
            name: str,
            sys_prompt: str,
            model_config_name: str,
            knowledge_id_list: List[str],
            recent_n_mem_for_retrieve: int = 3,
    ) -> None:
        sys_prompt = """## Message Order Adjustment Rules
            You are a professional system architect. Please adjust the message order based on change requests and the logical flow in the knowledge base:
            1. Identify positions where message order needs adjustment (before/after/in parallel)
            2. Generate new message order complying with business logic (keep original message content)
            3. Support types of order adjustments:
               - Insert new steps
               - Adjust step order
               - Add conditional branches (use alt/else)
               - Create loop structures (loop)
            4. The result must use strict format: ```RESULT\nmessage flow\n...```"""

        super().__init__(
            name=name,
            sys_prompt=sys_prompt,
            model_config_name=model_config_name,
            knowledge_id_list=knowledge_id_list,
            similarity_top_k=3,
            recent_n_mem_for_retrieve=recent_n_mem_for_retrieve,
        )

    def reply(self, x: Union[Msg, List[Msg]]) -> Msg:
        """Process input and generate an adjustment plan"""
        full_prompt = (
            f"{self.sys_prompt}\n\n"
            "Please generate a message order list that complies with UML standards:"
        )
        return Msg(self.name, self.model(full_prompt).text, role="assistant")

    def get_final_message_order(self, original_messages: List[str], change_request: str) -> List[str]:
        """Public interface: Get adjusted message order"""
        return self._extract_message_order(
            self.reply(
                Msg("user",
                    f"Current message order:\n{chr(10).join(original_messages)}\nChange request:{change_request}",
                    role="assistant")
            ).content
        )

    def _extract_message_order(self, content: str) -> List[str]:
        """Parse structured control messages order"""
        if match := re.search(r'```RESULT\n(.*?)\n```', content, re.DOTALL):
            processed = []
            indent_level = 0
            for line in match.group(1).split('\n'):
                line = line.rstrip()
                if not line:
                    continue

                # Handle structured control tags
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
        """Validate the rationality of the message order"""
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
                    raise ValueError(f"Extra end tag at line {idx + 1}")
                stack.pop()
        return len(stack) == 0


# Example usage
if __name__ == "__main__":
    order_identifier = DynamicMessageOrderIdentifier(
        name="Message Order Identifier",
        model_config_name="gpt-4",
        knowledge_id_list=["seq_flow_knowledge"]
    )

    # Example scenario: Payment process optimization
    original = [
        "User->PaymentService: Submit payment request",
        "PaymentService->BankGateway: Initiate payment",
        "BankGateway-->PaymentService: Return result",
        "PaymentService-->User: Notify result"
    ]
    change = "Add retry mechanism when Bank Gateway returns failure"

    new_order = order_identifier.get_final_message_order(original, change)
    """
    Possible output:
    [
        "User->PaymentService: Submit payment request",
        "alt Payment success",
        "  PaymentService->BankGateway: Initiate payment",
        "  BankGateway-->PaymentService: Return success",
        "else Payment failure",
        "  loop Retry 3 times",
        "    PaymentService->BankGateway: Initiate payment",
        "    alt Retry success",
        "      BankGateway-->PaymentService: Return success",
        "      break",
        "    else Continue retry",
        "      BankGateway-->PaymentService: Return failure",
        "  end",
        "end",
        "PaymentService-->User: Notify result"
    ]
    """

    # Validate process rationality
    try:
        if order_identifier.validate_message_flow(new_order):
            print("Message order validation passed")
    except ValueError as e:
        print(f"Process error: {str(e)}")
    ``` 

This version keeps the structure and functionality of the original code but replaces all the Chinese comments and strings with their English equivalents.