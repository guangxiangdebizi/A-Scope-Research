# 基础智能体类

import asyncio
import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv

class BaseAgent:
    """基础智能体类，所有专业分析师智能体的父类"""
    
    def __init__(self, name: str, role: str, prompt: str, model_config: Dict[str, Any]):
        self.name = name
        self.role = role
        self.prompt = prompt
        self.model_config = model_config
        self.conversation_history = []
        self.thoughts = []
        self.tool_calls = []
        
        # 初始化大模型 - 必须从配置文件获取所有参数
        self.llm = ChatOpenAI(
            model=model_config["model"],
            api_key=model_config["api_key"],
            base_url=model_config["base_url"],
            temperature=model_config["temperature"],
            max_tokens=model_config["max_tokens"]
        )
        
        self.client = None
        self.tools = []
        self.agent = None
        
    async def initialize_mcp(self, mcp_config: Dict[str, Any]):
        """初始化MCP客户端和工具"""
        try:
            # 提取servers配置
            servers_config = mcp_config.get("servers", {})
            if not servers_config:
                print(f"⚠️ {self.name} 没有可用的MCP服务器配置，跳过MCP初始化")
                self.tools = []
                # 创建不带工具的智能体
                self.agent = create_react_agent(self.llm, self.tools)
                return
                
            self.client = MultiServerMCPClient(servers_config)
            self.tools = await self.client.get_tools()
            
            # 创建带有角色prompt的智能体
            self.agent = create_react_agent(self.llm, self.tools)
            
            print(f"✅ {self.name} 初始化成功，可用工具: {len(self.tools)}个")
            
        except Exception as e:
            print(f"❌ {self.name} MCP初始化失败: {e}")
            raise
    
    async def analyze(self, stock_code: str, context: str = "") -> Dict[str, Any]:
        """分析股票，返回分析结果"""
        if not self.agent:
            return {"error": "智能体未初始化"}
        
        try:
            # 构建分析请求
            analysis_request = f"""
            {self.prompt}
            
            当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            
            请分析股票代码: {stock_code}
            
            额外上下文信息: {context}
            
            请从你的专业角度({self.role})进行深入分析，并提供具体的投资建议。
            请使用MCP工具获取必要的市场数据来支持你的分析。
            """
            
            # 记录思考过程
            thought = f"开始分析股票 {stock_code}，从{self.role}角度进行专业分析"
            self.thoughts.append({
                "timestamp": datetime.now().isoformat(),
                "content": thought
            })
            
            # 调用智能体进行分析
            response = await self.agent.ainvoke({
                "messages": [{"role": "user", "content": analysis_request}]
            })
            
            # 处理响应
            messages = response.get("messages", [])
            analysis_result = ""
            tool_calls_made = []
            
            for msg in messages:
                if hasattr(msg, 'type'):
                    if msg.type == 'ai':
                        if hasattr(msg, 'tool_calls') and msg.tool_calls:
                            for tool_call in msg.tool_calls:
                                tool_calls_made.append({
                                    "tool": tool_call.get('name', 'unknown'),
                                    "args": tool_call.get('args', {}),
                                    "timestamp": datetime.now().isoformat()
                                })
                        else:
                            analysis_result = msg.content
                    elif msg.type == 'tool':
                        # 记录工具返回结果
                        pass
            
            # 更新历史记录
            self.conversation_history.append({
                "timestamp": datetime.now().isoformat(),
                "request": analysis_request,
                "response": analysis_result,
                "tool_calls": tool_calls_made
            })
            
            self.tool_calls.extend(tool_calls_made)
            
            return {
                "agent_name": self.name,
                "role": self.role,
                "analysis": analysis_result,
                "tool_calls": tool_calls_made,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"分析失败: {str(e)}"
            print(f"❌ {self.name} {error_msg}")
            return {
                "agent_name": self.name,
                "role": self.role,
                "error": error_msg,
                "timestamp": datetime.now().isoformat()
            }
    
    async def debate_response(self, topic: str, other_opinions: List[Dict[str, Any]]) -> str:
        """参与团队辩论，回应其他智能体的观点"""
        if not self.agent:
            return "智能体未初始化，无法参与辩论"
        
        try:
            # 构建辩论上下文
            debate_context = f"辩论主题: {topic}\n\n其他分析师的观点:\n"
            
            for i, opinion in enumerate(other_opinions, 1):
                debate_context += f"{i}. {opinion.get('agent_name', '未知')}({opinion.get('role', '未知')}):\n"
                debate_context += f"   {opinion.get('analysis', opinion.get('content', ''))}\n\n"
            
            debate_request = f"""
            {self.prompt}
            
            当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            
            {debate_context}
            
            请从你的专业角度({self.role})对以上观点进行评价和回应。
            你可以：
            1. 支持某些观点并提供额外论据
            2. 质疑某些观点并提出反驳
            3. 提出新的视角和见解
            4. 使用MCP工具获取数据来支持你的论点
            
            请保持专业和建设性的讨论态度。
            """
            
            # 记录辩论思考
            thought = f"参与辩论: {topic}，准备从{self.role}角度回应"
            self.thoughts.append({
                "timestamp": datetime.now().isoformat(),
                "content": thought
            })
            
            # 调用智能体
            response = await self.agent.ainvoke({
                "messages": [{"role": "user", "content": debate_request}]
            })
            
            # 提取回应内容
            messages = response.get("messages", [])
            debate_response = ""
            
            for msg in messages:
                if hasattr(msg, 'type') and msg.type == 'ai':
                    if not (hasattr(msg, 'tool_calls') and msg.tool_calls):
                        debate_response = msg.content
                        break
            
            return debate_response
            
        except Exception as e:
            return f"辩论回应失败: {str(e)}"
    
    async def make_decision(self, analysis_summary: str) -> Dict[str, Any]:
        """基于分析结果做出投资决策"""
        if not self.agent:
            return {"error": "智能体未初始化"}
        
        try:
            decision_request = f"""
            {self.prompt}
            
            当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            
            基于以下分析总结，请做出明确的投资决策：
            
            {analysis_summary}
            
            请从你的专业角度({self.role})给出：
            1. 投资建议：买入/持有/卖出
            2. 建议仓位：轻仓/标准仓位/重仓
            3. 风险评级：低风险/中风险/高风险
            4. 持有期建议：短期/中期/长期
            5. 关键理由：支持你决策的3个主要原因
            
            请给出明确的结构化回答。
            """
            
            response = await self.agent.ainvoke({
                "messages": [{"role": "user", "content": decision_request}]
            })
            
            # 提取决策内容
            messages = response.get("messages", [])
            decision_content = ""
            
            for msg in messages:
                if hasattr(msg, 'type') and msg.type == 'ai':
                    if not (hasattr(msg, 'tool_calls') and msg.tool_calls):
                        decision_content = msg.content
                        break
            
            return {
                "agent_name": self.name,
                "role": self.role,
                "decision": decision_content,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "agent_name": self.name,
                "role": self.role,
                "error": f"决策失败: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    def get_status(self) -> Dict[str, Any]:
        """获取智能体状态信息"""
        return {
            "name": self.name,
            "role": self.role,
            "model": self.model_config["model"],
            "initialized": self.agent is not None,
            "tools_count": len(self.tools),
            "conversation_count": len(self.conversation_history),
            "thoughts_count": len(self.thoughts),
            "tool_calls_count": len(self.tool_calls)
        }
    
    async def close(self):
        """关闭智能体连接"""
        if self.client:
            await self.client.close()