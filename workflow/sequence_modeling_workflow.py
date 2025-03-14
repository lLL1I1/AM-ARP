# File: workflows/sequence_modeling.py
"""RAG-enhanced Sequence Workflow"""
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
import utils.util_function as uf

def run_sequence_workflow(
        context: str,
        knowledge_config: str = "../configs/sequence_knowledge.json"
) -> Tuple[List[str], List[str], List[str]]:

    agents = agentscope.init(
        model_configs="G:\\PycharmProjects\\UMLGenerator\\configs\\model_configs.json",
        agent_configs="G:\\PycharmProjects\\UMLGenerator\\configs\\sequence_agent_configs.json"
    )

    knowledge_bank = KnowledgeBank(configs=knowledge_config)

    knowledge_bank.equip(agents[0], ["object_rules"])  # ObjectIdentifier
    knowledge_bank.equip(agents[1], ["message_rules"])  # MessageIdentifier
    knowledge_bank.equip(agents[2], ["sequence_rules"])  # MessageOrderIdentifier


    with msghub(agents) as hub:
        hub.broadcast(Msg("Host", "Start the timing modeling process:", role="system"))
        hub.broadcast(Msg("Host", f"context:{context}", role="user"))

        objects = agents[0].identify_objects(context)
        hub.broadcast(Msg("ObjectAgent", json.dumps(objects, ensure_ascii=False), role="assistant"))

        messages = agents[1].identify_messages(objects, context)
        hub.broadcast(Msg("MessageAgent", json.dumps(messages, ensure_ascii=False), role="assistant"))

        sequence = agents[2].identify_sequence(messages, context)
        hub.broadcast(Msg("OrderAgent", json.dumps(sequence, ensure_ascii=False), role="assistant"))


    version_dir = _save_sequence_results(
        context=context,
        objects=objects,
        messages=messages,
        sequence=sequence
    )
    print(f"\nThe generated results are versioned and saved to a directory: {version_dir}")
    return objects, messages, sequence


def _save_sequence_results(
        context: str,
        objects: List[str],
        messages: List[str],
        sequence: List[str],
        output_base: str = "sequence_versions"
) -> str:

    os.makedirs(output_base, exist_ok=True)
    #version num（sequence-date-num）
    today = datetime.now().strftime("%Y-%m-%d")
    existing_versions = glob.glob(os.path.join(output_base, f"{today}-*"))
    version_num = len(existing_versions) + 1
    version_id = f"{today}-{version_num}"
    version_dir = os.path.join(output_base, version_id)
    os.makedirs(version_dir, exist_ok=True)

    with open(os.path.join(version_dir, "context.md"), 'w', encoding='utf-8') as f:
        f.write(f"# context\n\n{context}\n")

    with open(os.path.join(version_dir, "objects.md"), 'w', encoding='utf-8') as f:
        f.write("# object list\n\n")
        for idx, obj in enumerate(objects, 1):
            f.write(f"{idx}. {obj}\n")

    with open(os.path.join(version_dir, "messages.md"), 'w', encoding='utf-8') as f:
        f.write("# Message Lists\n\n")
        f.write("| Sender | receiver | The message content is of the | type |\n")
        f.write("|--------|--------|----------|------|\n")
        for msg in messages:
            parts = re.split(r"\s*->\s*|\s*:\s*", msg.strip())
            if len(parts) >= 3:
                sender, receiver = parts[0], parts[1]
                content = " : ".join(parts[2:]) if len(parts) > 2 else ""
                f.write(f"| {sender} | {receiver} | {content} | synchronous messages |\n")
            else:
                f.write(f"| Unknown | unknown | {msg} | indicates an asynchronous message |\n")

    with open(os.path.join(version_dir, "sequence.md"), 'w', encoding='utf-8') as f:
        f.write("# Sequential flow\n\n")
        for idx, step in enumerate(sequence, 1):
            f.write(f"{idx}. {step}\n")

    return version_dir


if __name__ == "__main__":
    # file_path = "../data/sequence_case.docx"

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

    objects, messages, sequence = run_sequence_workflow(test_input)

    print("\nFinal generated result:")
    print("[recognized object]", objects)
    print("[interactive message]", messages)
    print("[sequential flow]", sequence)