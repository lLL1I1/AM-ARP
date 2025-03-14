# File: agents/message_identifier.py
"""消息识别智能体"""
import re
from typing import List, Union
from agentscope.agents import LlamaIndexAgent
from agentscope.message import Msg
import utils.util_function as uf


class MessageIdentifier(LlamaIndexAgent):
    """支持知识检索的消息识别智能体"""

    def __init__(
            self,
            name: str,
            model_config_name: str,
            knowledge_id_list: List[str],
            recent_n_mem_for_retrieve: int = 3,
    ) -> None:
        # 固化系统提示
        sys_prompt = """## 消息识别规则
            你是一个专业的系统架构师，请根据以下内容：
            1. 对象列表
            2. 知识库中的交互模式
            3. 用户输入场景
            结果必须使用格式：```RESULT\n对象A->对象B:消息\n...```"""

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
            f"[交互规则]\n{related_rules}\n\n"
            f"[分析场景]\n{query}\n\n"
            "请列出所有交互消息："
        )

        response_text = self.model(full_prompt).text
        return Msg(self.name, response_text, role="assistant")
    def identify_messages(self, objects: List[str], context: str) -> List[str]:
        """对外接口"""
        analysis_input = f"对象列表：{', '.join(objects)}\n场景：{context}"
        response = self.reply(Msg("user", analysis_input, role="assistant"))
        return self._parse_response(response.content)

    def _parse_response(self, content: str) -> List[str]:
        """解析响应内容"""
        print('.....................所识别的消息：.............................');
        print(content);
        if match := re.search(r'```RESULT\n(.*?)\n```', content, re.DOTALL):
            return [x.strip() for x in match.group(1).split('\n') if x.strip()]
        return list(set(re.findall(r'.+?->.+?:.+', content)))