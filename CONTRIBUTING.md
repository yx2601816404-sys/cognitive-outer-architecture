# 贡献指南

感谢你对 COA（Cognitive Orchestration Architecture）项目的兴趣！

## 🎯 我们需要什么样的贡献

### 1. 代码贡献

- **核心组件改进**：优化 parasitic-shell、distiller、三体分离架构
- **新功能**：实现论文中提到但尚未实现的功能
- **Bug 修复**：修复已知问题
- **性能优化**：降低延迟、减少 token 消耗
- **测试**：增加单元测试、集成测试

### 2. 文档贡献

- **完善文档**：改进现有文档的清晰度和完整性
- **翻译**：将文档翻译成其他语言（英文、日文、韩文等）
- **教程**：编写使用教程、最佳实践指南
- **案例研究**：分享你的使用场景和经验

### 3. 实验贡献

- **复现实验**：在你的场景下测试 COA，分享数据
- **新场景**：探索 COA 在新领域的应用（医疗、法律、教育等）
- **对比实验**：与其他方案对比，提供客观评估

### 4. 理论贡献

- **挑战假设**：质疑我们的理论基础，提出反例
- **新洞察**：提出新的理论框架或改进方案
- **跨学科视角**：从哲学、心理学、神经科学等角度提供洞察

---

## 🚀 如何开始

### 1. Fork 项目

点击右上角的 "Fork" 按钮，将项目 fork 到你的账号下。

### 2. Clone 到本地

```bash
git clone https://github.com/your-username/coa-project.git
cd coa-project
```

### 3. 创建分支

```bash
git checkout -b feature/your-feature-name
```

### 4. 进行修改

- 遵循代码风格（见下文）
- 添加必要的测试
- 更新相关文档

### 5. 提交 PR

```bash
git add .
git commit -m "feat: add your feature description"
git push origin feature/your-feature-name
```

然后在 GitHub 上创建 Pull Request。

---

## 📝 代码风格

### Python

- 遵循 PEP 8
- 使用 type hints
- 函数和类添加 docstring
- 变量名使用英文，注释可以用中文

示例：

```python
def distill(
    self,
    conversation_buffer: list[dict],
    session: aiohttp.ClientSession,
) -> Optional[str]:
    """
    蒸馏对话缓冲，返回蒸馏结果文本。

    Args:
        conversation_buffer: 对话缓冲 [{"role": "user", "content": "...", "ts": "..."}]
        session: aiohttp session

    Returns:
        蒸馏结果文本，如果失败返回 None
    """
    pass
```

### Markdown

- 使用清晰的标题层级
- 代码块指定语言
- 链接使用相对路径

---

## 🧪 测试

### 运行测试

```bash
# 单元测试
pytest tests/

# 集成测试
pytest tests/integration/

# 覆盖率
pytest --cov=parasitic_shell tests/
```

### 添加测试

- 每个新功能都应该有对应的测试
- 测试文件放在 `tests/` 目录下
- 测试函数以 `test_` 开头

---

## 📋 提交信息规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

- `feat:` 新功能
- `fix:` Bug 修复
- `docs:` 文档更新
- `style:` 代码格式（不影响功能）
- `refactor:` 重构
- `test:` 测试相关
- `chore:` 构建/工具相关

示例：

```
feat: add pain firewall mechanism
fix: resolve memory leak in distiller
docs: update README with new examples
```

---

## 🔍 代码审查

所有 PR 都需要经过代码审查：

1. **自动检查**：CI/CD 会自动运行测试和 linting
2. **人工审查**：至少一位维护者会审查你的代码
3. **反馈**：根据反馈进行修改
4. **合并**：审查通过后，维护者会合并你的 PR

---

## 🤝 行为准则

### 我们期望的行为

- **尊重**：尊重所有贡献者，无论背景和经验
- **建设性**：提供建设性的反馈，而不是批评
- **开放**：对不同观点保持开放态度
- **协作**：乐于帮助他人，分享知识

### 不可接受的行为

- **骚扰**：任何形式的骚扰、歧视、攻击
- **垃圾信息**：发送垃圾信息、广告
- **恶意行为**：故意破坏项目、泄露隐私

违反行为准则的贡献者可能会被禁止参与项目。

---

## 📬 联系我们

如果你有任何问题或建议，可以通过以下方式联系我们：

- **GitHub Issues**：提交 issue
- **Discord**：[待补充]
- **邮箱**：[待补充]

---

## 🙏 感谢

感谢你的贡献！每一个 PR、每一个 issue、每一条反馈都让 COA 变得更好。

**一起推动认知主权革命！** 🔥
