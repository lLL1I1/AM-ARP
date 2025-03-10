# -*- coding: utf-8 -*-
"""Sequence Diagram Reflection Workflow with Structured Output"""
import json
from typing import List, Dict, Tuple

from agents.sequence_generator.object_identifier import ObjectIdentifier
from agents.sequence_generator.message_identifier import MessageIdentifier
from agents.sequence_generator.message_order_identifier import MessageOrderIdentifier
from agentscope.message import Msg


class SequenceDiagramEvaluator:
    """评估顺序图模型的正确性和逻辑一致性"""

    def evaluate_objects(self, generated_objects: List[str], correct_objects: List[str]) -> float:
        """评估对象的正确性：正确对象数量 / 总生成对象数量"""
        correct_count = len(set(generated_objects) & set(correct_objects))
        return correct_count / len(generated_objects) if generated_objects else 0

    def evaluate_messages(self, generated_messages: List[str], correct_messages: List[str]) -> float:
        """评估消息的正确性：正确消息数量 / 总生成消息数量"""
        correct_count = sum(1 for msg in generated_messages if msg in correct_messages)
        return correct_count / len(generated_messages) if generated_messages else 0

    def evaluate_sequence(self, generated_sequence: List[str], correct_sequence: List[str]) -> float:
        """评估消息时序的正确性：正确时序数量 / 总生成时序数量"""
        correct_count = sum(1 for gen, cor in zip(generated_sequence, correct_sequence) if gen == cor)
        return correct_count / len(generated_sequence) if generated_sequence else 0