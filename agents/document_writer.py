from pathlib import Path
from tempfile import TemporaryDirectory

from docx import Document
import re
from typing import Dict, Any, List, Union
from agentscope.agents import LlamaIndexAgent
from agentscope.message import Msg


class DocumentWriter(LlamaIndexAgent):
    """需求规格说明书生成智能体"""

    def __init__(
            self,
            name: str,
            model_config_name: str,
            sys_prompt: str,
            knowledge_id_list: List[str],
            recent_n_mem_for_retrieve: int = 3,
    ) -> None:
        """
        初始化需求规格说明书生成智能体。

        :param name: 智能体名称
        :param model_config_name: 模型配置名称
        :param sys_prompt: 系统提示信息
        :param knowledge_id_list: 知识库ID列表
        :param recent_n_mem_for_retrieve: 最近记忆检索数量
        """
        sys_prompt = """## 需求规格说明书生成规则
            你是一个专业的需求规格说明书生成器，请根据用户输入和知识库中的规则：
            1. 根据已有的UML模型、需求分解表格和原始需求，生成需求规格说明书（SRS）。
            2. 如果知识库中缺少某些内容，则对应的部分留空白。
            3. 结果必须使用格式：```RESULT\n[章节]: [内容]\n...```"""
        super().__init__(
            name=name,
            sys_prompt=sys_prompt,
            model_config_name=model_config_name,
            knowledge_id_list=knowledge_id_list,
            similarity_top_k=3,
            recent_n_mem_for_retrieve=recent_n_mem_for_retrieve,
        )

    def reply(self, x: Union[Msg, List[Msg]]) -> Msg:
        """处理输入并返回响应"""
        # 提取输入内容
        query = self._extract_query(x)
        # 知识检索
        related_knowledge = self._retrieve_knowledge(query)
        # 构建提示
        full_prompt = (
            f"{self.sys_prompt}\n\n"
            f"[知识库内容]\n{related_knowledge}\n\n"
            f"[用户输入]\n{query}\n\n"
            "请按照规则生成需求规格说明书："
        )
        # 调用模型生成
        response_text = self.model(full_prompt).text
        return Msg(self.name, response_text, role="assistant")

    def generate_srs(self, input_data: str) -> Dict[str, Any]:
        """对外接口，生成需求规格说明书"""
        response = self.reply(Msg("user", input_data, role="user"))
        return self._parse_response(response.content)

    def _parse_response(self, content: str) -> Dict[str, Any]:
        """解析响应内容"""
        srs_content = {}
        if match := re.findall(r'```RESULT\n(.*?)\n```', content, re.DOTALL):
            for section in match:
                lines = [line.strip() for line in section.split('\n') if line.strip()]
                for line in lines:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        srs_content[key.strip()] = value.strip()
        return srs_content

    def save_to_doc(self, srs_content: Dict[str, Any], output_path: str) -> None:
        """将需求规格说明书保存为 .doc 文件"""
        doc = Document()

        # 添加业务层
        self._add_business_level(doc, srs_content)

        # 添加系统层
        self._add_system_level(doc, srs_content)

        # 添加附录
        self._add_appendixes(doc, srs_content)

        # 保存文件
        doc.save(output_path)
        print(f"需求规格说明书已生成并保存到 {output_path}")

    def _add_heading(self, doc: Document, text: str, level: int):
        """添加标题"""
        doc.add_heading(text, level=level)

    def _add_paragraph(self, doc: Document, text: str):
        """添加段落"""
        doc.add_paragraph(text)

    def _add_table(self, doc: Document, headers: List[str], rows: List[List[str]]):
        """添加表格"""
        table = doc.add_table(rows=len(rows) + 1, cols=len(headers))
        for i, header in enumerate(headers):
            table.cell(0, i).text = header
        for i, row in enumerate(rows):
            for j, cell_value in enumerate(row):
                table.cell(i + 1, j).text = str(cell_value)

    def _add_business_level(self, doc: Document, srs_content: Dict[str, Any]):
        """添加业务层内容"""
        self._add_heading(doc, "Chapter 1: 引言", level=1)

        # 1.1 Purpose 文档目的
        self._add_heading(doc, "1.1 文档目的", level=2)
        purpose = srs_content.get("1.1 文档目的", "")
        self._add_paragraph(doc, purpose if purpose else "未提供文档目的。")

        # 1.2 Glossary 术语表
        self._add_heading(doc, "1.2 术语表", level=2)
        glossary = srs_content.get("1.2 术语表", {})
        if glossary:
            headers = ["术语", "定义"]
            rows = [[term, definition] for term, definition in glossary.items()]
            self._add_table(doc, headers, rows)
        else:
            self._add_paragraph(doc, "未提供术语表。")

        # 1.3 Stakeholders 利益相关者模型
        self._add_heading(doc, "1.3 利益相关者模型", level=2)
        stakeholders = srs_content.get("1.3 利益相关者模型", "")
        self._add_paragraph(doc, stakeholders if stakeholders else "未提供利益相关者模型。")

        # 1.4 Goals 目标模型
        self._add_heading(doc, "1.4 目标模型", level=2)
        goals = srs_content.get("1.4 目标模型", "")
        self._add_paragraph(doc, goals if goals else "未提供目标模型。")

        # 1.7-1.8 参考文献与文档结构
        self._add_heading(doc, "1.7 参考文献", level=2)
        references = srs_content.get("1.7 参考文献", "")
        self._add_paragraph(doc, references if references else "未提供参考文献。")

        self._add_heading(doc, "1.8 文档结构", level=2)
        structure = srs_content.get("1.8 文档结构", "")
        self._add_paragraph(doc, structure if structure else "未提供文档结构描述。")

    def _add_system_level(self, doc: Document, srs_content: Dict[str, Any]):
        """添加系统层内容"""
        self._add_heading(doc, "Chapter 2: 系统概览", level=1)

        # 2.1 Context 上下文模型
        self._add_heading(doc, "2.1 上下文模型", level=2)
        context_model = srs_content.get("2.1 上下文模型", "")
        self._add_paragraph(doc, context_model if context_model else "未提供上下文模型。")

        # 2.3 Assumptions 假设
        self._add_heading(doc, "2.3 假设", level=2)
        assumptions = srs_content.get("2.3 假设", "")
        self._add_paragraph(doc, assumptions if assumptions else "未提供假设。")

        # 2.4 Constraints 约束
        self._add_heading(doc, "2.4 约束", level=2)
        constraints = srs_content.get("2.4 约束", "")
        self._add_paragraph(doc, constraints if constraints else "未提供约束。")

        # Chapters 3~N-1: 子系统描述
        subsystems = srs_content.get("子系统描述", [])
        if subsystems:
            for i, subsystem in enumerate(subsystems, start=1):
                self._add_heading(doc, f"Chapter 3.{i}: 子系统描述", level=1)
                self._add_heading(doc, f"3.{i}.1 信息实体", level=2)
                entities = subsystem.get("信息实体", "")
                self._add_paragraph(doc, entities if entities else "未提供信息实体。")

                self._add_heading(doc, f"3.{i}.2 参与者", level=2)
                actors = subsystem.get("参与者", "")
                self._add_paragraph(doc, actors if actors else "未提供参与者。")

                self._add_heading(doc, f"3.{i}.3 功能需求", level=2)
                frs = subsystem.get("功能需求", "")
                self._add_paragraph(doc, frs if frs else "未提供功能需求。")

                self._add_heading(doc, f"3.{i}.4 用例", level=2)
                use_cases = subsystem.get("用例", "")
                self._add_paragraph(doc, use_cases if use_cases else "未提供用例。")

                self._add_heading(doc, f"3.{i}.5 子系统级NFRs", level=2)
                nfrs = subsystem.get("子系统级NFRs", "")
                self._add_paragraph(doc, nfrs if nfrs else "未提供子系统级非功能性需求。")

        # Chapter N: 全局非功能性需求
        self._add_heading(doc, "Chapter N: 全局非功能性需求", level=1)
        global_nfrs = srs_content.get("全局非功能性需求", "")
        self._add_paragraph(doc, global_nfrs if global_nfrs else "未提供全局非功能性需求。")

        # Chapter N+1: 关注点整合
        self._add_heading(doc, "Chapter N+1: 关注点整合", level=1)
        concerns = srs_content.get("关注点整合", "")
        self._add_paragraph(doc, concerns if concerns else "未提供关注点整合内容。")

    def _add_appendixes(self, doc: Document, srs_content: Dict[str, Any]):
        """添加附录内容"""
        self._add_heading(doc, "附录", level=1)

        # 文档版本
        self._add_heading(doc, "A. 文档版本", level=2)
        versions = srs_content.get("文档版本", "")
        self._add_paragraph(doc, versions if versions else "未提供文档版本信息。")

        # 需求追踪矩阵
        self._add_heading(doc, "B. 需求追踪矩阵", level=2)
        traceability_matrix = srs_content.get("需求追踪矩阵", [])
        if traceability_matrix:
            headers = ["需求编号", "需求描述", "测试用例", "状态"]
            rows = [
                [item["id"], item["description"], item["test_case"], item["status"]]
                for item in traceability_matrix
            ]
            self._add_table(doc, headers, rows)
        else:
            self._add_paragraph(doc, "未提供需求追踪矩阵。")


if __name__ == "__main__":
    ##############################################
    # 示例运行（功能测试）
    ##############################################
    print("\n" + "=" * 50)
    print("开始执行需求规格说明书生成示例...")

    # 初始化生成器
    test_writer = DocumentWriter(
        name="示例生成器",
        model_config_name="dummy_model",
        sys_prompt="测试用提示词",
        knowledge_id_list=["sample_knowledge"],
    )

    # 示例输入数据
    sample_input = """
    [用户需求]
    1. 需要用户登录功能
    2. 支持文件上传

    [UML模型]
    类图:
    - User: username, password
    - File: name, size

    [需求分解表]
    FR-001: 用户登录认证
    NFR-001: 文件上传响应时间小于3秒
    """

    # 生成需求规格说明书
    print("\n生成需求规格说明书内容...")
    srs_content = test_writer.generate_srs(sample_input)

    # 打印生成结果
    print("\n生成结果解析:")
    for section, content in srs_content.items():
        print(f"{section}: {content[:50]}...")  # 显示前50字符避免过长

    # 保存测试文档
    with TemporaryDirectory() as tmp_dir:
        output_path = Path(tmp_dir) / "示例文档.docx"
        test_writer.save_to_doc(srs_content, str(output_path))
        print(f"\n文档保存验证: {output_path.exists()}")
