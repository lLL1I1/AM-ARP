import glob
import os
import re
from datetime import datetime
from typing import List, Dict, Union

import agentscope
from agentscope.agents import LlamaIndexAgent
from agentscope.message import Msg
from agentscope.rag import KnowledgeBank

import utils.util_function as uf


class DemandDecomposer(LlamaIndexAgent):
    """需求分解智能体"""

    def __init__(
            self,
            name: str,
            model_config_name: str,
            sys_prompt: str,
            knowledge_id_list: List[str],
            recent_n_mem_for_retrieve: int = 3,
    ) -> None:
        sys_prompt = """ Requirement Decomposition Rules
            You are a professional requirement analyst. Please decompose user input and knowledge base rules as follows:
            1. Decompose requirements into functional and non-functional requirements.
            2. Each requirement must include the following fields: request number, original requirement, request type, sub-requirements/constraints, source, priority, related system components, remarks.
            3. You should determine the priority based on actual analysis, with more necessary functions appearing earlier in the list.
            4. Categorize these software requirements into: functional requirements and non-functional requirements, and fill them into the corresponding fields.
            5. The result must be formatted as follows:
        ```RESULT\n[Request Number]: [Request Content]\n[Request Category]: [Category Result]\n\n[Field Name]: [Field Value]\n...```
        """
        super().__init__(
            name=name,
            sys_prompt=sys_prompt,
            model_config_name=model_config_name,
            knowledge_id_list=knowledge_id_list,
            similarity_top_k=3,
            recent_n_mem_for_retrieve=recent_n_mem_for_retrieve,
        )

    def reply(self, x: Union[Msg, List[Msg]]) -> Msg:
        query = uf._extract_query(x)
        related_knowledge = uf._retrieve_knowledge(query, self.knowledge_list, self.similarity_top_k)
        full_prompt = (
            f"{self.sys_prompt}\n\n"
            f"[Knowledge base content:]\n{related_knowledge}\n\n"
            f"[User input:]\n{query}\n\n"
            "Break down the requirements according to the rules:"
        )
        response_text = self.model(full_prompt).text
        return Msg(self.name, response_text, role="assistant")

    def decompose_demands(self, raw_demand: str) -> List[Dict]:
        response = self.reply(Msg("user", raw_demand, role="user"))
        return self._parse_response(response.content)

    def _parse_response(self, content: str) -> List[Dict]:
        demands = []
        entries = re.split(r'\n(?=\d+\. )', content.strip())

        for entry in entries:
            demand = {}
            lines = [line.strip() for line in entry.split('\n') if line.strip()]

            for line in lines:
                clean_line = re.sub(r'^\d+\.\s*', '', line)
                if ':' in clean_line:
                    key, value = map(str.strip, clean_line.split(':', 1))
                    if key == "Sub-Requirements/Constraints":
                        value = [v.strip() for v in value.split('- ') if v]
                    demand[key] = value

            if demand:
                demands.append(demand)
        return demands

    def save_to_md(self, demands: List[Dict], output_dir: str) -> None:
        file_path = os.path.join(output_dir, "demands.md")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("# Requirement breakdown list\n\n")
            for idx, demand in enumerate(demands, 1):
                f.write(f"## Requirement {idx}\n")
                for key, value in demand.items():
                    if isinstance(value, list):
                        value = "\n  - ".join([""] + value)
                    f.write(f"- {key}: {value}\n")
                f.write("\n")

    def save_to_doc(self, demands: List[Dict], output_dir: str) -> None:
        file_path = os.path.join(output_dir, "demands.doc")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("Requirement breakdown list\n\n")
            for idx, demand in enumerate(demands, 1):
                f.write(f"Requirement {idx}\n")
                for key, value in demand.items():
                    if isinstance(value, list):
                        value = ", ".join(value)
                    f.write(f"{key}: {value}\n")
                f.write("\n")


def get_next_version_num(target_dir: str, date_str: str) -> int:
    pattern = os.path.join(target_dir, f"class-{date_str}-*")
    existing_dirs = glob.glob(pattern)

    max_num = 0
    for dir_path in existing_dirs:
        dir_name = os.path.basename(dir_path)
        if match := re.match(rf"class-{date_str}-(\d+)", dir_name):
            current_num = int(match.group(1))
            max_num = max(max_num, current_num)
    return max_num + 1


def main():
    agents = agentscope.init(
        model_configs="G:\\PycharmProjects\\UMLGenerator\\configs\\model_configs.json",
        agent_configs="G:\\PycharmProjects\\UMLGenerator\\configs\\decomposer_agent.json"
    )

    knowledge_bank = KnowledgeBank(configs="../configs/rest_knowledge_config.json")
    knowledge_bank.equip(agents[0], ["classificaiton_rules"])
    decomposer = agents[0]

    input_path = "../data/case.docx"
    test_demand = uf.read_docx(input_path)

    output_base = "./output"
    today = datetime.now().strftime("%Y-%m-%d")
    version_num = get_next_version_num(output_base, today)
    version_dir = os.path.join(output_base, f"class-{today}-{version_num}")
    os.makedirs(version_dir, exist_ok=True)

    demands = decomposer.decompose_demands(test_demand)

    decomposer.save_to_md(demands, version_dir)
    decomposer.save_to_doc(demands, version_dir)

    print("Decomposed requirements:")
    for idx, demand in enumerate(demands, 1):
        print(f"Requirement {idx}:")
        for key, value in demand.items():
            print(f"  {key}: {value}")
        print()
    print(f"The file was saved to: {os.path.abspath(version_dir)}")


if __name__ == "__main__":
    main()