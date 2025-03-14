# File: agents/relationship_identifier.py
"""RAG-enhanced Relationship Identifier"""
import json
import re
from typing import List, Union, Dict
from agentscope.agents import LlamaIndexAgent
from agentscope.message import Msg
import utils.util_function as uf


class ClassRelationshipIdentifier(LlamaIndexAgent):
    """支持知识检索的关系识别智能体"""

    def __init__(
            self,
            name: str,
            model_config_name: str,
            sys_prompt: str,
            knowledge_id_list: List[str],
            recent_n_mem_for_retrieve: int = 3,
    ) -> None:
        sys_prompt = """## 关系识别规则
            你是一个专业的架构师，请根据：
            1. 类及其方法
            2. 知识库中的关系模式
            结果必须使用格式：```RESULT\n类A--关系类型-->类B\n...```"""

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
        related_patterns = uf._retrieve_knowledge(query, self.knowledge_list, self.similarity_top_k)

        full_prompt = (
            f"{self.sys_prompt}\n\n"
            f"[关系模式]\n{related_patterns}\n\n"
            f"[分析对象]\n{query}\n\n"
            "请列出所有类关系："
        )

        response_text = self.model(full_prompt).text
        return Msg(self.name, response_text, role="assistant")

    def identify_relationships(self, functions: Dict[str, List[str]], context: str) -> List[str]:
        """对外接口"""
        analysis_input = f"类方法：{json.dumps(functions, ensure_ascii=False)}\n场景：{context}"
        response = self.reply(Msg("user", analysis_input, role="assistant"))
        return self._parse_response(response.content)

    def _parse_response(self, content: str) -> List[str]:
        print('.....................所识别的类的关系：.............................');
        print(content);
        if match := re.search(r'```RESULT\n(.*?)\n```', content, re.DOTALL):
            return [x.strip() for x in match.group(1).split('\n') if x.strip()]
        return list(set(re.findall(r'.+?--.+?-->.*', content)))  # 匹配箭头语法