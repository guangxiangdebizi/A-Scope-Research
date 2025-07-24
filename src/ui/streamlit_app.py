# Streamlit Web界面应用

import streamlit as st
import asyncio
import json
import time
import yaml
from datetime import datetime
from typing import Dict, List, Any
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.agents.team_manager import AgentTeamManager

def load_config():
    """加载配置文件"""
    try:
        with open('config.yaml', 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        st.error("配置文件 config.yaml 不存在，请确保配置文件存在")
        st.stop()
    except Exception as e:
        st.error(f"加载配置文件失败: {e}")
        st.stop()

# 页面配置
st.set_page_config(
    page_title="A-Scope Research - 金融智能体团队",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
st.markdown("""
<style>
.agent-card {
    background-color: #f0f2f6;
    padding: 1rem;
    border-radius: 0.5rem;
    margin: 0.5rem 0;
    border-left: 4px solid #1f77b4;
}

.technical-analyst { border-left-color: #ff7f0e; }
.fundamental-analyst { border-left-color: #2ca02c; }
.quantitative-analyst { border-left-color: #d62728; }
.sentiment-analyst { border-left-color: #9467bd; }
.risk-manager { border-left-color: #8c564b; }

.chat-message {
    padding: 1rem;
    border-radius: 0.5rem;
    margin: 0.5rem 0;
    background-color: #ffffff;
    border: 1px solid #e0e0e0;
}

.tool-call {
    background-color: #e8f4fd;
    padding: 0.5rem;
    border-radius: 0.3rem;
    margin: 0.3rem 0;
    font-family: monospace;
    font-size: 0.8rem;
}

.decision-card {
    background-color: #f8f9fa;
    padding: 1rem;
    border-radius: 0.5rem;
    margin: 0.5rem 0;
    border: 2px solid #28a745;
}

.error-message {
    background-color: #f8d7da;
    color: #721c24;
    padding: 0.5rem;
    border-radius: 0.3rem;
    margin: 0.3rem 0;
}
</style>
""", unsafe_allow_html=True)

# 智能体头像映射
AGENT_AVATARS = {
    "李技术": "📈",
    "王基本": "📋",
    "张量化": "🔢",
    "陈情绪": "😊",
    "刘风控": "🛡️"
}

# 智能体颜色映射
AGENT_COLORS = {
    "技术分析师": "technical-analyst",
    "基本面分析师": "fundamental-analyst",
    "量化分析师": "quantitative-analyst",
    "市场情绪分析师": "sentiment-analyst",
    "风险管理师": "risk-manager"
}

def init_session_state():
    """初始化会话状态"""
    if 'team_manager' not in st.session_state:
        st.session_state.team_manager = None
    if 'team_initialized' not in st.session_state:
        st.session_state.team_initialized = False
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = []
    if 'debate_history' not in st.session_state:
        st.session_state.debate_history = []
    if 'final_decisions' not in st.session_state:
        st.session_state.final_decisions = []
    if 'current_stock' not in st.session_state:
        st.session_state.current_stock = ""

def display_agent_card(agent_info: Dict[str, Any]):
    """显示智能体信息卡片"""
    role = agent_info.get('role', '未知')
    name = agent_info.get('name', '未知')
    avatar = AGENT_AVATARS.get(name, "🤖")
    color_class = AGENT_COLORS.get(role, "")
    
    st.markdown(f"""
    <div class="agent-card {color_class}">
        <h4>{avatar} {name}</h4>
        <p><strong>角色:</strong> {role}</p>
        <p><strong>模型:</strong> {agent_info.get('model', '未知')}</p>
        <p><strong>状态:</strong> {'✅ 已初始化' if agent_info.get('initialized', False) else '❌ 未初始化'}</p>
        <p><strong>工具数量:</strong> {agent_info.get('tools_count', 0)}</p>
        <p><strong>对话次数:</strong> {agent_info.get('conversation_count', 0)}</p>
    </div>
    """, unsafe_allow_html=True)

def display_chat_message(message: Dict[str, Any], show_tools: bool = True):
    """显示聊天消息"""
    agent_name = message.get('agent_name', '系统')
    role = message.get('role', '')
    content = message.get('analysis', message.get('response', message.get('decision', '')))
    timestamp = message.get('timestamp', '')
    tool_calls = message.get('tool_calls', [])
    
    avatar = AGENT_AVATARS.get(agent_name, "🤖")
    color_class = AGENT_COLORS.get(role, "")
    
    # 格式化时间戳
    if timestamp:
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            time_str = dt.strftime('%H:%M:%S')
        except:
            time_str = timestamp
    else:
        time_str = ''
    
    st.markdown(f"""
    <div class="chat-message {color_class}">
        <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
            <span style="font-size: 1.2rem; margin-right: 0.5rem;">{avatar}</span>
            <strong>{agent_name}</strong>
            <span style="color: #666; margin-left: 0.5rem;">({role})</span>
            <span style="color: #999; margin-left: auto; font-size: 0.8rem;">{time_str}</span>
        </div>
        <div>{content}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # 显示工具调用
    if show_tools and tool_calls:
        for tool_call in tool_calls:
            tool_name = tool_call.get('tool', '未知工具')
            tool_args = tool_call.get('args', {})
            st.markdown(f"""
            <div class="tool-call">
                🔧 调用工具: <strong>{tool_name}</strong><br>
                📝 参数: {json.dumps(tool_args, ensure_ascii=False, indent=2)}
            </div>
            """, unsafe_allow_html=True)

def display_decision_card(decision: Dict[str, Any]):
    """显示决策卡片"""
    agent_name = decision.get('agent_name', '未知')
    role = decision.get('role', '')
    decision_content = decision.get('decision', '')
    timestamp = decision.get('timestamp', '')
    
    avatar = AGENT_AVATARS.get(agent_name, "🤖")
    
    # 格式化时间戳
    if timestamp:
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            time_str = dt.strftime('%H:%M:%S')
        except:
            time_str = timestamp
    else:
        time_str = ''
    
    st.markdown(f"""
    <div class="decision-card">
        <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
            <span style="font-size: 1.2rem; margin-right: 0.5rem;">{avatar}</span>
            <strong>{agent_name}</strong>
            <span style="color: #666; margin-left: 0.5rem;">({role})</span>
            <span style="color: #999; margin-left: auto; font-size: 0.8rem;">{time_str}</span>
        </div>
        <div><strong>最终决策:</strong></div>
        <div>{decision_content}</div>
    </div>
    """, unsafe_allow_html=True)

async def initialize_team():
    """初始化智能体团队"""
    try:
        if st.session_state.team_manager is None:
            st.session_state.team_manager = AgentTeamManager("config.yaml")
        
        await st.session_state.team_manager.initialize_team()
        st.session_state.team_initialized = True
        return True
    except Exception as e:
        st.error(f"团队初始化失败: {e}")
        return False

async def analyze_stock(stock_code: str):
    """分析股票"""
    try:
        if not st.session_state.team_initialized:
            st.error("请先初始化团队")
            return
        
        # 清空之前的结果
        st.session_state.analysis_results = []
        st.session_state.debate_history = []
        st.session_state.final_decisions = []
        st.session_state.current_stock = stock_code
        
        # 执行分析
        with st.spinner(f"正在分析股票 {stock_code}..."):
            result = await st.session_state.team_manager.analyze_stock(stock_code)
            st.session_state.analysis_results = result.get('analysis_results', [])
        
        st.success(f"股票 {stock_code} 分析完成！")
        
    except Exception as e:
        st.error(f"分析失败: {e}")

async def conduct_debate(stock_code: str):
    """进行辩论"""
    try:
        if not st.session_state.analysis_results:
            st.error("请先进行股票分析")
            return
        
        with st.spinner(f"正在进行团队辩论..."):
            debate_results = await st.session_state.team_manager.conduct_debate(
                stock_code, st.session_state.analysis_results
            )
            st.session_state.debate_history = debate_results
        
        st.success("团队辩论完成！")
        
    except Exception as e:
        st.error(f"辩论失败: {e}")

async def make_decisions(stock_code: str):
    """做出最终决策"""
    try:
        if not st.session_state.debate_history:
            st.error("请先进行团队辩论")
            return
        
        with st.spinner(f"正在做出最终决策..."):
            decisions = await st.session_state.team_manager.make_final_decisions(stock_code)
            st.session_state.final_decisions = decisions
        
        st.success("最终决策完成！")
        
    except Exception as e:
        st.error(f"决策失败: {e}")

def main():
    """主函数"""
    init_session_state()
    
    # 加载配置
    config = load_config()
    ui_config = config.get('ui', {})
    
    # 使用配置中的标题
    title = ui_config.get('title', '📊 A-Scope Research - 金融智能体团队')
    subtitle = ui_config.get('subtitle', '基于MCP的中国A股市场分析系统')
    
    st.title(title)
    st.markdown(f"### {subtitle}")
    
    # 侧边栏
    with st.sidebar:
        st.header("🎛️ 控制面板")
        
        # 团队初始化
        if st.button("🚀 初始化智能体团队", type="primary"):
            with st.spinner("正在初始化团队..."):
                success = asyncio.run(initialize_team())
                if success:
                    st.success("团队初始化成功！")
                    st.rerun()
        
        st.markdown("---")
        
        # 股票分析输入
        stock_code = st.text_input(
            "📈 股票代码",
            placeholder="例如: 000001, 600036",
            help="请输入6位A股股票代码"
        )
        
        # 分析按钮
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔍 开始分析", disabled=not st.session_state.team_initialized):
                if stock_code:
                    asyncio.run(analyze_stock(stock_code))
                    st.rerun()
                else:
                    st.error("请输入股票代码")
        
        with col2:
            if st.button("🗣️ 开始辩论", disabled=not bool(st.session_state.analysis_results)):
                asyncio.run(conduct_debate(st.session_state.current_stock))
                st.rerun()
        
        # 决策按钮
        if st.button("🎯 最终决策", disabled=not bool(st.session_state.debate_history)):
            asyncio.run(make_decisions(st.session_state.current_stock))
            st.rerun()
        
        st.markdown("---")
        
        # 导出结果
        if st.button("📄 导出结果", disabled=not bool(st.session_state.final_decisions)):
            if st.session_state.team_manager:
                filename = st.session_state.team_manager.export_results()
                if filename:
                    st.success(f"结果已导出: {filename}")
        
        # 显示设置
        st.header("⚙️ 显示设置")
        show_timestamps = st.checkbox("显示时间戳", value=True)
        show_tool_calls = st.checkbox("显示工具调用", value=True)
        auto_scroll = st.checkbox("自动滚动", value=True)
    
    # 主内容区域
    if st.session_state.team_initialized:
        # 显示团队状态
        if st.session_state.team_manager:
            team_status = st.session_state.team_manager.get_team_status()
            
            st.header("👥 智能体团队状态")
            
            # 团队概览
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("团队规模", team_status.get('team_size', 0))
            with col2:
                st.metric("分析次数", team_status.get('analysis_count', 0))
            with col3:
                st.metric("辩论轮数", team_status.get('debate_rounds', 0))
            with col4:
                st.metric("决策次数", team_status.get('decisions_count', 0))
            
            # 智能体状态卡片
            st.subheader("🤖 智能体状态")
            agents_info = team_status.get('agents', {})
            
            cols = st.columns(len(agents_info))
            for i, (agent_key, agent_info) in enumerate(agents_info.items()):
                with cols[i]:
                    display_agent_card(agent_info)
        
        # 分析结果
        if st.session_state.analysis_results:
            st.header(f"📊 分析结果 - {st.session_state.current_stock}")
            
            for result in st.session_state.analysis_results:
                if 'error' not in result:
                    display_chat_message(result, show_tool_calls)
                else:
                    st.markdown(f"""
                    <div class="error-message">
                        ❌ {result.get('agent_name', '未知智能体')} 分析失败: {result.get('error', '未知错误')}
                    </div>
                    """, unsafe_allow_html=True)
        
        # 辩论历史
        if st.session_state.debate_history:
            st.header("🗣️ 团队辩论")
            
            # 按轮次分组显示
            rounds = {}
            for debate in st.session_state.debate_history:
                round_num = debate.get('round', 1)
                if round_num not in rounds:
                    rounds[round_num] = []
                rounds[round_num].append(debate)
            
            for round_num in sorted(rounds.keys()):
                st.subheader(f"第 {round_num} 轮辩论")
                for debate in rounds[round_num]:
                    display_chat_message(debate, show_tool_calls)
        
        # 最终决策
        if st.session_state.final_decisions:
            st.header("🎯 最终投资决策")
            
            for decision in st.session_state.final_decisions:
                if 'error' not in decision:
                    display_decision_card(decision)
                else:
                    st.markdown(f"""
                    <div class="error-message">
                        ❌ {decision.get('agent_name', '未知智能体')} 决策失败: {decision.get('error', '未知错误')}
                    </div>
                    """, unsafe_allow_html=True)
    
    else:
        # 欢迎页面
        st.info("👋 欢迎使用A-Scope Research金融智能体团队！请先点击左侧的'初始化智能体团队'按钮开始。")
        
        # 功能介绍
        st.header("✨ 系统功能")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **🤖 智能体团队**
            - 技术分析师：专注技术指标和图表分析
            - 基本面分析师：关注财务数据和公司价值
            - 量化分析师：运用数学模型和统计方法
            - 市场情绪分析师：分析投资者情绪和市场心理
            - 风险管理师：评估和控制投资风险
            """)
        
        with col2:
            st.markdown("""
            **🔄 分析流程**
            1. 各智能体独立分析目标股票
            2. 团队进行多轮辩论讨论
            3. 基于辩论结果做出最终决策
            4. 提供买入/持有/卖出建议
            """)
        
        st.header("🛠️ 技术特性")
        st.markdown("""
        - **MCP工具集成**：实时获取A股市场数据
        - **多模型支持**：支持OpenAI、智谱GLM、通义千问等多种大模型
        - **实时辩论界面**：类似微信群聊的智能体对话界面
        - **决策投票机制**：基于团队共识的投资建议
        - **风险评估**：全面的风险分析和控制建议
        """)

if __name__ == "__main__":
    main()