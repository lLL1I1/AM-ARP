# -*- coding: utf-8 -*-
"""Class Diagram Reflection Workflow with Structured Output"""
import json
from typing import List, Dict, Tuple




class ClassDiagramEvaluator:
    """评估类图模型的正确性和逻辑一致性"""

    def evaluate_classes(self, generated_classes: List[str], correct_classes: List[str]) -> float:
        """评估类的正确性：正确类数量 / 总生成类数量"""
        correct_count = len(set(generated_classes) & set(correct_classes))
        return correct_count / len(generated_classes) if generated_classes else 0

    def evaluate_attributes(self, generated_attributes: Dict[str, List[str]], correct_attributes: Dict[str, List[str]]) -> float:
        """评估属性的正确性：正确属性数量 / 总生成属性数量"""
        total_correct = 0
        total_generated = 0
        for class_name, attrs in generated_attributes.items():
            if class_name in correct_attributes:
                correct_count = len(set(attrs) & set(correct_attributes[class_name]))
                total_correct += correct_count
                total_generated += len(attrs)
        return total_correct / total_generated if total_generated > 0 else 0

    def evaluate_functions(self, generated_functions: Dict[str, List[str]], correct_functions: Dict[str, List[str]]) -> float:
        """评估方法的正确性：正确方法数量 / 总生成方法数量"""
        total_correct = 0
        total_generated = 0
        for class_name, funcs in generated_functions.items():
            if class_name in correct_functions:
                correct_count = len(set(funcs) & set(correct_functions[class_name]))
                total_correct += correct_count
                total_generated += len(funcs)
        return total_correct / total_generated if total_generated > 0 else 0

    def evaluate_relationships(self, generated_relationships: List[str], correct_relationships: List[str]) -> float:
        """评估关系的逻辑一致性：正确关系数量 / 总生成关系数量"""
        correct_count = sum(1 for rel in generated_relationships if rel in correct_relationships)
        return correct_count / len(generated_relationships) if generated_relationships else 0