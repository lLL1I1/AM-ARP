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
from docx import Document  # Import python-docx library
import utils.util_function as uf

def run_use_case_workflow(
        background: str,
        knowledge_config: str = "../configs/uc_knowledge.json"
) -> Tuple[List[str], List[str], List[str]]:
    """Knowledge-enhanced use case modeling workflow"""

    # Initialize agent
    agents = agentscope.init(
        model_configs="G:\\PycharmProjects\\UMLGenerator\\configs\\model_configs.json",
        agent_configs="G:\\PycharmProjects\\UMLGenerator\\configs\\usecase_agent_configs.json"
    )

    # Initialize knowledge base
    knowledge_bank = KnowledgeBank(configs=knowledge_config)

    # Equip knowledge base
    knowledge_bank.equip(agents[0], ["actor_rules"])
    knowledge_bank.equip(agents[1], ["uc_rules"])
    knowledge_bank.equip(agents[2], ["uc_rel_rules"])

    # Execute collaboration process
    with msghub(agents) as hub:
        hub.broadcast(Msg("Host", "Initiate use case modeling process", role="system"))
        hub.broadcast(Msg("Host", f"Input background: {background}", role="user"))

        # Actor identification
        actors = agents[0].identify_actors(background)
        hub.broadcast(Msg("ActorAgent", json.dumps(actors, ensure_ascii=False), role="assistant"))

        # Use case identification
        use_cases = agents[1].identify_use_cases(background)
        hub.broadcast(Msg("UseCaseAgent", json.dumps(use_cases, ensure_ascii=False), role="assistant"))

        # Relationship identification
        relationships = agents[2].identify_relationships(
            use_cases,
            actors,
            background
        )
        hub.broadcast(Msg("RelAgent", json.dumps(relationships, ensure_ascii=False), role="assistant"))

    # Structured saving of results
    version_dir = _save_structured_results(
        background=background,
        actors=actors,
        use_cases=use_cases,
        relationships=relationships
    )

    print(f"\nGenerated results have been versioned and saved in directory: {version_dir}")

    return actors, use_cases, relationships


def _save_structured_results(
        background: str,
        actors: List[str],
        use_cases: List[str],
        relationships: List[str],
        output_base: str = "versions"
) -> str:
    """Structured saving of use case model results into versioned Markdown files"""
    # Create base directory
    os.makedirs(output_base, exist_ok=True)

    # Generate version number (date-sequence)
    today = datetime.now().strftime("%Y-%m-%d")
    existing_versions = glob.glob(os.path.join(output_base, f"{today}-*"))
    version_num = len(existing_versions) + 1
    version_id = f"{today}-{version_num}"
    version_dir = os.path.join(output_base, version_id)
    os.makedirs(version_dir, exist_ok=True)

    # Save original requirements background
    with open(os.path.join(version_dir, "requirements.md"), 'w', encoding='utf-8') as f:
        f.write(f"# Original Requirements\n\n{background}\n")

    # Structured saving of actors
    with open(os.path.join(version_dir, "actors.md"), 'w', encoding='utf-8') as f:
        f.write("# Actors List\n\n")
        for idx, actor in enumerate(actors, 1):
            f.write(f"## Actor {idx}\n")
            f.write(f"- Name: {actor}\n")
            f.write(f"- Type: Business Role\n")
            f.write(f"- Related Requirements: {background}\n\n")

    # Structured saving of use cases
    with open(os.path.join(version_dir, "use_cases.md"), 'w', encoding='utf-8') as f:
        f.write("# Use Cases List\n\n")
        for idx, uc in enumerate(use_cases, 1):
            f.write(f"## Use Case {idx}\n")
            f.write(f"- Name: {uc}\n")
            f.write("- Type: System Functionality\n")
            f.write(f"- Related Requirements: {background}\n\n")

    # Structured saving of relationships
    with open(os.path.join(version_dir, "relationships.md"), 'w', encoding='utf-8') as f:
        f.write("# Relationship Matrix\n\n")
        f.write("| Subject | Relation Type | Object | Related Requirements |\n")
        f.write("|---------|---------------|--------|----------------------|\n")
        for rel in relationships:
            # Parse relationship expression (example format: User -> Browse Products)
            parts = re.split(r"\s*->\s*|\s*-->\s*", rel)
            if len(parts) == 2:
                subject, obj = parts
                f.write(f"| {subject} | Associated | {obj} | {background} |\n")
            else:
                f.write(f"| {rel} | Associated | System | {background} |\n")

    return version_dir


if __name__ == "__main__":
    file_path = "../data/case.docx"

    test_input = uf.read_docx(file_path)

    print('...........test input............:')
    print(test_input)

    actors, cases, rels = run_use_case_workflow(test_input)

    print("\nFinal generated results:")
    print("Actors:", actors)
    print("Use Cases:", cases)
    print("Relationships:", rels)
    print("Relationships:", rels)