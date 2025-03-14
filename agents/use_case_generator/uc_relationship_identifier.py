# File: agents/use_case_generator/uc_relationship_identifier.py
"""RAG-enhanced Relationship Identifier"""
import re
from typing import List, Union
from agentscope.agents import LlamaIndexAgent
from agentscope.message import Msg
import utils.util_function as uf

class UCRelationshipIdentifier(LlamaIndexAgent):
    """支持规则库检索的关系识别智能体"""

    def __init__(
            self,
            name: str,
            model_config_name: str,
            sys_prompt: str,
            knowledge_id_list: List[str],
            recent_n_mem_for_retrieve: int = 3,
    ) -> None:
        # 固化系统提示
        sys_prompt = sys_prompt = """## SYSTEM PROMPT
            You are a professional use case relationship identification assistant. Please strictly follow the requirements below:
            1. Identify association relationships between actors and use cases.
            2. Identify include/extend relationships between use cases.
            3. Output the type of relationships in the result!
            3. The result must be returned in the following format:
            ```RESULT
            Actor --association--> UseCase1  type:association
            UseCase1 --include--> UseCase2   type:include
            UseCase3 --extend--> UseCase4    type:extend
            ...
            ```"""

        super().__init__(
            name=name,
            sys_prompt=sys_prompt,
            model_config_name=model_config_name,
            knowledge_id_list=knowledge_id_list,
            similarity_top_k=3,
            recent_n_mem_for_retrieve=recent_n_mem_for_retrieve
        )

    def reply(self, x: Union[Msg, List[Msg]]) -> Msg:
        """覆盖父类方法，确保输入为字符串"""
        # 提取输入内容
        query = uf._extract_query(x)

        # 知识检索
        related_rules = uf._retrieve_knowledge(query, self.knowledge_list, self.similarity_top_k)

        # 构建完整提示
        full_prompt = (
            f"{self.sys_prompt}\n\n"
            f"[关联规则]\n{related_rules}\n\n"
            f"[分析对象]\n{query}\n\n"
            "请列出分析内容中所有用例模型中关系：The result must be returned in the following format:RESULTActor --association--> UseCase1  type:associationUseCase1 --include--> UseCase2   type:includeUseCase3 --extend--> UseCase4    type:extend"
        )

        # 调用模型生成
        response_text = self.model(full_prompt).text
        return Msg(self.name, response_text, role="assistant")

    def identify_relationships(
            self,
            use_cases: List[str],
            actors: List[str],
            background: str
    ) -> List[str]:
        """对外接口"""
        # 构造分析输入
        analysis_input = (
            f"背景：{background}\n"
            f"参与者：{', '.join(actors)}\n"
            f"用例：{', '.join(use_cases)}"
        )

        response = self.reply(Msg("user", analysis_input, role="assistant"))

        return self._extract_relationships(response.content)

    def _extract_relationships(self, content: str) -> List[str]:
        print('.....................所识别的用例关系：.............................');
        print(content)
        """解析响应内容"""
        # 严格模式匹配代码块
        if match := re.search(r'```RESULT\n(.*?)\n```', content, re.DOTALL):
            return [x.strip() for x in match.group(1).split('\n') if x.strip()]

        # 降级解析箭头语法
        return list(set(re.findall(r'.+?(?:-->|—).+', content)))