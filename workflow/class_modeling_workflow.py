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

    agents = agentscope.init(
        model_configs="G:\\PycharmProjects\\UMLGenerator\\configs\\model_configs.json",
        agent_configs="G:\\PycharmProjects\\UMLGenerator\\configs\\class_agent_configs.json"
    )

    knowledge_bank = KnowledgeBank(configs=knowledge_config)


    knowledge_bank.equip(agents[0], ["class_rules"])  # ClassIdentifier
    knowledge_bank.equip(agents[1], ["attribute_rules"])  # AttributeIdentifier
    knowledge_bank.equip(agents[2], ["function_rules"])  # FunctionIdentifier
    knowledge_bank.equip(agents[3], ["class_relationship_rules"])  # ClassRelationshipIdentifier

    with msghub(agents) as hub:
        hub.broadcast(Msg("Host", "Start the class diagram modeling process:", role="system"))
        hub.broadcast(Msg("Host", f"background：{background}", role="user"))

        classes = agents[0].identify_classes(background)
        hub.broadcast(Msg("ClassAgent", json.dumps(classes, ensure_ascii=False), role="assistant"))

        attributes = agents[1].identify_attributes(classes, background)
        hub.broadcast(Msg("AttrAgent", json.dumps(attributes, ensure_ascii=False), role="assistant"))

        functions = agents[2].identify_functions(attributes, background)
        hub.broadcast(Msg("FuncAgent", json.dumps(functions, ensure_ascii=False), role="assistant"))

        relationships = agents[3].identify_relationships(functions, background)
        hub.broadcast(Msg("RelAgent", json.dumps(relationships, ensure_ascii=False), role="assistant"))

    version_dir = _save_class_results(
        background=background,
        classes=classes,
        attributes=attributes,
        functions=functions,
        relationships=relationships
    )
    print(f"\nThe generated results are versioned and saved to a directory: {version_dir}")
    return classes, attributes, functions, relationships


def _save_class_results(
        background: str,
        classes: List[str],
        attributes: Dict[str, List[str]],
        functions: Dict[str, List[str]],
        relationships: List[str],
        output_base: str = "class_versions"
) -> str:

    os.makedirs(output_base, exist_ok=True)

    # version num（class-date-num）
    today = datetime.now().strftime("%Y-%m-%d")
    existing_versions = glob.glob(os.path.join(output_base, f"{today}-*"))
    version_num = len(existing_versions) + 1
    version_id = f"class-{today}-{version_num}"
    version_dir = os.path.join(output_base, version_id)
    os.makedirs(version_dir, exist_ok=True)

    with open(os.path.join(version_dir, "context.md"), 'w', encoding='utf-8') as f:
        f.write(f"# Original requirement background\n\n{background}\n")

    with open(os.path.join(version_dir, "classes.md"), 'w', encoding='utf-8') as f:
        f.write("# Recognition class list\n\n")
        for cls in classes:
            f.write(f"- {cls}\n")

    with open(os.path.join(version_dir, "attributes.md"), 'w', encoding='utf-8') as f:
        f.write("# Class attribute detail\n\n")
        for cls, attrs in attributes.items():
            f.write(f"## {cls}\n")
            if attrs:
                f.write("\n".join(f"- {attr}" for attr in attrs) + "\n\n")
            else:
                f.write("> No property definition is available\n\n")

    with open(os.path.join(version_dir, "methods.md"), 'w', encoding='utf-8') as f:
        f.write("# Class method detail\n\n")
        for cls, funcs in functions.items():
            f.write(f"## {cls}\n")
            if funcs:
                f.write("\n".join(f"- {func}" for func in funcs) + "\n\n")
            else:
                f.write("> No method definition yet\n\n")

    with open(os.path.join(version_dir, "relationships.md"), 'w', encoding='utf-8') as f:
        f.write("# Class relation matrix\n\n")
        f.write("| Subject | relation type | object | description |\n")
        f.write("|------|---------|------|-----|\n")
        for rel in relationships:

            if "extend" in rel:
                parts = re.split(r"\s*extend from\s*", rel)
                rel_type = "extend"
            elif "Association " in rel:
                parts = re.split(r"\s*Association \s*", rel)
                rel_type = "Association "
            elif "Dependency" in rel:
                parts = re.split(r"\s*Dependency\s*", rel)
                rel_type = "Dependency"
            else:
                parts = [rel, ""]
                rel_type = "Dependency"

            if len(parts) >= 2:
                subject, obj = parts[0], parts[1]
                f.write(f"| {subject} | {rel_type} | {obj} | systematic design |\n")
            else:
                f.write(f"| {rel} | The | system is automatically generated by | |\n")

    return version_dir


if __name__ == "__main__":
    # file_path = "../data/case.docx"

    output_base = "./agents/output"
    latest_version_dir = uf.get_latest_version_dir()
    # print(latest_version_dir)

    if latest_version_dir:

        file_path = os.path.join(latest_version_dir, "demands.doc")
        print(f"Use the history requirements file: {file_path}")
    else:

        file_path = "../data/case.docx"
        print(f"Use the default test file: {file_path}")

    try:
        test_demand = uf.read_docx(file_path)
    except FileNotFoundError:
        raise Exception(f"The input file does not exist: {file_path}")

    test_input = uf.read_docx(file_path)

    classes, attrs, funcs, rels = run_class_modeling_workflow(test_input)

    print("\nresult:")
    print("[class]", classes)
    print("[attribute]", attrs)
    print("[function]", funcs)
    print("[relationship]", rels)