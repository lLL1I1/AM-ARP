# File: agents/use_case_generator/updated_actor_lister.py
"""RAG-enhanced Updated Actor Lister"""
import re
from typing import List, Union
from agentscope.agents import LlamaIndexAgent
from agentscope.message import Msg


class DynamicActorIdentifier(LlamaIndexAgent):
    """支持知识检索的变更后参与者列表生成智能体"""

    def __init__(
            self,
            name: str,
            model_config_name: str,
            sys_prompt: str,
            knowledge_id_list: List[str],
            recent_n_mem_for_retrieve: int = 3,
    ) -> None:
        sys_prompt = """## 最终参与者列表生成规则
            你是一个专业的需求分析师，请根据变更需求和知识库中的最新参与者模型：
            1. 生成变更后的完整参与者列表
            2. 结果必须使用严格格式：```RESULT\n参与者1\n参与者2\n...```"""

        super().__init__(
            name=name,
            sys_prompt=sys_prompt,
            model_config_name=model_config_name,
            knowledge_id_list=knowledge_id_list,
            similarity_top_k=3,
            recent_n_mem_for_retrieve=recent_n_mem_for_retrieve,
        )

    def reply(self, x: Union[Msg, List[Msg]]) -> Msg:
        """处理输入并生成最终参与者列表"""
        # 构建提示模板

        full_prompt = (
            f"{self.sys_prompt}\n\n"
            "请生成格式规范的最终参与者列表："
        )

        # 调用模型生成响应
        return Msg(self.name, self.model(full_prompt).text, role="assistant")

    def get_final_actors(self, original_actors: List[str], change_request: str) -> List[str]:
        """对外接口：获取变更后参与者列表"""
        # 合并知识库与输入参数中的参与者
        combined_actors = list(set(original_actors))
        return self._extract_actors(self.reply(Msg("user", "参考以下内容生成最新的参与者列表:" + str(combined_actors) + ";变更需求:" + change_request, role="assistant")).content)

    def _extract_actors(self, content: str) -> List[str]:
        """解析标准化响应"""
        if match := re.search(r'```RESULT\n(.*?)\n```', content, re.DOTALL):
            return list({x.strip() for x in match.group(1).split('\n') if x.strip()})
        return []