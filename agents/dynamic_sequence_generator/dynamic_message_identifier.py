# File: agents/sequence_modeling/dynamic_message_identifier.py
"""RAG-enhanced Dynamic Message Identifier for Sequence Diagrams"""
import re
from typing import List, Union
from agentscope.agents import LlamaIndexAgent
from agentscope.message import Msg


class DynamicMessageIdentifier(LlamaIndexAgent):

    MESSAGE_PATTERN = r"^\w+\s*->\s*\w+\s*:\s*.+$"  

    def __init__(
            self,
            name: str,
            sys_prompt: str,
            model_config_name: str,
            knowledge_id_list: List[str],
            recent_n_mem_for_retrieve: int = 3,
    ) -> None:
        sys_prompt = """## Final message list generation rule
            You are a professional system architect, based on the change requirements and the latest sequence diagram model in the knowledge base:
            1. Identify the message flow involved in the change (new/modified/deleted)
            2. Generate the complete message list after the change (format: send object -> Receive object: message content)
            3. Supported message types: synchronous call, asynchronous message, return message
            4. Results must be in a strict format:```RESULT\nmessage1\nmessage2\n...```"""

        super().__init__(
            name=name,
            sys_prompt=sys_prompt,
            model_config_name=model_config_name,
            knowledge_id_list=knowledge_id_list,
            similarity_top_k=3,
            recent_n_mem_for_retrieve=recent_n_mem_for_retrieve,
        )

    def reply(self, x: Union[Msg, List[Msg]]) -> Msg:
        full_prompt = (
            f"{self.sys_prompt}\n\n"
            "Generate a UML-compliant message flow list:"
        )
        return Msg(self.name, self.model(full_prompt).text, role="assistant")

    def get_final_messages(self, original_messages: List[str], change_request: str) -> List[str]:

        combined_msgs = list(set(original_messages))
        return self._extract_messages(
            self.reply(
                Msg("user",
                    f"Refer to the following message flow to generate the latest list:{str(combined_msgs)}; change requirement:{change_request}",
                    role="assistant")
            ).content
        )

    def _extract_messages(self, content: str) -> List[str]:
        if match := re.search(r'```RESULT\n(.*?)\n```', content, re.DOTALL):
            valid_messages = []
            for item in match.group(1).split('\n'):
                item = item.strip()
                if item and re.match(self.MESSAGE_PATTERN, item):
                    valid_messages.append(self._normalize_message(item))
            return list(set(valid_messages))
        return []

    def _normalize_message(self, message: str) -> str:
        return re.sub(r'\s*->\s*', '->', message).replace(' : ', ': ')



if __name__ == "__main__":
    msg_identifier = DynamicMessageIdentifier(
        name="message identifier",
        model_config_name="gpt-4",
        knowledge_id_list=["seq_messages_knowledge"]
    )


    original = [
        "User->PaymentService: Submit a payment request",
        "PaymentService->BankGateway: initiate and issue payments"
    ]
    change = "1. Adding payment result verification Step 2. Add a payment timeout retry mechanism"

    new_messages = msg_identifier.get_final_messages(original, change)
    """
    possible output:
    [
        "User->PaymentService: Submit a payment request ",
        "PaymentService->BankGateway: Initiate payment ",
        "BankGateway-->PaymentService: Payment result ",
        "PaymentService->PaymentService: retry verification ",
        "PaymentService-->User: Payment result notification"
    ]
    """