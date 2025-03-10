# File: workflows/change_sequence_modeling.py
"""RAG-enhanced Sequence Model Change Workflow"""
import json
import os
import re
from datetime import datetime
from typing import Tuple, List, Dict, Optional
from pathlib import Path

import agentscope
from agentscope.rag import KnowledgeBank
from agentscope.msghub import msghub
from agentscope.message import Msg


def run_sequence_change_workflow(
        change_request: str,
        knowledge_config: str = "../configs/sequence_knowledge.json",
        model_base: str = "../workflow/sequence_versions"
) -> Tuple[Dict[str, List[str]], Dict[str, List[str]], List[str]]:
    """顺序模型变更建模工作流"""

    # 初始化顺序模型变更智能体
    agents = agentscope.init(
        model_configs="G:\\PycharmProjects\\UMLGenerator\\configs\\model_configs.json",
        agent_configs="G:\\PycharmProjects\\UMLGenerator\\configs\\dynamic_sequence_agent_configs.json"
    )

    # 加载现有最新顺序模型（修复编码问题）
    latest_version = _find_latest_sequence_version(model_base)
    original_data = _load_existing_sequence_model(latest_version) if latest_version else None

    # 初始化知识库
    knowledge_bank = KnowledgeBank(configs=knowledge_config)
    knowledge_bank.equip(agents[0], ["sequence_change_rules"])  #旧的模型当作知识
    knowledge_bank.equip(agents[1], ["sequence_change_rules"])
    knowledge_bank.equip(agents[2], ["sequence_change_rules"])

    knowledge_bank.equip(agents[0], ["object_rules"])  # 对象规则
    knowledge_bank.equip(agents[1], ["message_rules"])  # 消息规则
    knowledge_bank.equip(agents[2], ["sequence_rules"])  # 流程规则

    # 执行变更流程
    with msghub(agents) as hub:
        hub.broadcast(Msg("Host", "启动顺序模型变更流程", role="system"))
        hub.broadcast(Msg("Host", f"变更请求：{change_request}", role="user"))

        # 步骤1：对象变更
        original_objects = original_data["objects"] if original_data else []
        new_objects = agents[0].get_final_objects(original_objects, change_request)
        hub.broadcast(Msg("ObjectAgent", json.dumps(new_objects, ensure_ascii=False), role="assistant"))

        # 步骤2：消息变更
        original_messages = original_data["messages"] if original_data else []
        changed_messages = agents[1].get_final_messages(original_messages, change_request)
        hub.broadcast(Msg("MessageAgent", json.dumps(changed_messages, ensure_ascii=False), role="assistant"))

        # 步骤3：流程顺序调整
        original_flow = original_data["flow"] if original_data else []
        changed_flow = agents[2].get_final_message_order(original_flow, change_request)
        hub.broadcast(Msg("FlowAgent", json.dumps(changed_flow, ensure_ascii=False), role="assistant"))

    # 生成最终模型（合并变更）
    final_model = _merge_sequence_changes(
        original_data,
        new_objects,
        changed_messages,
        changed_flow
    )

    # 版本化存储（统一使用UTF-8编码）
    version_dir = _save_sequence_version(
        change_request=change_request,
        final_model=final_model,
        original_version=latest_version,
        output_base=model_base
    )

    print(f"\n顺序模型变更结果已保存至：{version_dir}")
    return new_objects, changed_messages, changed_flow


def _find_latest_sequence_version(base_dir: str) -> Optional[str]:
    """查找最新顺序模型版本（实现同用例版本查找）"""
    version_dirs = []
    for d in Path(base_dir).iterdir():
        if d.is_dir() and re.match(r"\d{4}-\d{2}-\d{2}-\d+", d.name):
            try:
                date_part, num = d.name.rsplit("-", 1)
                dt = datetime.strptime(date_part, "%Y-%m-%d")
                version_dirs.append((dt, int(num), d))
            except ValueError:
                continue
    return str(version_dirs[0][2]) if version_dirs else None


def _load_existing_sequence_model(version_dir: str) -> Dict:
    """加载顺序模型数据（修复编码问题）"""
    model_data = {"objects": [], "messages": [], "flow": []}
    version_path = Path(version_dir)

    # 解析对象（统一使用UTF-8）
    obj_path = version_path / "objects.md"
    if obj_path.exists():
        content = obj_path.read_text(encoding='utf-8')
        model_data["objects"] = list(set(re.findall(r"^\*\s+(\w+:\w+.*?)$", content, re.M)))

    # 解析消息（统一使用UTF-8）
    msg_path = version_path / "messages.md"
    if msg_path.exists():
        content = msg_path.read_text(encoding='utf-8')
        model_data["messages"] = list(set(re.findall(r"^\d+\)\s+(.+)$", content, re.M)))

    # 解析流程（统一使用UTF-8）
    flow_path = version_path / "flow.md"
    if flow_path.exists():
        model_data["flow"] = flow_path.read_text(encoding='utf-8').splitlines()

    return model_data


def _merge_sequence_changes(
        original: Optional[Dict],
        new_objects: List[str],
        changed_messages: List[str],
        changed_flow: List[str]
) -> Dict:
    """合并顺序模型变更"""
    # 合并对象
    final_objects = list(set(new_objects))

    # 合并消息
    original_msgs = original["messages"] if original else []
    final_msgs = _merge_messages(original_msgs, changed_messages)

    # 合并流程（保留完整流程结构）
    final_flow = changed_flow if changed_flow else original.get("flow", [])

    return {
        "objects": final_objects,
        "messages": final_msgs,
        "flow": final_flow
    }


def _merge_messages(original: List[str], changes: List[str]) -> List[str]:
    """智能合并消息变更"""
    msg_signatures = {}
    # 保留原始消息签名
    for msg in original:
        sig = re.split(r"\s*:\s*", msg, 1)[0]
        msg_signatures[sig] = msg
    # 应用变更
    for change_msg in changes:
        sig = re.split(r"\s*:\s*", change_msg, 1)[0]
        msg_signatures[sig] = change_msg
    return list(msg_signatures.values())

def _save_sequence_version(
        change_request: str,
        final_model: Dict,
        original_version: Optional[str],
        output_base: str
) -> str:
    """版本化存储（统一编码处理）"""
    output_path = Path(output_base)
    output_path.mkdir(exist_ok=True)

    # 生成版本号（修正部分）
    today = datetime.now().strftime("%Y-%m-%d")
    existing_versions = list(output_path.glob(f"{today}-*"))
    ver_num = len(existing_versions) + 1 if existing_versions else 1
    version_id = f"{today}-{ver_num}"
    version_dir = output_path / version_id
    version_dir.mkdir()

    # 保存变更请求
    (version_dir / "change_request.txt").write_text(change_request, encoding='utf-8')

    # 保存结构化结果
    _save_sequence_artifacts(
        objects=final_model["objects"],
        messages=final_model["messages"],
        flow=final_model["flow"],
        output_dir=version_dir
    )

    # 保存版本关联信息
    if original_version:
        (version_dir / "previous_version.txt").write_text(original_version, encoding='utf-8')

    return str(version_dir)


def _save_sequence_artifacts(
        objects: List[str],
        messages: List[str],
        flow: List[str],
        output_dir: Path
) -> None:
    """保存顺序模型结构化结果到指定目录（统一UTF-8编码）"""
    # 保存对象定义
    with open(output_dir / "objects.md", 'w', encoding='utf-8') as f:
        f.write("# 顺序图对象列表\n\n")
        for obj in sorted(objects):
            parts = re.split(r"[:#]", obj)
            name = parts[0].strip()
            obj_type = parts[1].strip() if len(parts) > 1 else "Component"
            note = parts[2].strip() if len(parts) > 2 else ""
            f.write(f"## {name}\n- 对象名称: {name}\n- 类型: {obj_type}\n")
            if note:
                f.write(f"- 备注: {note}\n")
            f.write("\n")

    # 保存详细消息列表
    with open(output_dir / "messages.md", 'w', encoding='utf-8') as f:
        f.write("# 详细消息清单\n\n")
        for idx, msg in enumerate(messages, 1):
            clean_msg = re.sub(r"\s*->\s*", "→", msg)  # 统一使用箭头符号
            f.write(f"{idx}. ​**{clean_msg}**\n")
            f.write(f"   - 类型: 同步消息\n   - 技术协议: REST API\n\n")

    # 保存流程结构
    with open(output_dir / "flow.md", 'w', encoding='utf-8') as f:
        f.write("# 消息流程控制结构\n\n```sequence\n")
        f.writelines(f"{line}\n" for line in flow)
        f.write("```\n")

    # 生成PlantUML图
    with open(output_dir / "sequence.puml", 'w', encoding='utf-8') as f:
        f.write("@startuml\n")
        # 添加参与者声明
        type_mapping = {
            "Actor": "actor",
            "System": "participant",
            "Database": "database",
            "Component": "component"
        }
        for obj in objects:
            name_type = obj.split("#")[0].strip()
            name, obj_type = (name_type.split(":") + ["Component"])[:2]
            uml_type = type_mapping.get(obj_type.strip(), "participant")
            f.write(f"{uml_type} \"{name}\" as {name.replace(' ', '_')}\n")
        # 添加消息流程
        f.write("\n")
        for line in flow:
            line = line.replace("alt", "alt").replace("loop", "loop")
            line = line.replace("opt", "opt").replace("par", "par")
            line = line.replace("else", "else").replace("end", "end")
            f.write(f"{line}\n")
        f.write("@enduml\n")

    # 保存变更元数据
    with open(output_dir / "metadata.json", 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "object_count": len(objects),
            "message_count": len(messages),
            "flow_steps": len(flow)
        }, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    # 测试场景：订单支付流程优化
    # change1 = "添加支付超时重试机制，最多重试3次"
    # objects, messages, flow = run_sequence_change_workflow(change1)

    # 二次变更测试
    change2 = "在支付成功后增加短信通知环节"
    run_sequence_change_workflow(change2)