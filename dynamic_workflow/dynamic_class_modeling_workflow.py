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
    """Class Model Change Modeling Workflow (Fixed Type Error Version)"""

    agents = agentscope.init(
        model_configs="G:\\PycharmProjects\\UMLGenerator\\configs\\model_configs.json",
        agent_configs="G:\\PycharmProjects\\UMLGenerator\\configs\\dynamic_class_agent_configs.json"
    )

    latest_version = _find_latest_class_version(model_base)
    original_data = _load_existing_class_model(latest_version) if latest_version else None

    knowledge_bank = KnowledgeBank(configs=knowledge_config)
    knowledge_bank.equip(agents[0], ["class_rules"])  
    knowledge_bank.equip(agents[1], ["attribute_rules"])  
    knowledge_bank.equip(agents[2], ["function_rules"]) 
    knowledge_bank.equip(agents[3], ["class_relationship_rules"])  

    with msghub(agents) as hub:
        hub.broadcast(Msg("Host", "Starting class model change process", role="system"))
        hub.broadcast(Msg("Host", f"Change request: {change_request}", role="user"))

        # Step 1: Class list changes
        original_classes = original_data["classes"] if original_data else []
        new_classes = _ensure_dict_format(
            agents[0].get_final_classes(original_classes, change_request),
            agent_name="ClassAgent"
        )

        # Step 2: Class attribute changes
        original_attributes = original_data["attributes"] if original_data else []
        changed_attributes = _ensure_dict_format(
            agents[1].get_final_attributes(original_attributes, change_request),
            agent_name="AttributeAgent"
        )

        # Step 3: Class method changes
        original_methods = original_data["methods"] if original_data else []
        changed_methods = _ensure_dict_format(
            agents[2].get_final_methods(original_methods, change_request),
            agent_name="MethodAgent"
        )

        # Step 4: Class relationship changes
        original_relations = original_data["relations"] if original_data else []
        changed_relations = _ensure_dict_format(
            agents[3].get_final_relations(original_relations, change_request),
            agent_name="RelationAgent"
        )

    final_model = _merge_class_changes(
        original_data,
        new_classes,
        changed_attributes,
        changed_methods,
        changed_relations
    )

    version_dir = _save_class_version(
        change_request=change_request,
        final_model=final_model,
        original_version=latest_version,
        output_base=model_base
    )

    print(f"\nClass model change results saved to: {version_dir}")
    return new_classes, changed_attributes, changed_methods, changed_relations


def _ensure_dict_format(
        data: Union[Dict, List],
        agent_name: str
) -> Dict:
    """Type safety protection: Ensure agent returns dictionary format"""
    if isinstance(data, dict):
        return data
    elif isinstance(data, list):
        print(f"Warning: {agent_name} returned list format, automatically converted to dictionary structure")
        return {"add": data, "delete": [], "before modification": [], "after modification": []}
    else:
        raise TypeError(f"{agent_name} returned incorrect format, expected dict/list, got {type(data)}")


def _find_latest_class_version(base_dir: str) -> Optional[str]:
    """Find the latest class model version (unchanged)"""
    """Find the latest class model version"""
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
    """Load class model data (added null handling)"""
    model_data = {
        "classes": [],
        "attributes": [],
        "methods": [],
        "relations": []
    }

    class_path = Path(version_dir) / "classes.md"
    if class_path.exists():
        model_data["classes"] = list(set(
            re.findall(r"^#+\s+(.+?)\s*$", class_path.read_text(encoding="utf-8"), re.M)
        ))

    attr_path = Path(version_dir) / "attributes.md"
    if attr_path.exists():
        model_data["attributes"] = list(set(
            re.findall(r"^\*\s+(\w+\.\w+)", attr_path.read_text(encoding="utf-8"), re.M)
        ))

    method_path = Path(version_dir) / "methods.md"
    if method_path.exists():
        model_data["methods"] = list(set(
            re.findall(r"^\*\s+(\w+\.\w+$.*?$)", method_path.read_text(encoding="utf-8"), re.M)
        ))

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
    """Merge class model changes (enhanced type checking)"""

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
    """Element merge with type checking"""
    if not isinstance(changes, dict):
        raise TypeError(f"{element_type} change data should be a dictionary, got {type(changes)}")

    return _merge_elements_dict(original, changes)


def _merge_elements_dict(original: List[str], changes: Dict) -> List[str]:
    """Dictionary structure merge (with fault tolerance)"""
    try:
        merged = list(set(original + changes.get("add", [])))
        merged = [x for x in merged if x not in set(changes.get("delete", []))]

        # Handle modification operations
        modifies_old = changes.get("before modification", [])
        modifies_new = changes.get("after modification", [])
        for old, new in zip(modifies_old, modifies_new):
            if old in merged:
                merged.remove(old)
                merged.append(new)
        return list(set(merged))
    except Exception as e:
        raise ValueError(f"Error merging elements: {str(e)}")


def _safe_merge_relations(
        original: List[str],
        changes: Dict
) -> List[str]:
    """Relationship merge with type checking"""
    if not isinstance(changes, dict):
        raise TypeError(f"Relationship change data should be a dictionary, got {type(changes)}")

    return _merge_relations_dict(original, changes)


def _merge_relations_dict(original: List[str], changes: Dict) -> List[str]:
    """Relationship merge (enhanced fault tolerance)"""
    try:
        merged = list(set(original + changes.get("add", [])))
        merged = [r for r in merged if r not in set(changes.get("delete", []))]

        # Handle relationship modifications
        modifies_old = changes.get("before modification", [])
        modifies_new = changes.get("after modification", [])
        for old, new in zip(modifies_old, modifies_new):
            if old in merged:
                merged.remove(old)
                merged.append(new)
        return merged
    except Exception as e:
        raise ValueError(f"Error merging relationships: {str(e)}")


def _save_class_version(
        change_request: str,
        final_model: Dict,
        original_version: Optional[str],
        output_base: str
) -> str:

    today = datetime.now().strftime("%Y-%m-%d")
    if original_version and os.path.basename(original_version).startswith(today):
        ver_num = int(original_version.split("-")[-1]) + 1
    else:
        existing = list(Path(output_base).glob(f"{today}-*"))
        ver_num = len(existing) + 1

    version_id = f"{today}-{ver_num}"
    version_dir = Path(output_base) / version_id
    version_dir.mkdir(parents=True, exist_ok=True)

    # Save change description
    with open(version_dir / "CHANGE.md", "w", encoding="utf-8") as f:
        f.write("# Class Model Change Record\n\n")
        f.write(f"## Change Request\n{change_request}\n\n")
        f.write("## Change Types\n- Class list changes\n- Attribute changes\n- Method changes\n- Relationship changes\n")
        if original_version:
            f.write(f"\n**Baseline Version**: {os.path.basename(original_version)}")

    # Save structured results
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
    """Save class model artifacts (added null handling)"""

    output_dir.mkdir(parents=True, exist_ok=True)

    # Class list
    with open(output_dir / "classes.md", "w", encoding="utf-8") as f:
        f.write("# Class List\n\n")
        for cls in classes or []:  
            f.write(f"## {cls}\n- Type: Business Entity\n- Associated Requirement: {background}\n\n")

    with open(output_dir / "attributes.md", "w", encoding="utf-8") as f:
        f.write("# Class Attributes\n\n")
        for attr in attributes:
            if '.' in attr:
                cls, field = attr.split('.', 1)
                f.write(f"* {cls}.{field}\n  - Type: String\n  - Constraint: Required\n\n")

        # Save methods
    with open(output_dir / "methods.md", "w", encoding="utf-8") as f:
        f.write("# Class Methods\n\n")
        for method in methods:
            if '.' in method:
                cls, func = method.split('.', 1)
                f.write(f"* {cls}.{func}\n  - Visibility: public\n  - Complexity: 1\n\n")

        # Save relationships
    with open(output_dir / "relations.md", "w", encoding="utf-8") as f:
        f.write("# Class Relationships\n\n")
        for rel in relations:
            f.write(f"{rel}\n")


if __name__ == "__main__":

    try:
        # Test scenario: Payment system refactoring
        change1 = "1. Split Payment class into OnlinePayment and CashPayment\n2. Add calculateTax method to Order"
        classes, attrs, methods, rels = run_class_change_workflow(change1)
        print("First change results:")
        print(f"Class changes: added {classes.get('add', [])}, removed {classes.get('delete', [])}")

        # Second change test
        change2 = "Add currency attribute and validateCurrency() method to OnlinePayment"
        run_class_change_workflow(change2)
    except Exception as e:
        print(f"Workflow execution failed: {str(e)}")
        raise