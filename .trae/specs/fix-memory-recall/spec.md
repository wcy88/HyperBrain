# HyperBrain 长期记忆检索问题修复规格说明书

## Why
用户反馈"还是记不住，是不是记忆索引没有导致的"。截图证据：
- 长期记忆总记忆数：2646（数据已存在）
- 索引状态：**未构建**（用户圈出）
- 对话测试 "你是谁"+"看看记忆系统" — AI 没有展示出对之前对话的记忆
- faiss 模块未安装（`ModuleNotFoundError: No module named 'faiss'`）

经代码审查发现根本原因：
1. `memory_utils.py` 的 `generate_random_embedding()` 使用 `np.random.randn(dim)` 生成**完全随机**的归一化向量作为记忆的嵌入表示
2. 由于每次调用都返回不同的随机向量，相似度搜索（cosine similarity）实际上是**随机匹配**
3. 长期记忆已有 2646 条数据，但因为嵌入是随机的，检索出的"相关记忆"与真实语义无关
4. FAISS 未安装 → `enable_faiss=False` → 索引状态显示"未构建"
5. 即便 FAISS 可用，因为嵌入是随机的，FAISS 加速搜索的结果仍然是随机的

记忆系统的整个检索链路都建立在错误的随机向量之上，导致 AI 完全"记不住"任何上下文。

## What Changes
- **核心修复**：在 `memory_utils.py` 中新增 `generate_text_embedding()` 函数，使用**确定性**的文本特征哈希（字符 n-gram + 词袋）生成语义一致的嵌入向量
- **核心修复**：在 `memory_manager.py` 中将 `generate_random_embedding` 替换为 `generate_text_embedding` 作为默认嵌入生成器
- **核心修复**：在 `long_term_memory.py` 的 `store()` 和 `search_by_embedding()` 中，使用 `generate_text_embedding` 处理文本内容
- **兼容性修复**：保留 `generate_random_embedding` 函数以备后用，但添加弃用警告
- **UI 修复**：当 `enable_faiss=False` 但 `long_term_memory.get_stats()["total_memories"] > 0` 时，将索引状态显示为"已构建（暴力搜索）"
- **可选**：在 `requirements.txt` 中添加 `faiss-cpu`（用户可选安装以获得更快的检索速度）
- **验证**：编写并运行端到端测试，验证"添加记忆 → 检索相似记忆 → 包含相关内容"的全链路

## Impact
- Affected specs: 记忆层、UI 记忆面板、对话系统、模型调用链
- Affected code:
  - `hyperbrain/layers/memory/memory_utils.py`（新增 `generate_text_embedding`）
  - `hyperbrain/layers/memory/memory_manager.py`（替换默认嵌入生成器）
  - `hyperbrain/layers/memory/long_term_memory.py`（使用确定性嵌入）
  - `hyperbrain/ui/memory_viz.py`（改进索引状态显示）
  - `requirements.txt`（添加可选的 faiss-cpu）
- 涉及系统：嵌入向量生成、相似度检索、记忆持久化、UI 状态显示

## ADDED Requirements
### Requirement: 确定性文本嵌入生成
系统SHALL使用基于文本特征的确定性哈希算法生成嵌入向量，确保相同/相似文本产生相同/相似的向量表示。

#### Scenario: 相同文本生成相同向量
- **WHEN** 对同一文本调用 `generate_text_embedding()` 两次
- **THEN** 返回完全相同的嵌入向量

#### Scenario: 相似文本生成相似向量
- **WHEN** 对"今天天气真好"和"今天天气不错"调用 `generate_text_embedding()`
- **THEN** 余弦相似度 > 0.5（明显高于不相关文本的相似度）

#### Scenario: 不相关文本生成不相似向量
- **WHEN** 对"今天天气真好"和"Python 编程"调用 `generate_text_embedding()`
- **THEN** 余弦相似度 < 0.3

### Requirement: 记忆检索准确性
系统SHALL能在长期记忆库中检索出语义相关的历史记忆。

#### Scenario: 添加记忆后立即可检索
- **WHEN** 存储记忆 "项目使用 PyQt6 构建界面"
- **AND** 用查询 "界面用什么框架" 进行检索
- **THEN** 检索结果中包含 "PyQt6" 相关记忆且排名靠前

#### Scenario: 跨会话记忆检索
- **WHEN** 在会话 A 存储记忆 "我叫张三"
- **AND** 在会话 B 用查询 "我叫什么名字" 进行检索
- **THEN** 能检索到会话 A 中存储的 "我叫张三" 记忆

### Requirement: 索引状态正确显示
系统SHALL在记忆面板中正确显示索引状态，反映实际的检索能力。

#### Scenario: 暴力索引已构建
- **WHEN** 长期记忆中有数据（total_memories > 0）
- **AND** `enable_faiss=False`（使用暴力搜索）
- **THEN** 索引状态显示"已构建（暴力搜索）"或类似表述

#### Scenario: FAISS 索引已构建
- **WHEN** `enable_faiss=True` 且 FAISS 模块可用
- **THEN** 索引状态显示"已构建（FAISS）"

### Requirement: 向后兼容
系统SHALL保留 `generate_random_embedding` 函数以确保历史代码不报错，但默认使用新的确定性嵌入。

#### Scenario: 旧代码调用随机嵌入
- **WHEN** 旧代码调用 `generate_random_embedding()`
- **THEN** 函数仍可用但产生 deprecation warning

## MODIFIED Requirements
### Requirement: 默认嵌入生成器
原 `MemoryManager` 在未提供 embedding 时默认调用 `generate_random_embedding()`，现在改为调用 `generate_text_embedding()`。

**修改前**:
```python
if embedding is None:
    embedding = generate_random_embedding(self.vector_dim)
```

**修改后**:
```python
if embedding is None:
    embedding = generate_text_embedding(text_content, self.vector_dim)
```

### Requirement: 长期记忆 store() 流程
原 `LongTermMemory.store()` 接受可选 `embedding` 参数，若未提供则使用随机嵌入。现在改为从 `content` 中提取文本生成确定性嵌入。

**修改前**:
```python
def store(self, content: str, embedding: Optional[np.ndarray] = None, ...):
    if embedding is None:
        embedding = generate_random_embedding(self.vector_dim)
```

**修改后**:
```python
def store(self, content: str, embedding: Optional[np.ndarray] = None, ...):
    if embedding is None:
        # 提取 content 中的文本用于嵌入
        text = self._extract_text_for_embedding(content)
        embedding = generate_text_embedding(text, self.vector_dim)
```

### Requirement: 记忆面板索引状态显示
原 `memory_viz.py` 的 `update_long_term_stats` 仅根据 `enable_faiss` 标志显示索引状态。现改为根据 `total_memories > 0` 和 `enable_faiss` 共同决定显示内容。

**修改前**:
```python
self.ltm_index_label.setText("已构建" if index_built else "未构建")
```

**修改后**:
```python
if total_memories > 0:
    if index_built:
        self.ltm_index_label.setText("已构建（FAISS）")
    else:
        self.ltm_index_label.setText("已构建（暴力搜索）")
else:
    self.ltm_index_label.setText("无数据")
```

## REMOVED Requirements
无

## 验证策略

### 单元测试
1. 测试 `generate_text_embedding()` 的确定性：相同输入 → 相同输出
2. 测试 `generate_text_embedding()` 的语义性：相似文本 → 高相似度
3. 测试 `LongTermMemory.store()` + `search_by_embedding()` 的全链路

### 集成测试
1. 启动 Brain，存储若干条测试记忆
2. 用相关查询检索，验证返回的相关记忆
3. 验证记忆面板的索引状态显示

### 端到端测试
1. 启动 GUI
2. 在对话中说"我叫张三，喜欢蓝色"
3. 在新会话中问"我喜欢什么颜色"
4. 验证 AI 能回忆起"蓝色"
