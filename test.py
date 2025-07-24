import asyncio
import json
import os
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, AIMessage

# 加载环境变量
load_dotenv()

class MCPAgent:
    """MCP工具代理，实现大模型与MCP工具的交互"""
    
    def __init__(self, openai_api_key: str = None, model: str = "glm-4-air-250414", config_file: str = "mcp_config.json"):
        """初始化MCP代理
        
        Args:
            openai_api_key: OpenAI API密钥
            model: 使用的模型名称
            config_file: MCP配置文件路径
        """
        # 从环境变量获取API密钥和基础URL
        if openai_api_key is None:
            openai_api_key = os.getenv('LLM_API_KEY')
        
        base_url = os.getenv('LLM_BASE_URL', 'https://open.bigmodel.cn/api/paas/v4')
        
        if not openai_api_key:
            print("⚠️ 警告: 未设置LLM API密钥，请设置环境变量LLM_API_KEY或传入api_key参数")
        
        self.config_file = config_file
        self.config = self._load_config()
        
        # 使用配置文件中的模型设置
        model_config = self.config.get('model_config', {})
        default_model = os.getenv('CHIEF_ANALYST_MODEL', 'glm-4-air-250414')
        
        self.llm = ChatOpenAI(
            model=model or self.config.get('default_model', default_model), 
            temperature=model_config.get('temperature', 0),
            max_tokens=model_config.get('max_tokens', 4000),
            api_key=openai_api_key,
            base_url=base_url
        )
        self.client = None
        self.tools = []
        self.tools_by_server = {}
        self.agent = None
        self.conversation_history = []
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                print(f"⚠️ 配置文件 {self.config_file} 不存在，使用默认配置")
                return self._get_default_config()
        except Exception as e:
            print(f"⚠️ 加载配置文件失败: {e}，使用默认配置")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
             "servers": {
                 "finance": {
                     "url": "http://106.14.205.176:3101/sse",
                     "transport": "sse",
                     "timeout": 600
                 }
             },
             "default_model": "glm-4",
             "model_config": {
                 "temperature": 0,
                 "max_tokens": 4000
             }
         }
    
    async def initialize(self, mcp_config: Dict[str, Any] = None):
        """初始化MCP客户端和工具
        
        Args:
            mcp_config: MCP服务器配置，如果为None则使用配置文件中的配置
        """
        # 使用传入的配置或配置文件中的配置
        if mcp_config is None:
            mcp_config = self.config.get('servers', {})
        
        try:
            # 创建MCP客户端
            self.client = MultiServerMCPClient(mcp_config)
            
            # 获取所有工具
            self.tools = await self.client.get_tools()
            
            # 按服务器分组工具
            self._organize_tools_by_server()
            
            # 创建React Agent
            self.agent = create_react_agent(self.llm, self.tools)
            
            print(f"✅ MCP代理初始化成功！")
            print(f"📊 发现 {len(self.tools)} 个工具，来自 {len(self.tools_by_server)} 个服务器")
            
        except Exception as e:
            print(f"❌ MCP代理初始化失败: {e}")
            raise
    
    def _organize_tools_by_server(self):
        """按服务器组织工具"""
        for tool in self.tools:
            # 尝试从工具名称或属性中推断服务器名称
            server_name = getattr(tool, 'server_name', 'unknown')
            if server_name not in self.tools_by_server:
                self.tools_by_server[server_name] = []
            self.tools_by_server[server_name].append(tool)
    
    def get_tools_info(self) -> Dict[str, Any]:
        """获取工具信息列表，按MCP服务器分组"""
        if not self.tools_by_server:
            return {"servers": {}, "total_tools": 0, "server_count": 0}
        
        servers_info = {}
        total_tools = 0
        
        # 按服务器分组构建工具信息
        for server_name, server_tools in self.tools_by_server.items():
            tools_info = []
            
            for tool in server_tools:
                tool_info = {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {},
                    "required": []
                }
                
                # 获取参数信息
                try:
                    schema = None
                    
                    # 方法1: 尝试使用args_schema (LangChain工具常用)
                    if hasattr(tool, 'args_schema') and tool.args_schema:
                        if isinstance(tool.args_schema, dict):
                            schema = tool.args_schema
                        elif hasattr(tool.args_schema, 'model_json_schema'):
                            schema = tool.args_schema.model_json_schema()
                    
                    # 方法2: 如果没有args_schema，尝试tool_call_schema
                    if not schema and hasattr(tool, 'tool_call_schema') and tool.tool_call_schema:
                        schema = tool.tool_call_schema
                    
                    # 方法3: 最后尝试input_schema
                    if not schema and hasattr(tool, 'input_schema') and tool.input_schema:
                        if isinstance(tool.input_schema, dict):
                            schema = tool.input_schema
                        elif hasattr(tool.input_schema, 'model_json_schema'):
                            try:
                                schema = tool.input_schema.model_json_schema()
                            except:
                                pass
                    
                    # 解析schema
                    if schema and isinstance(schema, dict):
                        if 'properties' in schema:
                            tool_info["parameters"] = schema['properties']
                            tool_info["required"] = schema.get('required', [])
                        elif 'type' in schema and schema.get('type') == 'object' and 'properties' in schema:
                            tool_info["parameters"] = schema['properties']
                            tool_info["required"] = schema.get('required', [])
                
                except Exception as e:
                    # 如果出错，至少保留工具的基本信息
                    print(f"⚠️ 获取工具 '{tool.name}' 参数信息失败: {e}")
                
                tools_info.append(tool_info)
            
            # 添加服务器信息
            servers_info[server_name] = {
                "name": server_name,
                "tools": tools_info,
                "tool_count": len(tools_info)
            }
            
            total_tools += len(tools_info)
        
        return {
            "servers": servers_info,
            "total_tools": total_tools,
            "server_count": len(servers_info)
        }
    
    async def chat(self, message: str, verbose: bool = True) -> str:
        """与用户对话，使用MCP工具
        
        Args:
            message: 用户消息
            verbose: 是否显示详细的工具调用过程
            
        Returns:
            AI回复
        """
        if not self.agent:
            return "❌ MCP代理未初始化，请先调用 initialize() 方法"
        
        try:
            # 添加用户消息到历史记录
            self.conversation_history.append(HumanMessage(content=message))
            
            if verbose:
                print(f"\n🔄 开始处理用户消息: {message}")
                print("=" * 60)
            
            # 使用agent处理消息
            response = await self.agent.ainvoke({
                "messages": self.conversation_history
            })
            
            if verbose:
                print("\n📋 完整对话流程:")
                print("-" * 40)
                
                # 显示所有消息的详细信息
                for i, msg in enumerate(response["messages"]):
                    msg_type = type(msg).__name__
                    
                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                        print(f"\n[{i+1}] 🤖 AI消息 ({msg_type}):")
                        print(f"内容: {msg.content}")
                        print(f"🔧 工具调用 ({len(msg.tool_calls)} 个):")
                        
                        for j, tool_call in enumerate(msg.tool_calls):
                            print(f"  [{j+1}] 工具名称: {tool_call['name']}")
                            print(f"      调用ID: {tool_call.get('id', 'N/A')}")
                            print(f"      参数: {json.dumps(tool_call['args'], indent=6, ensure_ascii=False)}")
                    
                    elif hasattr(msg, 'tool_call_id'):
                        print(f"\n[{i+1}] 🔧 工具返回结果:")
                        print(f"工具调用ID: {msg.tool_call_id}")
                        print(f"返回内容: {msg.content}")
                    
                    else:
                        print(f"\n[{i+1}] 👤 {msg_type}:")
                        print(f"内容: {msg.content}")
                
                print("\n" + "=" * 60)
            
            # 获取最后的AI回复
            ai_response = response["messages"][-1].content
            
            # 添加AI回复到历史记录
            self.conversation_history.append(AIMessage(content=ai_response))
            
            return ai_response
            
        except Exception as e:
            error_msg = f"❌ 对话处理失败: {e}"
            print(error_msg)
            return error_msg
    
    def clear_history(self):
        """清空对话历史"""
        self.conversation_history = []
        print("🧹 对话历史已清空")
    
    async def close(self):
        """关闭MCP客户端"""
        if self.client:
            try:
                # 检查客户端是否有close方法
                if hasattr(self.client, 'close'):
                    await self.client.close()
                    print("✅ MCP客户端已关闭")
                else:
                    print("✅ MCP客户端连接已断开")
            except Exception as e:
                print(f"⚠️ 关闭MCP客户端时出错: {e}")


async def interactive_chat():
    """交互式聊天界面"""
    print("🤖 MCP工具对话系统")
    print("=" * 50)
    
    # 创建MCP代理
    agent = MCPAgent()
    
    try:
        # 初始化代理
        print("🔄 正在初始化MCP代理...")
        await agent.initialize()
        
        # 显示可用工具信息
        tools_info = agent.get_tools_info()
        print(f"\n📋 可用工具概览:")
        for server_name, server_info in tools_info["servers"].items():
            print(f"  📡 服务器: {server_name} ({server_info['tool_count']} 个工具)")
            for tool in server_info["tools"]:
                print(f"    🔧 {tool['name']}: {tool['description']}")
        
        print("\n💬 开始对话 (输入 'quit' 退出, 'clear' 清空历史, 'tools' 查看工具):")
        print("-" * 50)
        
        while True:
            try:
                # 获取用户输入
                user_input = input("\n👤 您: ").strip()
                
                if user_input.lower() == 'quit':
                    print("👋 再见！")
                    break
                elif user_input.lower() == 'clear':
                    agent.clear_history()
                    continue
                elif user_input.lower() == 'tools':
                    tools_info = agent.get_tools_info()
                    print(json.dumps(tools_info, indent=2, ensure_ascii=False))
                    continue
                elif not user_input:
                    continue
                
                # 处理用户消息
                response = await agent.chat(user_input, verbose=True)
                print(f"\n🤖 最终回复: {response}")
                
            except KeyboardInterrupt:
                print("\n👋 再见！")
                break
            except Exception as e:
                print(f"\n❌ 处理消息时出错: {e}")
    
    finally:
        # 关闭代理
        await agent.close()


async def demo_usage():
    """演示用法"""
    print("🚀 MCP工具演示")
    print("=" * 30)
    
    # 创建代理
    agent = MCPAgent()
    
    try:
        # 初始化
        await agent.initialize()
        
        # 演示对话
        demo_messages = [
            "你好，你能做什么？",
            "查询苹果公司的股价信息",
            "分析一下最近的市场趋势"
        ]
        
        for message in demo_messages:
            print(f"\n👤 用户: {message}")
            response = await agent.chat(message, verbose=True)
            print(f"\n🤖 最终回复: {response}")
            print("-" * 50)
    
    finally:
        await agent.close()


if __name__ == "__main__":
    # 选择运行模式
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        # 演示模式
        asyncio.run(demo_usage())
    else:
        # 交互模式
        asyncio.run(interactive_chat())