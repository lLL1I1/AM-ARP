# File: workflows/use_case_modeling.py
import json
import os
import glob
import re
from datetime import datetime
from typing import Tuple, List

import agentscope
from agentscope.rag import KnowledgeBank
from agentscope.msghub import msghub
from agentscope.message import Msg
from docx import Document  # 导入 python-docx 库
import utils.util_function as uf

def run_use_case_workflow(
        background: str,
        knowledge_config: str = "../configs/uc_knowledge.json"
) -> Tuple[List[str], List[str], List[str]]:
    """知识增强的用例建模工作流"""

    # 初始化智能体
    agents = agentscope.init(
        model_configs="G:\\PycharmProjects\\UMLGenerator\\configs\\model_configs.json",
        agent_configs="G:\\PycharmProjects\\UMLGenerator\\configs\\usecase_agent_configs.json"
    )

    # 初始化知识库
    knowledge_bank = KnowledgeBank(configs=knowledge_config)

    # 装备知识库
    knowledge_bank.equip(agents[0], ["actor_rules"])
    knowledge_bank.equip(agents[1], ["uc_rules"])
    knowledge_bank.equip(agents[2], ["uc_rel_rules"])

    # 执行协作流程
    with msghub(agents) as hub:
        hub.broadcast(Msg("Host", "启动用例建模流程", role="system"))
        hub.broadcast(Msg("Host", f"输入背景：{background}", role="user"))

        # 参与者识别
        actors = agents[0].identify_actors(background)
        hub.broadcast(Msg("ActorAgent", json.dumps(actors, ensure_ascii=False), role="assistant"))

        # 用例识别
        use_cases = agents[1].identify_use_cases(background)
        hub.broadcast(Msg("UseCaseAgent", json.dumps(use_cases, ensure_ascii=False), role="assistant"))

        # 关系识别
        relationships = agents[2].identify_relationships(
            use_cases,
            actors,
            background
        )
        hub.broadcast(Msg("RelAgent", json.dumps(relationships, ensure_ascii=False), role="assistant"))

    # 结构化保存结果
    version_dir = _save_structured_results(
        background=background,
        actors=actors,
        use_cases=use_cases,
        relationships=relationships
    )

    print(f"\n生成结果已版本化保存至目录: {version_dir}")

    return actors, use_cases, relationships


def _save_structured_results(
        background: str,
        actors: List[str],
        use_cases: List[str],
        relationships: List[str],
        output_base: str = "versions"
) -> str:
    """结构化保存用例模型结果到版本化的Markdown文件"""
    # 创建基础目录
    os.makedirs(output_base, exist_ok=True)

    # 生成版本号（日期-序号）
    today = datetime.now().strftime("%Y-%m-%d")
    existing_versions = glob.glob(os.path.join(output_base, f"{today}-*"))
    version_num = len(existing_versions) + 1
    version_id = f"{today}-{version_num}"
    version_dir = os.path.join(output_base, version_id)
    os.makedirs(version_dir, exist_ok=True)

    # 保存原始需求背景
    with open(os.path.join(version_dir, "requirements.md"), 'w', encoding='utf-8') as f:
        f.write(f"# 原始需求\n\n{background}\n")

    # 结构化保存参与者
    with open(os.path.join(version_dir, "actors.md"), 'w', encoding='utf-8') as f:
        f.write("# 参与者列表\n\n")
        for idx, actor in enumerate(actors, 1):
            f.write(f"## 参与者 {idx}\n")
            f.write(f"- 名称: {actor}\n")
            f.write(f"- 类型: 业务角色\n")
            f.write(f"- 关联需求: {background}\n\n")

    # 结构化保存用例
    with open(os.path.join(version_dir, "use_cases.md"), 'w', encoding='utf-8') as f:
        f.write("# 用例列表\n\n")
        for idx, uc in enumerate(use_cases, 1):
            f.write(f"## 用例 {idx}\n")
            f.write(f"- 名称: {uc}\n")
            f.write("- 类型: 系统功能\n")
            f.write(f"- 关联需求: {background}\n\n")

    # 结构化保存关系
    with open(os.path.join(version_dir, "relationships.md"), 'w', encoding='utf-8') as f:
        f.write("# 关系矩阵\n\n")
        f.write("| 主体 | 关系类型 | 客体 | 关联需求 |\n")
        f.write("|------|---------|------|----------|\n")
        for rel in relationships:
            # 解析关系表达式（示例格式：用户 -> 浏览商品）
            parts = re.split(r"\s*->\s*|\s*-->\s*", rel)
            if len(parts) == 2:
                subject, obj = parts
                f.write(f"| {subject} | 关联 | {obj} | {background} |\n")
            else:
                f.write(f"| {rel} | 关联 | 系统 | {background} |\n")

    return version_dir


if __name__ == "__main__":
    file_path = "../data/case.docx"

    # output_base = "./agents/output"
    # latest_version_dir = uf.get_latest_version_dir()
    # # print(latest_version_dir)
    #
    # if latest_version_dir:
    #     # 如果找到历史版本，读取最新的需求文档
    #     file_path = os.path.join(latest_version_dir, "demands.doc")
    #     print(f"使用历史需求文件: {file_path}")
    # else:
    #     # 没有历史版本时使用默认测试文件
    #     file_path = "../data/case.docx"
    #     print(f"使用默认测试文件: {file_path}")
    #
    # # 读取输入内容
    # try:
    #     test_demand = uf.read_docx(file_path)
    # except FileNotFoundError:
    #     raise Exception(f"输入文件不存在: {file_path}")


    test_input = uf.read_docx(file_path)

    print('...........test input............:')
    print(test_input)

    actors, cases, rels = run_use_case_workflow(test_input)

    print("\n最终生成结果:")
    print("参与者:", actors)
    print("用例:", cases)
    print("关系:", rels)
    print("关系:", rels)