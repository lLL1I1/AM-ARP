# File: workflows/change_class_modeling.py
"""RAG-enhanced Class Model Change Workflow"""
import json
import os
import re
from datetime import datetime
from typing import Tuple, Dict, List, Optional, Union
from pathlib import Path

import agentscope
from agentscope.rag import KnowledgeBank
from agentscope.msghub import msghub
from agentscope.message import Msg


def run_class_change_workflow(
        change_request: str,
        knowledge_config: str = "../configs/class_knowledge.json",
        model_base: str = "../workflow/class_versions"
) -> Tuple[Dict, Dict, Dict, Dict]:
    """类模型变更建模工作流（修正类型错误版）"""

    # 初始化类模型变更智能体
    agents = agentscope.init(
        model_configs="G:\\PycharmProjects\\UMLGenerator\\configs\\model_configs.json",
        agent_configs="G:\\PycharmProjects\\UMLGenerator\\configs\\dynamic_class_agent_configs.json"
    )

    # 加载现有最新类模型
    latest_version = _find_latest_class_version(model_base)
    original_data = _load_existing_class_model(latest_version) if latest_version else None

    # 初始化知识库
    knowledge_bank = KnowledgeBank(configs=knowledge_config)
    knowledge_bank.equip(agents[0], ["class_rules"])  # 类定义规则
    knowledge_bank.equip(agents[1], ["attribute_rules"])  # 属性规则
    knowledge_bank.equip(agents[2], ["function_rules"])  # 方法规则
    knowledge_bank.equip(agents[3], ["class_relationship_rules"])  # 关系规则

    # 执行变更流程（添加类型转换保护）
    with msghub(agents) as hub:
        hub.broadcast(Msg("Host", "启动类模型变更流程", role="system"))
        hub.broadcast(Msg("Host", f"变更请求：{change_request}", role="user"))

        # 步骤1：类列表变更
        original_classes = original_data["classes"] if original_data else []
        new_classes = _ensure_dict_format(
            agents[0].get_final_classes(original_classes, change_request),
            agent_name="ClassAgent"
        )

        # 步骤2：类属性变更
        original_attributes = original_data["attributes"] if original_data else []
        changed_attributes = _ensure_dict_format(
            agents[1].get_final_attributes(original_attributes, change_request),
            agent_name="AttributeAgent"
        )

        # 步骤3：类方法变更
        original_methods = original_data["methods"] if original_data else []
        changed_methods = _ensure_dict_format(
            agents[2].get_final_methods(original_methods, change_request),
            agent_name="MethodAgent"
        )

        # 步骤4：类关系变更
        original_relations = original_data["relations"] if original_data else []
        changed_relations = _ensure_dict_format(
            agents[3].get_final_relations(original_relations, change_request),
            agent_name="RelationAgent"
        )

    # 生成最终类模型
    final_model = _merge_class_changes(
        original_data,
        new_classes,
        changed_attributes,
        changed_methods,
        changed_relations
    )

    # 版本化存储
    version_dir = _save_class_version(
        change_request=change_request,
        final_model=final_model,
        original_version=latest_version,
        output_base=model_base
    )

    print(f"\n类模型变更结果已保存至：{version_dir}")
    return new_classes, changed_attributes, changed_methods, changed_relations


def _ensure_dict_format(
        data: Union[Dict, List],
        agent_name: str
) -> Dict:
    """类型安全保护：确保智能体返回字典格式"""
    if isinstance(data, dict):
        return data
    elif isinstance(data, list):
        print(f"警告：{agent_name} 返回列表格式，自动转换为字典结构")
        return {"新增": data, "删除": [], "修改前": [], "修改后": []}
    else:
        raise TypeError(f"{agent_name} 返回格式错误，预期dict/list，实际得到{type(data)}")


def _find_latest_class_version(base_dir: str) -> Optional[str]:
    """查找最新类模型版本（保持不变）"""
    """查找最新类模型版本"""
    version_dirs = []
    for d in Path(base_dir).iterdir():
        if d.is_dir() and re.match(r"\d{4}-\d{2}-\d{2}-\d+", d.name):
            try:
                date_part, num = d.name.rsplit("-", 1)
                dt = datetime.strptime(date_part, "%Y-%m-%d")
                version_dirs.append((dt, int(num), d))
            except ValueError:
                continue

    if not version_dirs:
        return None

    version_dirs.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return str(version_dirs[0][2])


def _load_existing_class_model(version_dir: str) -> Dict:
    """加载类模型数据（添加空值处理）"""
    model_data = {
        "classes": [],
        "attributes": [],
        "methods": [],
        "relations": []
    }

    # 解析类列表
    class_path = Path(version_dir) / "classes.md"
    if class_path.exists():
        model_data["classes"] = list(set(
            re.findall(r"^#+\s+(.+?)\s*$", class_path.read_text(encoding="utf-8"), re.M)
        ))

    # 解析属性
    attr_path = Path(version_dir) / "attributes.md"
    if attr_path.exists():
        model_data["attributes"] = list(set(
            re.findall(r"^\*\s+(\w+\.\w+)", attr_path.read_text(encoding="utf-8"), re.M)
        ))

    # 解析方法
    method_path = Path(version_dir) / "methods.md"
    if method_path.exists():
        model_data["methods"] = list(set(
            re.findall(r"^\*\s+(\w+\.\w+$.*?$)", method_path.read_text(encoding="utf-8"), re.M)
        ))

    # 解析关系
    rel_path = Path(version_dir) / "relations.md"
    if rel_path.exists():
        model_data["relations"] = list(set(
            re.findall(r"(\w+\s*<:[\w\s]+:>\s*\w+)", rel_path.read_text(encoding="utf-8"))
        ))

    return model_data


def _merge_class_changes(
        original: Optional[Dict],
        new_classes: Dict,
        changed_attrs: Dict,
        changed_methods: Dict,
        changed_relations: Dict
) -> Dict:
    """合并类模型变更（增强类型校验）"""
    # 确保原始数据格式正确
    original = original or {
        "classes": [],
        "attributes": [],
        "methods": [],
        "relations": []
    }

    return {
        "classes": _safe_merge_elements(
            original["classes"],
            new_classes,
            "Class"
        ),
        "attributes": _safe_merge_elements(
            original["attributes"],
            changed_attrs,
            "Attribute"
        ),
        "methods": _safe_merge_elements(
            original["methods"],
            changed_methods,
            "Method"
        ),
        "relations": _safe_merge_relations(
            original["relations"],
            changed_relations
        )
    }


def _safe_merge_elements(
        original: List[str],
        changes: Dict,
        element_type: str
) -> List[str]:
    """带类型检查的元素合并"""
    if not isinstance(changes, dict):
        raise TypeError(f"{element_type}变更数据应为字典，实际得到{type(changes)}")

    return _merge_elements_dict(original, changes)


def _merge_elements_dict(original: List[str], changes: Dict) -> List[str]:
    """字典结构合并（带容错处理）"""
    try:
        merged = list(set(original + changes.get("新增", [])))
        merged = [x for x in merged if x not in set(changes.get("删除", []))]

        # 处理修改操作
        modifies_old = changes.get("修改前", [])
        modifies_new = changes.get("修改后", [])
        for old, new in zip(modifies_old, modifies_new):
            if old in merged:
                merged.remove(old)
                merged.append(new)
        return list(set(merged))
    except Exception as e:
        raise ValueError(f"合并元素时发生错误：{str(e)}")


def _safe_merge_relations(
        original: List[str],
        changes: Dict
) -> List[str]:
    """带类型检查的关系合并"""
    if not isinstance(changes, dict):
        raise TypeError(f"关系变更数据应为字典，实际得到{type(changes)}")

    return _merge_relations_dict(original, changes)


def _merge_relations_dict(original: List[str], changes: Dict) -> List[str]:
    """关系合并（增强容错）"""
    try:
        merged = list(set(original + changes.get("新增", [])))
        merged = [r for r in merged if r not in set(changes.get("删除", []))]

        # 处理关系修改
        modifies_old = changes.get("修改前", [])
        modifies_new = changes.get("修改后", [])
        for old, new in zip(modifies_old, modifies_new):
            if old in merged:
                merged.remove(old)
                merged.append(new)
        return merged
    except Exception as e:
        raise ValueError(f"合并关系时发生错误：{str(e)}")


def _save_class_version(
        change_request: str,
        final_model: Dict,
        original_version: Optional[str],
        output_base: str
) -> str:
    """版本化存储（保持不变）"""
    """保存版本化类模型"""
    today = datetime.now().strftime("%Y-%m-%d")
    if original_version and os.path.basename(original_version).startswith(today):
        ver_num = int(original_version.split("-")[-1]) + 1
    else:
        existing = list(Path(output_base).glob(f"{today}-*"))
        ver_num = len(existing) + 1

    version_id = f"{today}-{ver_num}"
    version_dir = Path(output_base) / version_id
    version_dir.mkdir(parents=True, exist_ok=True)

    # 保存变更说明
    with open(version_dir / "CHANGE.md", "w", encoding="utf-8") as f:
        f.write("# 类模型变更记录\n\n")
        f.write(f"## 变更请求\n{change_request}\n\n")
        f.write("## 变更类型\n- 类列表变更\n- 属性变更\n- 方法变更\n- 关系变更\n")
        if original_version:
            f.write(f"\n**基线版本**: {os.path.basename(original_version)}")

    # 保存结构化结果
    _save_class_artifacts(
        background=change_request,
        classes=final_model["classes"],
        attributes=final_model["attributes"],
        methods=final_model["methods"],
        relations=final_model["relations"],
        output_dir=version_dir
    )

    return str(version_dir)

def _save_class_artifacts(
        background: str,
        classes: List[str],
        attributes: List[str],
        methods: List[str],
        relations: List[str],
        output_dir: Path
) -> None:
    """保存类模型产物（添加空值处理）"""
    # 确保输出目录存在
    output_dir.mkdir(parents=True, exist_ok=True)

    # 类列表
    with open(output_dir / "classes.md", "w", encoding="utf-8") as f:
        f.write("# 类列表\n\n")
        for cls in classes or []:  # 处理空值
            f.write(f"## {cls}\n- 类型: 业务实体\n- 关联需求: {background}\n\n")

        # 保存属性
    with open(output_dir / "attributes.md", "w", encoding="utf-8") as f:
        f.write("# 类属性\n\n")
        for attr in attributes:
            if '.' in attr:
                cls, field = attr.split('.', 1)
                f.write(f"* {cls}.{field}\n  - 类型: String\n  - 约束: 必填\n\n")

        # 保存方法
    with open(output_dir / "methods.md", "w", encoding="utf-8") as f:
        f.write("# 类方法\n\n")
        for method in methods:
            if '.' in method:
                cls, func = method.split('.', 1)
                f.write(f"* {cls}.{func}\n  - 可见性: public\n  - 复杂度: 1\n\n")

        # 保存关系
    with open(output_dir / "relations.md", "w", encoding="utf-8") as f:
        f.write("# 类关系\n\n")
        for rel in relations:
            f.write(f"{rel}\n")


if __name__ == "__main__":
    # 测试用例（添加错误处理）
    try:
        # 测试场景：支付系统重构
        change1 = "1. 拆分Payment类为OnlinePayment和CashPayment\n2. 为Order添加calculateTax方法"
        classes, attrs, methods, rels = run_class_change_workflow(change1)
        print("首次变更结果:")
        print(f"类变更：新增 {classes.get('新增', [])}，删除 {classes.get('删除', [])}")

        # 二次变更测试
        change2 = "在OnlinePayment中添加currency属性和validateCurrency()方法"
        run_class_change_workflow(change2)
    except Exception as e:
        print(f"工作流执行失败：{str(e)}")
        raise