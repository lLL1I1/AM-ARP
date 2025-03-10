from typing import List, Dict


class EvaluationModule:
    """评估类模块，包含单节点评估和逻辑一致性评估"""

    def evaluate_single_node(self, generated_elements: List[str], correct_elements: List[str]) -> float:
        """单节点评估：正确元素数量 / 所有生成元素数量"""
        correct_count = len(set(generated_elements) & set(correct_elements))
        return correct_count / len(generated_elements) if generated_elements else 0

    def evaluate_logical_consistency(self, relationships: List[str], actors: List[str], use_cases: List[str]) -> float:
        """逻辑一致性评估：符合逻辑的关系数量 / 总关系数量"""
        valid_count = 0
        for rel in relationships:
            parts = rel.split(" --")
            if len(parts) >= 2:
                left, right = parts[0], parts[1].split("--> ")[-1]
                if (left in actors or left in use_cases) and (right in actors or right in use_cases):
                    valid_count += 1
        return valid_count / len(relationships) if relationships else 0