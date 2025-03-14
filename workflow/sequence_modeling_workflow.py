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
    """知识增强的时序建模工作流"""
    # 初始化智能体（通过配置文件加载）
    agents = agentscope.init(
        model_configs="G:\\PycharmProjects\\UMLGenerator\\configs\\model_configs.json",
        agent_configs="G:\\PycharmProjects\\UMLGenerator\\configs\\sequence_agent_configs.json"
    )
    # 初始化知识库
    knowledge_bank = KnowledgeBank(configs=knowledge_config)
    # 装备知识库到对应智能体
    knowledge_bank.equip(agents[0], ["object_rules"])  # ObjectIdentifier
    knowledge_bank.equip(agents[1], ["message_rules"])  # MessageIdentifier
    knowledge_bank.equip(agents[2], ["sequence_rules"])  # MessageOrderIdentifier

    # 执行协作流程
    with msghub(agents) as hub:
        hub.broadcast(Msg("Host", "启动时序建模流程", role="system"))
        hub.broadcast(Msg("Host", f"输入场景：{context}", role="user"))
        # 阶段1: 对象识别
        objects = agents[0].identify_objects(context)
        hub.broadcast(Msg("ObjectAgent", json.dumps(objects, ensure_ascii=False), role="assistant"))
        # 阶段2: 消息识别（依赖对象列表）
        messages = agents[1].identify_messages(objects, context)
        hub.broadcast(Msg("MessageAgent", json.dumps(messages, ensure_ascii=False), role="assistant"))
        # 阶段3: 时序识别（依赖消息列表）
        sequence = agents[2].identify_sequence(messages, context)
        hub.broadcast(Msg("OrderAgent", json.dumps(sequence, ensure_ascii=False), role="assistant"))

    # 结构化保存结果
    version_dir = _save_sequence_results(
        context=context,
        objects=objects,
        messages=messages,
        sequence=sequence
    )
    print(f"\n生成结果已版本化保存至目录: {version_dir}")
    return objects, messages, sequence


def _save_sequence_results(
        context: str,
        objects: List[str],
        messages: List[str],
        sequence: List[str],
        output_base: str = "sequence_versions"
) -> str:
    """结构化保存时序图结果到版本化的Markdown文件"""
    # 创建基础目录
    os.makedirs(output_base, exist_ok=True)
    # 生成版本号（sequence-日期-序号）
    today = datetime.now().strftime("%Y-%m-%d")
    existing_versions = glob.glob(os.path.join(output_base, f"{today}-*"))
    version_num = len(existing_versions) + 1
    version_id = f"{today}-{version_num}"
    version_dir = os.path.join(output_base, version_id)
    os.makedirs(version_dir, exist_ok=True)

    # 保存场景描述
    with open(os.path.join(version_dir, "context.md"), 'w', encoding='utf-8') as f:
        f.write(f"# 场景描述\n\n{context}\n")

    # 结构化保存对象
    with open(os.path.join(version_dir, "objects.md"), 'w', encoding='utf-8') as f:
        f.write("# 对象列表\n\n")
        for idx, obj in enumerate(objects, 1):
            f.write(f"{idx}. {obj}\n")

    # 结构化保存消息
    with open(os.path.join(version_dir, "messages.md"), 'w', encoding='utf-8') as f:
        f.write("# 消息列表\n\n")
        f.write("| 发送者 | 接收者 | 消息内容 | 类型 |\n")
        f.write("|--------|--------|----------|------|\n")
        for msg in messages:
            # 解析消息格式（示例：用户 -> 系统 : 登录请求）
            parts = re.split(r"\s*->\s*|\s*:\s*", msg.strip())
            if len(parts) >= 3:
                sender, receiver = parts[0], parts[1]
                content = " : ".join(parts[2:]) if len(parts) > 2 else ""
                f.write(f"| {sender} | {receiver} | {content} | 同步消息 |\n")
            else:
                f.write(f"| 未知 | 未知 | {msg} | 异步消息 |\n")

    # 结构化保存时序
    with open(os.path.join(version_dir, "sequence.md"), 'w', encoding='utf-8') as f:
        f.write("# 时序流程\n\n")
        for idx, step in enumerate(sequence, 1):
            f.write(f"{idx}. {step}\n")

    return version_dir


if __name__ == "__main__":
    # file_path = "../data/sequence_case.docx"

    output_base = "./agents/output"
    latest_version_dir = uf.get_latest_version_dir()
    # print(latest_version_dir)

    if latest_version_dir:
        # 如果找到历史版本，读取最新的需求文档
        file_path = os.path.join(latest_version_dir, "demands.doc")
        print(f"使用历史需求文件: {file_path}")
    else:
        # 没有历史版本时使用默认测试文件
        file_path = "../data/case.docx"
        print(f"使用默认测试文件: {file_path}")

    try:
        test_demand = uf.read_docx(file_path)
    except FileNotFoundError:
        raise Exception(f"输入文件不存在: {file_path}")

    test_input = uf.read_docx(file_path)

    # 执行工作流
    objects, messages, sequence = run_sequence_workflow(test_input)
    # 输出结果
    print("\n最终生成结果:")
    print("[识别对象]", objects)
    print("[交互消息]", messages)
    print("[时序流程]", sequence)