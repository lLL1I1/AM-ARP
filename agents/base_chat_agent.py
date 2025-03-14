# -*- coding: utf-8 -*-
"""A base chat agent that extends DialogAgent."""
from typing import Optional

from loguru import logger
from agentscope.message import Msg
from agentscope.agents.dialog_agent import DialogAgent

class BaseChatAgent(DialogAgent):
    """A base chat agent used for specific dialogue tasks with contextual reflection capabilities."""

    def __init__(
            self,
            name: str,
            sys_prompt: str,
            model_config_name: str,
            use_memory: bool = True,
            memory_config: Optional[dict] = None,
    ) -> None:
        """Initialize the base chat agent.

        Arguments:
            name (`str`): The name of the agent.
            sys_prompt (`str`): The system prompt for the agent.
            model_config_name (`str`): The model configuration name.
            use_memory (`bool`, defaults to `True`): Whether the agent has memory.
            memory_config (`Optional[dict]`): Configuration for memory.
        """
        super().__init__(
            name=name,
            sys_prompt=sys_prompt,
            model_config_name=model_config_name,
            use_memory=use_memory,
            memory_config=memory_config,
        )

        self.context = []  # 额外上下文记录

    def set_context(self, context: list) -> None:
        """Update the context with the given information."""
        self.context = context

    def process_input(self, user_input: str) -> str:
        """Process user input and generate a response."""
        # 记录用户输入
        self.context.append({"role": "user", "content": user_input})
        # 调用父类的回复功能
        response = self.reply({"content": user_input})
        return response['content']  # 返回助手的输出内容

    def reflect_on_output(self, output: str) -> None:
        """Reflect on the generated output for further optimization."""
        logger.info(f"Reflected Output: {output}")

    def reply(self, x: dict = None) -> dict:
        """Override reply method to include context handling."""
        # 记录输入到内存（如果有内存）
        if self.memory:
            self.memory.add(x)

        # prepare prompt with added context
        prompt = self.model.format(
            Msg("system", self.sys_prompt, role="system"),
            self.memory.get_memory() if self.memory else x,
            *self.context  # 加入上下文
        )

        # 调用语言模型并生成响应
        response = self.model(prompt).text
        msg = Msg(self.name, response, role="assistant")

        # 以该智能体的声音打印/说出消息
        self.speak(msg)

        # 记录消息到内存
        if self.memory:
            self.memory.add(msg)

        return msg
