# File: agents/message_order_identifier.py
"""消息顺序识别智能体"""
import re
from typing import List, Union
from agentscope.agents import LlamaIndexAgent
from agentscope.message import Msg
import utils.util_function as uf


class MessageOrderIdentifier(LlamaIndexAgent):
    """支持知识检索的时序识别智能体"""

    def __init__(
            self,
            name: str,
            model_config_name: str,
            knowledge_id_list: List[str],
            recent_n_mem_for_retrieve: int = 3,
    ) -> None:
        # 固化系统提示
        sys_prompt = """## 消息顺序识别规则
            你是一个专业的流程分析师，请根据：
            1. 消息列表
            2. 知识库中的流程规范
            3. 用户输入场景
            结果必须使用格式：```RESULT\n1. 消息1\n2. 消息2\n...```"""

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
        query = uf._extract_query(x)
        related_rules = uf._retrieve_knowledge(query, self.knowledge_list, self.similarity_top_k)

        full_prompt = (
            f"{self.sys_prompt}\n\n"
            f"[流程规范]\n{related_rules}\n\n"
            f"[分析场景]\n{query}\n\n"
            "请确定消息执行顺序："
        )

        response_text = self.model(full_prompt).text
        return Msg(self.name, response_text, role="assistant")

    def identify_sequence(self, messages: List[str], context: str) -> List[str]:
        """对外接口"""
        analysis_input = f"message list：\n" + "\n".join(messages) + f"\n context：{context}"
        response = self.reply(Msg("user", analysis_input, role="assistant"))

        return self._parse_response(response.content)

    def _parse_response(self, content: str) -> List[str]:
        """解析响应内容"""
        print('.....................所识别的消息顺序：.............................');
        print(content);
        if match := re.search(r'```RESULT\n(.*?)\n```', content, re.DOTALL):
            return [x.strip() for x in match.group(1).split('\n') if x.strip()]
        return list(set(re.findall(r'\d+\.\s*.+', content)))