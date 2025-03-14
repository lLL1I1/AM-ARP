# File: workflows/class_modeling.py
"""RAG-enhanced Class Modeling Workflow"""
import json
import os
import glob
import re
from datetime import datetime
from typing import Tuple, Dict, List
import agentscope
from agentscope.rag import KnowledgeBank
from agentscope.msghub import msghub
from agentscope.message import Msg
import utils.util_function as uf


def run_class_modeling_workflow(
        background: str,
        knowledge_config: str = "../configs/class_knowledge.json"
) -> Tuple[List[str], Dict[str, List[str]], Dict[str, List[str]], List[str]]:
    """知识增强的类图建模工作流"""
    # 初始化智能体
    agents = agentscope.init(
        model_configs="G:\\PycharmProjects\\UMLGenerator\\configs\\model_configs.json",
        agent_configs="G:\\PycharmProjects\\UMLGenerator\\configs\\class_agent_configs.json"
    )

    # 初始化知识库
    knowledge_bank = KnowledgeBank(configs=knowledge_config)

    # 装备知识库到对应智能体
    knowledge_bank.equip(agents[0], ["class_rules"])  # ClassIdentifier
    knowledge_bank.equip(agents[1], ["attribute_rules"])  # AttributeIdentifier
    knowledge_bank.equip(agents[2], ["function_rules"])  # FunctionIdentifier
    knowledge_bank.equip(agents[3], ["class_relationship_rules"])  # ClassRelationshipIdentifier

    # 执行协作流程
    with msghub(agents) as hub:
        hub.broadcast(Msg("Host", "启动类图建模流程", role="system"))
        hub.broadcast(Msg("Host", f"输入背景：{background}", role="user"))

        # 各阶段识别
        classes = agents[0].identify_classes(background)
        hub.broadcast(Msg("ClassAgent", json.dumps(classes, ensure_ascii=False), role="assistant"))

        attributes = agents[1].identify_attributes(classes, background)
        hub.broadcast(Msg("AttrAgent", json.dumps(attributes, ensure_ascii=False), role="assistant"))

        functions = agents[2].identify_functions(attributes, background)
        hub.broadcast(Msg("FuncAgent", json.dumps(functions, ensure_ascii=False), role="assistant"))

        relationships = agents[3].identify_relationships(functions, background)
        hub.broadcast(Msg("RelAgent", json.dumps(relationships, ensure_ascii=False), role="assistant"))

    # 结构化保存结果
    version_dir = _save_class_results(
        background=background,
        classes=classes,
        attributes=attributes,
        functions=functions,
        relationships=relationships
    )
    print(f"\n生成结果已版本化保存至目录: {version_dir}")
    return classes, attributes, functions, relationships


def _save_class_results(
        background: str,
        classes: List[str],
        attributes: Dict[str, List[str]],
        functions: Dict[str, List[str]],
        relationships: List[str],
        output_base: str = "class_versions"
) -> str:
    """结构化保存类图结果到版本化的Markdown文件"""
    # 创建基础目录
    os.makedirs(output_base, exist_ok=True)

    # 生成版本号（class-日期-序号）
    today = datetime.now().strftime("%Y-%m-%d")
    existing_versions = glob.glob(os.path.join(output_base, f"{today}-*"))
    version_num = len(existing_versions) + 1
    version_id = f"class-{today}-{version_num}"
    version_dir = os.path.join(output_base, version_id)
    os.makedirs(version_dir, exist_ok=True)

    # 保存原始背景
    with open(os.path.join(version_dir, "context.md"), 'w', encoding='utf-8') as f:
        f.write(f"# 原始需求背景\n\n{background}\n")

    # 保存类列表
    with open(os.path.join(version_dir, "classes.md"), 'w', encoding='utf-8') as f:
        f.write("# 识别类列表\n\n")
        for cls in classes:
            f.write(f"- {cls}\n")

    # 保存类属性
    with open(os.path.join(version_dir, "attributes.md"), 'w', encoding='utf-8') as f:
        f.write("# 类属性明细\n\n")
        for cls, attrs in attributes.items():
            f.write(f"## {cls}\n")
            if attrs:
                f.write("\n".join(f"- {attr}" for attr in attrs) + "\n\n")
            else:
                f.write("> 暂无属性定义\n\n")

    # 保存类方法
    with open(os.path.join(version_dir, "methods.md"), 'w', encoding='utf-8') as f:
        f.write("# 类方法明细\n\n")
        for cls, funcs in functions.items():
            f.write(f"## {cls}\n")
            if funcs:
                f.write("\n".join(f"- {func}" for func in funcs) + "\n\n")
            else:
                f.write("> 暂无方法定义\n\n")

    # 保存类关系
    with open(os.path.join(version_dir, "relationships.md"), 'w', encoding='utf-8') as f:
        f.write("# 类关系矩阵\n\n")
        f.write("| 主体 | 关系类型 | 客体 | 说明 |\n")
        f.write("|------|---------|------|-----|\n")
        for rel in relationships:
            # 解析关系表达式（示例：用户继承自人员）
            if "继承" in rel:
                parts = re.split(r"\s*继承自\s*", rel)
                rel_type = "继承"
            elif "关联" in rel:
                parts = re.split(r"\s*关联\s*", rel)
                rel_type = "关联"
            elif "依赖" in rel:
                parts = re.split(r"\s*依赖\s*", rel)
                rel_type = "依赖"
            else:
                parts = [rel, ""]
                rel_type = "关联"

            if len(parts) >= 2:
                subject, obj = parts[0], parts[1]
                f.write(f"| {subject} | {rel_type} | {obj} | 系统设计 |\n")
            else:
                f.write(f"| {rel} | 关联 | 系统 | 自动生成 |\n")

    return version_dir


if __name__ == "__main__":
    # file_path = "../data/case.docx"

    output_base = "./agents/output"
    latest_version_dir = uf.get_latest_version_dir()
    # print(latest_version_dir)

    if latest_version_dir:
        #如果找到历史版本，读取最新的需求文档
        file_path = os.path.join(latest_version_dir, "demands.doc")
        print(f"使用历史需求文件: {file_path}")
    else:
        #没有历史版本时使用默认测试文件
        file_path = "../data/case.docx"
        print(f"使用默认测试文件: {file_path}")

    try:
        test_demand = uf.read_docx(file_path)
    except FileNotFoundError:
        raise Exception(f"输入文件不存在: {file_path}")

    test_input = uf.read_docx(file_path)

    classes, attrs, funcs, rels = run_class_modeling_workflow(test_input)

    print("\n最终生成结果:")
    print("[识别类]", classes)
    print("[类属性]", attrs)
    print("[类方法]", funcs)
    print("[类关系]", rels)