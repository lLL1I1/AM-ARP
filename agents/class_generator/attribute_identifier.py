# File: agents/attribute_identifier.py
"""RAG-enhanced Attribute Identifier"""
import re
import json
from typing import Dict, List, Union
from agentscope.agents import LlamaIndexAgent
from agentscope.message import Msg


class AttributeIdentifier(LlamaIndexAgent):
    """支持知识检索的属性识别智能体"""

    def __init__(
            self,
            name: str,
            model_config_name: str,
            sys_prompt: str,
            knowledge_id_list: List[str],
            recent_n_mem_for_retrieve: int = 3,
    ) -> None:
        sys_prompt = """## 属性识别规则
            你是一个专业的系统设计师，请根据：
            1. 已识别的类列表
            2. 知识库中的属性规范
            结果必须使用JSON格式：```RESULT\n{"类名":["属性1","属性2"]}```"""

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
        query = self._extract_query(x)
        related_rules = self._retrieve_knowledge(query)

        full_prompt = (
            f"{self.sys_prompt}\n\n"
            f"[属性规范]\n{related_rules}\n\n"
            f"[分析对象]\n{query}\n\n"
            "请列出所有类的属性："
        )

        response_text = self.model(full_prompt).text
        return Msg(self.name, response_text, role="assistant")

    def _extract_query(self, x: Union[Msg, List[Msg]]) -> str:
        if isinstance(x, Msg):
            return x.content
        elif isinstance(x, list) and len(x) > 0:
            return x[-1].content
        return ""

    def _retrieve_knowledge(self, query: str) -> str:
        knowledge_str = ""
        for knowledge in self.knowledge_list:
            nodes = knowledge.retrieve(query, self.similarity_top_k)
            for node in nodes:
                knowledge_str += f"属性规范：{node.text}\n来源：{node.node.metadata}\n\n"
        return knowledge_str.strip()

    def identify_attributes(self, classes: List[str], context: str) -> Dict[str, List[str]]:
        """对外接口"""

        analysis_input = f"类列表：{', '.join(classes)}\n场景：{context}"
        response = self.reply(Msg("user", analysis_input, role="assistant"))
        return self._parse_response(response.content)

    def _parse_response(self, content: str) -> Dict[str, List[str]]:
        print('.....................所识别的类的属性：.............................');
        print(content);
        try:
            if match := re.search(r'```RESULT\n(.*?)\n```', content, re.DOTALL):
                return json.loads(match.group(1))
        except Exception:
            pass

        # 降级解析
        attributes = {}
        current_class = None
        for line in content.split('\n'):
            if "属性" in line and "：" in line:
                current_class = line.split("：")[0].strip()
                attributes[current_class] = []
            elif line.strip().startswith("- "):
                attributes[current_class].append(line.strip()[2:].split(":")[0])
        return attributes