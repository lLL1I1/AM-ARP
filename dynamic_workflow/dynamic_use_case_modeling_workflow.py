# File: workflows/change_use_case_modeling.py
"""RAG-enhanced Change Workflow"""
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
    """变更用例建模工作流"""

    # 初始化变更处理智能体        修改这个代码，model_base应该是原有模型的文件夹才对，然后读取文件夹的内容，里面有actors.md、use_case.md、relationship.md、requirement.md,这个是代表原有用例模型的内容及需求
    agents = agentscope.init(
        model_configs = "G:\\PycharmProjects\\UMLGenerator\\configs\\model_configs.json",
        agent_configs = "G:\\PycharmProjects\\UMLGenerator\\configs\\dynamic_usecase_agent_configs.json"
    )

    # 加载现有最新模型
    latest_version = _find_latest_version(model_base)
    original_data = _load_existing_model(latest_version) if latest_version else None

    # 初始化知识库
    knowledge_bank = KnowledgeBank(configs=knowledge_config)
    knowledge_bank.equip(agents[0], ["uc_change_rules"])  # 变更模式库
    knowledge_bank.equip(agents[0], ["actor_rules"])  # 参与者规则
    knowledge_bank.equip(agents[1], ["uc_rules"])  # 用例规则
    knowledge_bank.equip(agents[2], ["uc_rel_rules"])  # 关系规则

    # 执行变更流程
    with msghub(agents) as hub:
        hub.broadcast(Msg("Host", "启动变更建模流程", role="system"))
        hub.broadcast(Msg("Host", f"变更请求：{change_request}", role="user"))

        # 步骤1：参与者变更
        if original_data:
            new_actors = agents[0].get_final_actors(original_data["actors"], change_request)  # 存在原有内容
        else:
            new_actors = agents[0].get_final_actors(change_request)
        hub.broadcast(Msg("ActorAgent", json.dumps(new_actors, ensure_ascii=False), role="assistant"))

        # 步骤2：用例变更
        if original_data:
            changed_cases = agents[1].get_final_use_cases(original_data["use_cases"], change_request)
        else:
            changed_cases = agents[1].get_final_use_cases(change_request)
        hub.broadcast(Msg("UseCaseAgent", json.dumps(changed_cases, ensure_ascii=False), role="assistant"))

        # 步骤3：关系变更
        original_relations = original_data["relationships"] if original_data else []
        changed_relations = agents[2].get_final_relations(
            original_relations,
            new_actors,
            change_request
        )
        hub.broadcast(Msg("RelAgent", json.dumps(changed_relations, ensure_ascii=False), role="assistant"))

    # 生成最终模型（合并变更）
    final_model = _merge_changes(
        original_data,
        new_actors,
        changed_cases,
        changed_relations
    )

    # 版本化存储
    version_dir = _save_versioned_results(
        change_request=change_request,
        final_model=final_model,
        original_version=latest_version,
        output_base=model_base
    )

    print(f"\n变更结果已保存至：{version_dir}")
    return new_actors, changed_cases, changed_relations


def _find_latest_version(base_dir: str) -> Optional[str]:
    """查找最新版本目录"""
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

    # 按日期和版本号排序
    version_dirs.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return str(version_dirs[0][2])


def _load_existing_model(version_dir: str) -> Dict:
    """加载指定版本的模型数据"""
    model_data = {
        "actors": [],
        "use_cases": [],
        "relationships": []
    }

    # 解析参与者
    actors_path = Path(version_dir) / "actors.md"
    if actors_path.exists():
        with open(actors_path, 'r', encoding='utf-8') as f:
            content = f.read()
            model_data["actors"] = list(set(
                re.findall(r"名称:\s*(.+?)\s*\n", content)
            ))

    # 解析用例
    use_cases_path = Path(version_dir) / "use_cases.md"
    if use_cases_path.exists():
        with open(use_cases_path, 'r', encoding='utf-8') as f:
            content = f.read()
            model_data["use_cases"] = list(set(
                re.findall(r"名称:\s*(.+?)\s*\n", content)
            ))

    # 解析关系
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
    """合并变更到现有模型"""
    # 合并参与者
    final_actors = list(set(new_actors))  # 去重

    # 合并用例
    original_cases = original["use_cases"] if original else []
    final_cases = list(set(original_cases + changed_cases["新增"]))
    final_cases = [uc for uc in final_cases if uc not in changed_cases["删除"]]

    # 合并关系
    original_rels = original["relationships"] if original else []
    final_rels = list(set(original_rels + changed_relations["新增"]))
    final_rels = [r for r in final_rels if r not in changed_relations["删除"]]

    # 应用修改
    for modified in changed_relations["修改"]:
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
    """版本化存储变更结果"""
    # 确定新版本号
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
    with open(version_dir / "CHANGE.md", 'w', encoding='utf-8') as f:
        f.write("# 变更记录\n\n")
        f.write(f"## 变更请求\n{change_request}\n\n")
        f.write("## 变更类型\n")
        f.write("- 参与者变更\n- 用例变更\n- 关系变更\n\n")
        if original_version:
            f.write(f"**基线版本**: {os.path.basename(original_version)}\n")

    # 保存结构化结果
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
    """保存结构化结果到指定目录"""
    # 保存参与者
    with open(output_dir / "actors.md", 'w', encoding='utf-8') as f:
        f.write("# 参与者列表\n\n")
        for actor in actors:
            f.write(f"## {actor}\n")
            f.write(f"- 名称: {actor}\n")
            f.write(f"- 类型: 业务角色\n")
            f.write(f"- 关联需求: {background}\n\n")

    # 保存用例
    with open(output_dir / "use_cases.md", 'w', encoding='utf-8') as f:
        f.write("# 用例列表\n\n")
        for uc in use_cases:
            f.write(f"## {uc}\n")
            f.write(f"- 名称: {uc}\n")
            f.write("- 类型: 系统功能\n")
            f.write(f"- 关联需求: {background}\n\n")

    # 保存关系
    with open(output_dir / "relationships.md", 'w', encoding='utf-8') as f:
        f.write("# 关系矩阵\n\n")
        f.write("| 主体 | 关系类型 | 客体 | 关联需求 |\n")
        f.write("|------|---------|------|----------|\n")
        seen = set()
        for rel in relationships:
            if "->" in rel:
                subject, obj = rel.split("->", 1)
                rel_hash = f"{subject.strip()}->{obj.strip()}"
                if rel_hash not in seen:
                    f.write(f"| {subject.strip()} | 关联 | {obj.strip()} | {background} |\n")
                    seen.add(rel_hash)


if __name__ == "__main__":
    # 测试用例
    test_change = "新增微信支付渠道并移除银行卡支付"

    # 首次运行（无基线版本）
    print("首次变更测试:")
    actors_v1, cases_v1, rels_v1 = run_change_workflow(test_change)

    # 二次变更
    print("\n二次变更测试:")
    test_change_v2 = "增加积分兑换功能"
    actors_v2, cases_v2, rels_v2 = run_change_workflow(test_change_v2)

    # 显示结果
    print("\n版本1参与者:", actors_v1)
    print("版本1用例变更:", cases_v1)
    print("版本2关系变更:", rels_v2)