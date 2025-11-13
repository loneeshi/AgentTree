# Enhanced Knowledge Graph Builder

一个高质量的知识图谱构建工具，使用先进的深度学习模型从非结构化文本中自动抽取实体和关系。

## 特性

### 🚀 核心功能

1. **命名实体识别 (NER)**: 使用 `dslim/bert-base-NER` 模型识别人名、组织、地点等实体
2. **关系抽取 (RE)**: 使用 `Babelscape/rebel-large` 模型抽取实体间的语义关系
3. **智能后处理**: 自动清洗、过滤和标准化抽取结果

### ✨ 改进点

相比基础版本，增强版包含以下改进:

#### 1. 文本预处理 (`text_preprocessing.py`)
- 去除页眉、页脚、页码等噪音
- 清理 URL、邮箱等无关信息
- 过滤无意义的句子（如目录、索引）
- 标准化格式和空白字符

#### 2. 实体后处理 (`entity_postprocessing.py`)
- **合并破碎实体**: 自动合并被 tokenizer 分割的实体（如 `Control` + `##logy` → `Controllogy`）
- **去重**: 智能去重，保留最具体的实体类型
- **过滤噪音**: 移除无意义的实体（如单个字母、纯数字、常见词等）
- **标准化**: 统一实体的文本格式

#### 3. 关系后处理 (`relation_postprocessing.py`)
- **关系标准化**: 将多种表达映射到标准关系类型（如 `part of`, `component of` → `part_of`）
- **三元组验证**: 过滤无效的关系（如自环、空值）
- **去重**: 移除重复的三元组
- **噪音过滤**: 移除文档结构相关的无意义关系

#### 4. 可配置的关系模式 (`config.py`)
预定义了领域标准关系，包括：
- 分类关系: `is_a`, `subclass_of`
- 部分-整体关系: `part_of`, `has_part`
- 功能关系: `used_for`, `connects_with`
- 比较关系: `different_from`, `similar_to`
- 时序关系: `followed_by`, `follows`
- 归因关系: `based_on`, `operates`

## 安装

### 1. 安装依赖

```bash
cd AgentTree/kg_builder
pip install -r requirements.txt
```

### 2. 下载 spaCy 模型

```bash
python -m spacy download en_core_web_sm
```

## 使用方法

### 基本使用

```bash
cd AgentTree
python kg_builder/main.py
```

脚本会：
1. 读取 `texts/` 目录下的所有 `.txt` 文件
2. 对每个文件进行知识抽取和后处理
3. 将结果保存到 `output/knowledge_graph_enhanced.json`

### 配置选项

在 `main.py` 中可以修改以下配置：

```python
# 是否启用严格的关系过滤（只保留预定义的标准关系）
USE_STRICT_FILTERING = False  # 设为 True 可获得更干净但可能更少的关系
```

在 `config.py` 中可以：
- 添加或修改标准关系定义
- 调整实体/关系的过滤规则
- 设置最小实体长度等参数

## 输出格式

生成的 JSON 文件结构如下：

```json
{
  "filename.txt": {
    "entities": [
      {
        "text": "Apple",
        "type": "ORG",
        "start": 0,
        "end": 5
      }
    ],
    "relations": [
      {
        "subject": "Apple",
        "relation": "headquartered_in",
        "object": "Cupertino"
      }
    ],
    "statistics": {
      "total_entities": 50,
      "total_relations": 30,
      "entity_types": {
        "ORG": 20,
        "PER": 15,
        "LOC": 10,
        "MISC": 5
      },
      "relation_types": {
        "part_of": 10,
        "is_a": 8,
        "used_for": 5
      }
    }
  }
}
```

## 文件说明

| 文件 | 功能 |
|------|------|
| `main.py` | 主程序入口，协调整个流程 |
| `ner.py` | 命名实体识别模块 |
| `relation_extraction.py` | 关系抽取模块 |
| `text_preprocessing.py` | 文本预处理模块 |
| `entity_postprocessing.py` | 实体后处理模块 |
| `relation_postprocessing.py` | 关系后处理模块 |
| `config.py` | 配置文件（关系模式、过滤规则等） |
| `requirements.txt` | Python 依赖列表 |

## 性能说明

- **处理速度**: 由于使用了大型深度学习模型，处理速度较慢。一个中等大小的文档（约100句话）可能需要几分钟。
- **首次运行**: 第一次运行时会自动从 Hugging Face Hub 下载模型（约 1-2 GB），需要稳定的网络连接。
- **内存需求**: 建议至少 8GB RAM，GPU 可显著加速（但不是必需的）。

## 后续改进方向

1. **实体链接**: 将抽取的实体链接到知识库（如 Wikidata），解决实体消歧问题
2. **领域微调**: 在特定领域语料上微调 NER 和 RE 模型，提升准确率
3. **LLM 集成**: 使用大语言模型（GPT-4 等）进行端到端抽取或结果校验
4. **增量更新**: 支持增量式知识图谱构建，而不是每次从头开始
5. **可视化**: 添加知识图谱可视化功能

## 常见问题

**Q: 为什么实体中还是有一些 `##` 符号？**
A: 这可能是因为某些极端情况下的 tokenization 问题。可以在 `entity_postprocessing.py` 中增强 `merge_subword_entities` 函数的逻辑。

**Q: 如何添加自定义的关系类型？**
A: 编辑 `config.py` 中的 `STANDARD_RELATIONS` 字典，添加你需要的关系及其变体。

**Q: 抽取的关系质量还是不理想怎么办？**
A: 可以将 `USE_STRICT_FILTERING` 设为 `True` 只保留标准关系，或者考虑使用 LLM 进行二次校验。

## 许可证

本项目仅供研究和学习使用。

## 作者

AgentTree Knowledge Graph Builder Team
