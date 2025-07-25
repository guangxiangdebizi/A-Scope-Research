# A-Scope Research - 金融智能体团队

基于MCP（Model Context Protocol）的中国A股市场智能分析系统，通过多个专业智能体的协作和辩论，为投资决策提供全面的分析支持。

## 🌟 系统特色

### 🤖 专业智能体团队
- **技术分析师（李技术）**：专注技术指标、图表形态和趋势分析
- **基本面分析师（王基本）**：关注财务数据、公司价值和行业分析
- **量化分析师（张量化）**：运用数学模型、统计方法和风险量化
- **市场情绪分析师（陈情绪）**：分析投资者情绪、市场心理和舆情
- **风险管理师（刘风控）**：评估投资风险、制定风控策略

### 🔄 智能协作流程
1. **并行分析**：各智能体从专业角度独立分析目标股票
2. **团队辩论**：多轮辩论讨论，交换观点和质疑假设
3. **最终决策**：基于辩论共识做出投资建议
4. **风险评估**：全面的风险分析和控制建议

### 🛠️ 技术架构
- **MCP协议集成**：实时获取A股市场数据和分析工具
- **多模型支持**：兼容OpenAI、智谱GLM、通义千问等主流大模型
- **实时Web界面**：类似微信群聊的智能体对话界面
- **灵活配置**：支持YAML配置文件自定义模型和参数

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd A-Scope-Research

# 创建虚拟环境（推荐）
python -m venv .venv

# 激活虚拟环境
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置设置

#### 编辑 `config.yaml`

```yaml
agents:
  technical_analyst:
    name: "李技术"
    model: "gpt-3.5-turbo"  # 或其他支持的模型
    api_key: "your_api_key_here"  # 替换为您的API密钥
    base_url: "https://api.openai.com/v1"  # 或其他API地址
    temperature: 0.7
    max_tokens: 2000
  # ... 其他智能体配置
```

#### 支持的模型服务商

| 服务商 | base_url | 模型示例 |
|--------|----------|----------|
| OpenAI | `https://api.openai.com/v1` | `gpt-3.5-turbo`, `gpt-4` |
| 智谱GLM | `https://open.bigmodel.cn/api/paas/v4/` | `glm-4`, `glm-3-turbo` |
| 通义千问 | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-turbo`, `qwen-plus` |
| 月之暗面 | `https://api.moonshot.cn/v1` | `moonshot-v1-8k`, `moonshot-v1-32k` |
| DeepSeek | `https://api.deepseek.com/v1` | `deepseek-chat`, `deepseek-coder` |

### 3. 运行方式

#### 🌐 Web界面模式（推荐）

```bash
python main.py --mode web
```

访问 `http://localhost:8501` 打开Web界面

#### 💻 命令行模式

```bash
# 分析指定股票
python main.py --mode cli --stock 000001
```

#### 🎭 演示模式

```bash
# 交互式演示
python main.py --mode demo
```

## 📊 Web界面功能

### 主要功能
- **实时团队状态**：显示各智能体的初始化状态和工具数量
- **股票分析输入**：支持6位A股代码输入
- **分析结果展示**：各智能体的专业分析报告
- **辩论过程可视化**：类似群聊的实时辩论界面
- **最终决策汇总**：投资建议和风险评估
- **结果导出**：JSON格式的完整分析报告

### 界面特色
- 🎨 **智能体头像**：每个智能体有独特的emoji头像
- 🎨 **颜色区分**：不同角色使用不同的颜色主题
- ⏰ **时间戳显示**：完整的分析时间线
- 🔧 **工具调用展示**：实时显示MCP工具的调用过程
- 📱 **响应式设计**：适配不同屏幕尺寸

## 🔧 项目结构

```
A-Scope-Research/
├── main.py                 # 主入口文件
├── config.yaml            # 智能体配置文件
├── mcp.json              # MCP服务器配置
├── requirements.txt       # Python依赖包
├── README.md             # 项目文档
├── src/
│   ├── __init__.py
│   ├── agents/           # 智能体模块
│   │   ├── __init__.py
│   │   ├── base_agent.py      # 基础智能体类
│   │   └── team_manager.py    # 团队管理器
│   ├── prompts/          # 智能体Prompt
│   │   ├── __init__.py
│   │   ├── technical_analyst.py    # 技术分析师
│   │   ├── fundamental_analyst.py  # 基本面分析师
│   │   ├── quantitative_analyst.py # 量化分析师
│   │   ├── sentiment_analyst.py    # 情绪分析师
│   │   └── risk_manager.py         # 风险管理师
│   └── ui/               # 用户界面
│       ├── __init__.py
│       └── streamlit_app.py       # Streamlit Web应用
└── .venv/                # 虚拟环境（自动生成）
```

## 🎯 使用场景

### 个人投资者
- 获得多角度的专业分析意见
- 了解不同投资策略的优缺点
- 做出更加理性的投资决策

### 投资机构
- 辅助投研团队的决策流程
- 提供标准化的分析框架
- 降低单一视角的分析偏差

### 金融教育
- 学习不同分析方法的应用
- 理解投资决策的复杂性
- 观察专业分析师的思维过程

## 🔍 分析示例

### 输入
```
股票代码: 000001 (平安银行)
```

### 输出示例

#### 技术分析师观点
> 📈 从技术面看，000001当前处于上升通道中，MA20支撑有效，MACD金叉信号明确，建议逢低买入...

#### 基本面分析师观点
> 📋 平安银行Q3财报显示ROE稳定在13%以上，不良贷款率控制良好，估值相对合理，具备长期投资价值...

#### 量化分析师观点
> 🔢 基于历史数据回测，当前价位的风险调整收益率为1.8，波动率处于历史中位数，建议标准仓位配置...

#### 市场情绪分析师观点
> 😊 近期银行板块情绪回暖，机构资金流入明显，但需警惕政策预期变化对情绪的影响...

#### 风险管理师观点
> 🛡️ 主要风险来自利率政策变化和信贷周期，建议设置8%止损位，仓位不超过组合的15%...

## ⚙️ 高级配置

### 自定义智能体

可以通过修改 `src/prompts/` 目录下的文件来自定义智能体的行为和专业特长。

### MCP工具扩展

在 `mcp.json` 中添加新的MCP服务器来扩展数据源和分析工具。

### 模型参数调优

在 `config.yaml` 中调整各智能体的 `temperature` 和 `max_tokens` 参数来优化输出质量。

## 🐛 故障排除

### 常见问题

1. **模型连接失败**
   - 检查API密钥是否正确
   - 验证base_url格式
   - 确认网络连接正常

2. **MCP工具连接失败**
   - 检查MCP服务器URL可访问性
   - 验证防火墙设置
   - 确认超时设置合理

3. **依赖包安装失败**
   - 使用国内镜像源：`pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt`
   - 升级pip版本：`pip install --upgrade pip`

### 调试模式

启用详细日志输出：

```bash
# 设置环境变量
export LOG_LEVEL=DEBUG
python main.py --mode cli --stock 000001
```

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进项目！

### 开发环境设置

```bash
# 安装开发依赖
pip install -r requirements.txt
pip install pytest black flake8 mypy

# 代码格式化
black src/

# 代码检查
flake8 src/

# 类型检查
mypy src/

# 运行测试
pytest
```

## 📄 许可证

本项目采用 MIT 许可证，详见 [LICENSE](LICENSE) 文件。

## 🙏 致谢

- [LangChain](https://github.com/langchain-ai/langchain) - 大模型应用框架
- [MCP](https://github.com/modelcontextprotocol) - 模型上下文协议
- [Streamlit](https://streamlit.io/) - Web应用框架

## 📞 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 [GitHub Issue](https://github.com/guangxiangdebizi/A-Scope-Research/issues)
- 发送邮件至：guangxiangdebizi@gmail.com

---

**免责声明**：本系统仅供学习和研究使用，不构成投资建议。投资有风险，决策需谨慎。
