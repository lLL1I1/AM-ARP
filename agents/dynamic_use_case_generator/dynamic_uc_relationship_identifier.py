# File: agents/relationship_analyzer/dynamic_relation_identifier.py
"""RAG-enhanced Dynamic Relationship Identifier"""
import re
from typing import List, Dict, Union
from agentscope.agents import LlamaIndexAgent
from agentscope.message import Msg


class DynamicUCRelationshipIdentifier(LlamaIndexAgent):
    """智能关系变更分析器"""

    def __init__(
            self,
            name: str,
            model_config_name: str,
            sys_prompt: str,
            knowledge_id_list: List[str],
            recent_n_mem_for_retrieve: int = 5,
    ) -> None:
        sys_prompt = """## 关系变更规则
作为系统架构师，请分析以下要素：
1. 当前参与者: {actors}
2. 当前用例: {use_cases}
3. 变更需求: {change_request}
4. 基于业务规则分析关系变化

生成格式：
```RESULT
新增:
主体->客体
...
修改:
旧关系->新关系
...
删除:
主体->客体
...```"""

        super().__init__(
            name=name,
            sys_prompt=sys_prompt,
            model_config_name=model_config_name,
            knowledge_id_list=knowledge_id_list,
            similarity_top_k=5,
            recent_n_mem_for_retrieve=recent_n_mem_for_retrieve,
        )

    def get_final_relations(
            self,
            current_actors: List[str],
            current_cases: List[str],
            change_request: str,
            original_relations: List[str] = None
    ) -> Dict[str, List[str]]:
        """获取关系变更分析结果
        返回: {"新增": [], "修改": [], "删除": []}
        """
        context = (
            f"参与者：{', '.join(current_actors)}\n"
            f"用例：{', '.join(current_cases)}\n"
            f"变更需求：{change_request}"
        )
        response = self.reply(Msg("user", context, role="user"))
        return self._analyze_changes(response.content, original_relations or [])

    def reply(self, x: Union[Msg, List[Msg]]) -> Msg:
        """生成关系分析响应"""
        processed = self._format_response(super().reply(x).content)
        return Msg(self.name, processed, role="assistant")

    def _analyze_changes(
            self,
            response: str,
            original: List[str]
    ) -> Dict[str, List[str]]:
        """解析变更结果"""
        changes = {
            "新增": self._extract_section(response, "新增"),
            "修改": self._parse_modifications(response),
            "删除": self._extract_section(response, "删除")
        }

        # 验证删除项是否真实存在
        changes["删除"] = [r for r in changes["删除"] if r in original]
        return changes

    def _extract_section(self, text: str, section: str) -> List[str]:
        """提取指定区块的关系"""
        pattern = rf"{section}:\n((?:.+\n)*?)(?=\n\w+:|$)"
        if match := re.search(pattern, text, re.MULTILINE):
            return [line.strip() for line in match.group(1).split('\n') if line.strip()]
        return []

    def _parse_modifications(self, text: str) -> List[str]:
        """解析修改关系语法：旧关系->新关系"""
        mods = []
        pattern = r"修改:\n((?:.+\n)*?)(?=\n\w+:|$)"
        if match := re.search(pattern, text, re.MULTILINE):
            for line in match.group(1).split('\n'):
                if '->' in line and '=>' in line:
                    old, new = line.split('=>', 1)
                    mods.append(f"{old.strip()}->{new.strip()}")
        return mods

    def _format_response(self, raw: str) -> str:
        """响应格式标准化"""
        if "```RESULT" not in raw:
            return f"```RESULT\n{raw}\n```"
        return raw