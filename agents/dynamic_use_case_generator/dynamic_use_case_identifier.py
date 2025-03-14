# File: agents/use_case_generator/dynamic_use_case_identifier.py
"""RAG-enhanced Dynamic Use Case Identifier"""
import re
from typing import List, Union, Dict
from agentscope.agents import LlamaIndexAgent
from agentscope.message import Msg


class DynamicUseCaseIdentifier(LlamaIndexAgent):
    """支持知识检索的用例变更分析智能体"""

    def __init__(
            self,
            name: str,
            model_config_name: str,
            sys_prompt: str,
            knowledge_id_list: List[str],
            recent_n_mem_for_retrieve: int = 5,  # 扩大检索范围
    ) -> None:
        sys_prompt = """## 用例分析规则
作为资深业务分析师，请根据以下要素生成变更后的用例列表：
1. 当前参与者列表：{actors}
2. 变更需求描述：{change_request}
3. 知识库中的业务流程规则
4. 输出格式：```RESULT\n用例名称1\n用例名称2\n...```"""

        super().__init__(
            name=name,
            sys_prompt=sys_prompt,
            model_config_name=model_config_name,
            knowledge_id_list=knowledge_id_list,
            similarity_top_k=5,  # 扩大相似度检索范围
            recent_n_mem_for_retrieve=recent_n_mem_for_retrieve,
        )

    def reply(self, x: Union[Msg, List[Msg]]) -> Msg:
        """生成用例分析响应"""
        # 自动集成RAG检索结果
        return Msg(
            self.name,
            self._format_response(self.model(self._build_prompt(x)).text),
            role="assistant"
        )

    def get_final_use_cases(
            self,
            current_actors: List[str],
            change_request: str,
            original_use_cases: List[str] = None
    ) -> Dict[str, List[str]]:
        """对外接口：生成变更后用例列表
        返回格式：{"新增": [], "修改": [], "删除": []}
        """
        prompt = (
            f"当前参与者：{', '.join(current_actors)}\n"
            f"变更需求：{change_request}\n"
            f"原有用例：{original_use_cases or '无'}"
        )
        response = self.reply(Msg("user", prompt, role="assistant"))
        return self._analyze_changes(response.content, original_use_cases)

    def _build_prompt(self, msg: Union[Msg, List[Msg]]) -> str:
        """构建上下文增强提示"""
        # 自动集成RAG检索结果
        base_prompt = super().reply(msg).content

        # 添加结构化要求
        return f"{base_prompt}\n请按以下分类输出：新增/修改/删除用例"

    def _format_response(self, raw_text: str) -> str:
        """响应格式标准化"""
        if "```RESULT" not in raw_text:
            return f"```RESULT\n{raw_text}\n```"
        return raw_text

    def _analyze_changes(
            self,
            response: str,
            original_cases: List[str]
    ) -> Dict[str, List[str]]:
        """解析变更分析结果"""
        new_cases = self._extract_use_cases(response)

        # 变更类型分析
        result = {"新增": [], "修改": [], "删除": []}
        if original_cases:
            result["新增"] = [uc for uc in new_cases if uc not in original_cases]
            result["删除"] = [uc for uc in original_cases if uc not in new_cases]
        else:
            result["新增"] = new_cases
        return result

    def _extract_use_cases(self, content: str) -> List[str]:
        """从响应中提取用例名称"""
        if match := re.search(r'```RESULT\n(.*?)\n```', content, re.DOTALL):
            return list({
                self._clean_use_case_name(line.strip())
                for line in match.group(1).split('\n')
                if line.strip()
            })
        return []

    def _clean_use_case_name(self, name: str) -> str:
        """标准化用例名称"""
        # 移除特殊符号保留核心语义
        return re.sub(r'[【】$$$$()<>「」]', '', name).strip()