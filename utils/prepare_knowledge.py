# File: scripts/prepare_ucm_knowledge.py
import json
from pathlib import Path
from agentscope.rag import KnowledgeBank
from llama_index.core.node_parser import JSONParser  # 需要补充的依赖


def prepare_domain_knowledge():
    """构建用例建模知识库"""
    bank = KnowledgeBank()

    #参与者知识
    actor_texts = [
        "用户角色识别规则：当描述中出现'用户'、'客户'、'管理员'等身份称谓时，需识别为系统参与者"
        # "外部系统特征：若出现'调用XX接口'、'与XX系统对接'等描述，XX应识别为外部系统参与者"
    ]

    # 用例关系规则（示例文件路径）
    rule_files = [
        Path("data/rules/include_conditions.json"),
        Path("data/rules/extend_rules.json")
    ]

    # 添加知识
    bank.add_text_as_knowledge(
        knowledge_id="actor_knowledge",
        texts=actor_texts,
        emb_model_config_name="text_embedding_config"
    )

    bank.add_file_as_knowledge(
        knowledge_id="rel_rules",
        file_paths=rule_files,
        parser=JSONParser()  # 解析JSON格式规则
    )

    # 保存配置
    config_path = Path("configs/ucm_knowledge.json")
    config_path.parent.mkdir(exist_ok=True)
    bank.save_config(str(config_path))
    print(f"✅ 知识库配置已保存至 {config_path}")


if __name__ == "__main__":
    prepare_domain_knowledge()  # 添加执行入口