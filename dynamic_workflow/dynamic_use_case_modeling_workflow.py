import json
import os
import glob
import re
from datetime import datetime
from typing import Tuple, List, Dict, Optional
from pathlib import Path

import agentscope
from agentscope.rag import KnowledgeBank
from agentscope.msghub import msghub
from agentscope.message import Msg

def run_change_workflow(
        change_request: str,
        knowledge_config: str = "../configs/uc_knowledge.json",
        model_base: str = "../workflow/versions"
) -> Tuple[List[str], Dict[str, List[str]], Dict[str, List[str]]]:
    agents = agentscope.init(
        model_configs="G:\\PycharmProjects\\UMLGenerator\\configs\\model_configs.json",
        agent_configs="G:\\PycharmProjects\\UMLGenerator\\configs\\dynamic_usecase_agent_configs.json"
    )
    latest_version = _find_latest_version(model_base)
    original_data = _load_existing_model(latest_version) if latest_version else None
    knowledge_bank = KnowledgeBank(configs=knowledge_config)
    knowledge_bank.equip(agents[0], ["uc_change_rules"])
    knowledge_bank.equip(agents[0], ["actor_rules"])
    knowledge_bank.equip(agents[1], ["uc_rules"])
    knowledge_bank.equip(agents[2], ["uc_rel_rules"])
    with msghub(agents) as hub:
        hub.broadcast(Msg("Host", "Start change modeling process", role="system"))
        hub.broadcast(Msg("Host", f"Change request: {change_request}", role="user"))
        if original_data:
            new_actors = agents[0].get_final_actors(original_data["actors"], change_request)
        else:
            new_actors = agents[0].get_final_actors(change_request)
        hub.broadcast(Msg("ActorAgent", json.dumps(new_actors, ensure_ascii=False), role="assistant"))
        if original_data:
            changed_cases = agents[1].get_final_use_cases(original_data["use_cases"], change_request)
        else:
            changed_cases = agents[1].get_final_use_cases(change_request)
        hub.broadcast(Msg("UseCaseAgent", json.dumps(changed_cases, ensure_ascii=False), role="assistant"))
        original_relations = original_data["relationships"] if original_data else []
        changed_relations = agents[2].get_final_relations(
            original_relations,
            new_actors,
            change_request
        )
        hub.broadcast(Msg("RelAgent", json.dumps(changed_relations, ensure_ascii=False), role="assistant"))
    final_model = _merge_changes(
        original_data,
        new_actors,
        changed_cases,
        changed_relations
    )
    version_dir = _save_versioned_results(
        change_request=change_request,
        final_model=final_model,
        original_version=latest_version,
        output_base=model_base
    )
    print(f"\nChange results saved to: {version_dir}")
    return new_actors, changed_cases, changed_relations


def _find_latest_version(base_dir: str) -> Optional[str]:
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


def _load_existing_model(version_dir: str) -> Dict:
    model_data = {
        "actors": [],
        "use_cases": [],
        "relationships": []
    }
    actors_path = Path(version_dir) / "actors.md"
    if actors_path.exists():
        with open(actors_path, 'r', encoding='utf-8') as f:
            content = f.read()
            model_data["actors"] = list(set(
                re.findall(r"Name:\s*(.+?)\s*\n", content)
            ))
    use_cases_path = Path(version_dir) / "use_cases.md"
    if use_cases_path.exists():
        with open(use_cases_path, 'r', encoding='utf-8') as f:
            content = f.read()
            model_data["use_cases"] = list(set(
                re.findall(r"Name:\s*(.+?)\s*\n", content)
            ))
    rel_path = Path(version_dir) / "relationships.md"
    if rel_path.exists():
        with open(rel_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith("|") and "->" in line:
                    parts = [p.strip() for p in line.split("|") if p.strip()]
                    if len(parts) >= 3:
                        model_data["relationships"].append(
                            f"{parts[0]}->{parts[2]}"
                        )
    return model_data


def _merge_changes(
        original: Optional[Dict],
        new_actors: List[str],
        changed_cases: Dict[str, List[str]],
        changed_relations: Dict[str, List[str]]
) -> Dict:
    final_actors = list(set(new_actors))
    original_cases = original["use_cases"] if original else []
    final_cases = list(set(original_cases + changed_cases["added"]))
    final_cases = [uc for uc in final_cases if uc not in changed_cases["removed"]]
    original_rels = original["relationships"] if original else []
    final_rels = list(set(original_rels + changed_relations["added"]))
    final_rels = [r for r in final_rels if r not in changed_relations["removed"]]
    for modified in changed_relations["modified"]:
        if modified in final_rels:
            final_rels.remove(modified)
        final_rels.append(modified.split("->")[0] + "->" + modified.split("->")[1])
    return {
        "actors": final_actors,
        "use_cases": final_cases,
        "relationships": list(set(final_rels))
    }


def _save_versioned_results(
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
    with open(version_dir / "CHANGE.md", 'w', encoding='utf-8') as f:
        f.write("# Change Log\n\n")
        f.write(f"## Change Request\n{change_request}\n\n")
        f.write("## Change Types\n")
        f.write("- Actor Changes\n- Use Case Changes\n- Relationship Changes\n\n")
        if original_version:
            f.write(f"**Baseline Version**: {os.path.basename(original_version)}\n")
    _save_structured_results(
        background=change_request,
        actors=final_model["actors"],
        use_cases=final_model["use_cases"],
        relationships=final_model["relationships"],
        output_dir=version_dir
    )
    return str(version_dir)


def _save_structured_results(
        background: str,
        actors: List[str],
        use_cases: List[str],
        relationships: List[str],
        output_dir: Path
) -> None:
    with open(output_dir / "actors.md", 'w', encoding='utf-8') as f:
        f.write("# Actor List\n\n")
        for actor in actors:
            f.write(f"## {actor}\n")
            f.write(f"- Name: {actor}\n")
            f.write(f"- Type: Business Role\n")
            f.write(f"- Associated Requirement: {background}\n\n")
    with open(output_dir / "use_cases.md", 'w', encoding='utf-8') as f:
        f.write("# Use Case List\n\n")
        for uc in use_cases:
            f.write(f"## {uc}\n")
            f.write(f"- Name: {uc}\n")
            f.write("- Type: System Function\n")
            f.write(f"- Associated Requirement: {background}\n\n")
    with open(output_dir / "relationships.md", 'w', encoding='utf-8') as f:
        f.write("# Relationship Matrix\n\n")
        f.write("| Subject | Relation Type | Object | Associated Requirement |\n")
        f.write("|---------|---------------|--------|-------------------------|\n")
        seen = set()
        for rel in relationships:
            if "->" in rel:
                subject, obj = rel.split("->", 1)
                rel_hash = f"{subject.strip()}->{obj.strip()}"
                if rel_hash not in seen:
                    f.write(f"| {subject.strip()} | Association | {obj.strip()} | {background} |\n")
                    seen.add(rel_hash)


if __name__ == "__main__":
    test_change = "Add WeChat Pay channel and remove bank card payment"
    print("First change test:")
    actors_v1, cases_v1, rels_v1 = run_change_workflow(test_change)
    print("\nSecond change test:")
    test_change_v2 = "Add points redemption feature"
    actors_v2, cases_v2, rels_v2 = run_change_workflow(test_change_v2)
    print("\nVersion 1 actors:", actors_v1)
    print("Version 1 use case changes:", cases_v1)
    print("Version 2 relationship changes:", rels_v2)