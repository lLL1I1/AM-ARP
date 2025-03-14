# File: agents/function_identifier.py
"""RAG-enhanced Function Identifier"""
import re
import json
from typing import Dict, List, Union
from agentscope.agents import LlamaIndexAgent
from agentscope.message import Msg
import utils.util_function as uf

class FunctionIdentifier(LlamaIndexAgent):
    """支持知识检索的方法识别智能体"""

    def __init__(
            self,
            name: str,
            model_config_name: str,
            sys_prompt: str,
            knowledge_id_list: List[str],
            recent_n_mem_for_retrieve: int = 3,
    ) -> None:
        sys_prompt = """## 方法识别规则
            你是一个专业的系统设计师，请根据：
            1. 类及其属性
            2. 知识库中的方法规范
            结果必须使用JSON格式：```RESULT\n{"类名":["方法1()","方法2()"]}```"""

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
            f"[方法规范]\n{related_rules}\n\n"
            f"[分析对象]\n{query}\n\n"
            "请列出所有类的方法："
        )

        response_text = self.model(full_prompt).text
        return Msg(self.name, response_text, role="assistant")
    def identify_functions(self, attributes: Dict[str, List[str]], context: str) -> Dict[str, List[str]]:
        """对外接口"""
        analysis_input = f"类属性：{json.dumps(attributes, ensure_ascii=False)}\n场景：{context}"
        response = self.reply(Msg("user", analysis_input, role="assistant"))
        return self._parse_response(response.content)

    def _parse_response(self, content: str) -> Dict[str, List[str]]:
        print('.....................所识别的功能：.............................');
        print(content);
        try:
            if match := re.search(r'```RESULT\n(.*?)\n```', content, re.DOTALL):
                return json.loads(match.group(1))
        except Exception:
            pass

        # 降级解析
        functions = {}
        current_class = None
        for line in content.split('\n'):
            if "方法" in line and "：" in line:
                current_class = line.split("：")[0].strip()
                functions[current_class] = []
            elif line.strip().startswith("- ") and "()" in line:
                functions[current_class].append(line.strip()[2:].split("(")[0] + "()")
        return functions