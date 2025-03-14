# File: agents/class_diagram_generator/dynamic_relation_identifier.py
"""RAG-enhanced Dynamic Relation Identifier for Class Diagrams"""
import re
from typing import List, Union
from agentscope.agents import LlamaIndexAgent
from agentscope.message import Msg


class DynamicRelationIdentifier(LlamaIndexAgent):
    """支持知识检索的类关系变更识别智能体"""

    RELATION_PATTERN = r"^\w+\s*(<|:)\s*\w+\s*(>|:)\s*\w+$"  # 支持 <继承> 和 :association> 两种格式

    def __init__(
            self,
            name: str,
            model_config_name: str,
            sys_prompt: str,
            knowledge_id_list: List[str],
            recent_n_mem_for_retrieve: int = 3,
    ) -> None:
        sys_prompt = """## 最终关系列表生成规则
            你是一个专业的系统架构师，请根据变更需求和知识库中的最新类关系模型：
            1. 识别变更涉及的类关系（新增/修改/删除）
            2. 生成变更后的完整关系列表（格式：类名1 <关系类型> 类名2）
            3. 支持的关系类型：继承(<:inheritance>)、组合(<:composition>)、聚合(<:aggregation>)、关联(<:association>)、依赖(<:dependency>)
            4. 结果必须使用严格格式：```RESULT\n关系1\n关系2\n...```"""

        super().__init__(
            name=name,
            sys_prompt=sys_prompt,
            model_config_name=model_config_name,
            knowledge_id_list=knowledge_id_list,
            similarity_top_k=3,
            recent_n_mem_for_retrieve=recent_n_mem_for_retrieve,
        )

    def reply(self, x: Union[Msg, List[Msg]]) -> Msg:
        """处理输入并生成最终关系列表"""
        full_prompt = (
            f"{self.sys_prompt}\n\n"
            "请生成标准化的类关系列表："
        )
        return Msg(self.name, self.model(full_prompt).text, role="assistant")

    def get_final_relations(self, original_relations: List[str], change_request: str) -> List[str]:
        """对外接口：获取变更后类关系列表"""
        combined_relations = list(set(original_relations))
        return self._extract_relations(
            self.reply(
                Msg("user",
                    f"参考以下关系生成最新列表:{str(combined_relations)}; 变更需求:{change_request}",
                    role="assistant")
            ).content
        )

    def _extract_relations(self, content: str) -> List[str]:
        """解析标准化响应并验证关系格式"""
        if match := re.search(r'```RESULT\n(.*?)\n```', content, re.DOTALL):
            valid_relations = []
            for item in match.group(1).split('\n'):
                item = self._normalize_relation(item.strip())
                if item and re.match(self.RELATION_PATTERN, item):
                    valid_relations.append(item)
            return list(set(valid_relations))
        return []

    def _normalize_relation(self, relation: str) -> str:
        """统一关系表示格式"""
        replacements = {
            "<继承>": "<:inheritance>",
            "<组合>": "<:composition>",
            "<聚合>": "<:aggregation>",
            "<关联>": "<:association>",
            "<依赖>": "<:dependency>"
        }
        for chi, eng in replacements.items():
            relation = relation.replace(chi, eng)
        return relation.replace(" ", "")  # 去除空格


# 使用示例
if __name__ == "__main__":
    relation_identifier = DynamicRelationIdentifier(
        name="关系识别器",
        model_config_name="gpt-4",
        knowledge_id_list=["class_relations_knowledge"]
    )

    # 示例场景：重构用户系统
    original = ["User <继承> Admin", "Order <关联> Product"]
    change = "1. 拆分Admin为SystemAdmin和ContentAdmin 2. 增加用户等级体系"

    new_relations = relation_identifier.get_final_relations(original, change)
    # 可能输出：
    # ["User<:inheritance>SystemAdmin", "User<:inheritance>ContentAdmin",
    #  "Order<:association>Product", "User<:association>UserLevel"]