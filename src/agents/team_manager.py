# 智能体团队管理器

import asyncio
import json
import yaml
from typing import Dict, List, Any, Optional
from datetime import datetime
from .base_agent import BaseAgent
from ..prompts.technical_analyst import TECHNICAL_ANALYST_PROMPT
from ..prompts.fundamental_analyst import FUNDAMENTAL_ANALYST_PROMPT
from ..prompts.quantitative_analyst import QUANTITATIVE_ANALYST_PROMPT
from ..prompts.sentiment_analyst import SENTIMENT_ANALYST_PROMPT
from ..prompts.risk_manager import RISK_MANAGER_PROMPT

class AgentTeamManager:
    """智能体团队管理器，负责协调多个分析师智能体的协作"""
    
    def __init__(self, config_file: str = "config.yaml", mcp_config_file: str = "mcp.json"):
        self.config_file = config_file
        self.mcp_config_file = mcp_config_file
        self.config = self._load_config()
        self.mcp_config = self._load_mcp_config()
        self.agents = {}
        self.debate_history = []
        self.analysis_results = []
        self.final_decisions = []
        
    def _load_config(self) -> Dict[str, Any]:
        """加载主配置文件（不包含MCP配置）"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"配置文件 {self.config_file} 不存在，请确保配置文件存在")
        except Exception as e:
            raise Exception(f"加载配置文件失败: {e}")
    
    def _load_mcp_config(self) -> Dict[str, Any]:
        """加载MCP配置文件"""
        try:
            with open(self.mcp_config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"MCP配置文件 {self.mcp_config_file} 不存在，请确保MCP配置文件存在")
        except Exception as e:
            raise Exception(f"加载MCP配置文件失败: {e}")
    

    
    async def initialize_team(self):
        """初始化智能体团队"""
        print("🚀 开始初始化智能体团队...")
        
        # 定义智能体配置
        agent_configs = [
            ("technical_analyst", "技术分析师", TECHNICAL_ANALYST_PROMPT),
            ("fundamental_analyst", "基本面分析师", FUNDAMENTAL_ANALYST_PROMPT),
            ("quantitative_analyst", "量化分析师", QUANTITATIVE_ANALYST_PROMPT),
            ("sentiment_analyst", "市场情绪分析师", SENTIMENT_ANALYST_PROMPT),
            ("risk_manager", "风险管理师", RISK_MANAGER_PROMPT)
        ]
        
        # 初始化每个智能体
        for agent_key, role, prompt in agent_configs:
            try:
                agent_config = self.config["agents"].get(agent_key, {})
                agent_name = agent_config.get("name", role)
                
                # 创建智能体实例
                agent = BaseAgent(
                    name=agent_name,
                    role=role,
                    prompt=prompt,
                    model_config=agent_config
                )
                
                # 初始化MCP连接
                await agent.initialize_mcp(self.mcp_config)
                
                self.agents[agent_key] = agent
                print(f"✅ {agent_name} 初始化成功")
                
            except Exception as e:
                print(f"❌ {agent_key} 初始化失败: {e}")
        
        print(f"🎉 团队初始化完成，共有 {len(self.agents)} 个智能体")
    
    async def analyze_stock(self, stock_code: str) -> Dict[str, Any]:
        """团队分析股票"""
        print(f"\n📊 开始团队分析股票: {stock_code}")
        
        if not self.agents:
            return {"error": "团队未初始化"}
        
        analysis_results = []
        
        # 并行执行各智能体的分析
        tasks = []
        for agent_key, agent in self.agents.items():
            task = agent.analyze(stock_code)
            tasks.append(task)
        
        # 等待所有分析完成
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理分析结果
        for i, (agent_key, result) in enumerate(zip(self.agents.keys(), results)):
            if isinstance(result, Exception):
                print(f"❌ {agent_key} 分析失败: {result}")
                analysis_results.append({
                    "agent_key": agent_key,
                    "error": str(result)
                })
            else:
                analysis_results.append(result)
                print(f"✅ {result.get('agent_name', agent_key)} 分析完成")
        
        # 保存分析结果
        self.analysis_results = analysis_results
        
        return {
            "stock_code": stock_code,
            "analysis_results": analysis_results,
            "timestamp": datetime.now().isoformat()
        }
    
    async def conduct_debate(self, stock_code: str, analysis_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """进行团队辩论"""
        print(f"\n🗣️ 开始团队辩论: {stock_code}")
        
        debate_topic = f"关于股票 {stock_code} 的投资策略讨论"
        debate_rounds = []
        
        # 初始观点（基于分析结果）
        current_opinions = analysis_results.copy()
        
        round_num = 1
        debate_ended = False
        
        while not debate_ended:
            print(f"\n🔄 第 {round_num} 轮辩论")
            
            round_responses = []
            agents_completed = set()
            agents_ended = set()
            
            # 每个智能体基于其他智能体的观点进行回应
            for agent_key, agent in self.agents.items():
                try:
                    # 获取其他智能体的观点
                    other_opinions = [op for op in current_opinions 
                                    if op.get('agent_name') != agent.name]
                    
                    # 生成辩论回应
                    response = await agent.debate_response(debate_topic, other_opinions)
                    
                    # 检查停止标记
                    if self._check_agent_completion(response, agent_key):
                        agents_completed.add(agent_key)
                    
                    if self._check_agent_debate_end(response, agent_key):
                        agents_ended.add(agent_key)
                    
                    round_response = {
                        "round": round_num,
                        "agent_name": agent.name,
                        "role": agent.role,
                        "response": response,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    round_responses.append(round_response)
                    print(f"💬 {agent.name} 发表观点")
                    
                except Exception as e:
                    print(f"❌ {agent.name} 辩论回应失败: {e}")
            
            # 更新当前观点为本轮回应
            current_opinions = round_responses
            debate_rounds.extend(round_responses)
            
            # 检查是否应该结束辩论
            if len(agents_completed) >= len(self.agents) * 0.8 or len(agents_ended) >= 1:
                print(f"✅ 第 {round_num} 轮辩论结束条件满足，结束辩论")
                debate_ended = True
            elif round_num >= 10:  # 安全限制，防止无限循环
                print(f"⚠️ 达到最大轮次限制，强制结束辩论")
                debate_ended = True
            
            round_num += 1
            
            # 轮次间隔
            if not debate_ended:
                await asyncio.sleep(1)
        
        # 保存辩论历史
        self.debate_history = debate_rounds
        
        print(f"🏁 辩论结束，共进行 {round_num-1} 轮")
        return debate_rounds
    
    def _check_agent_completion(self, response: str, agent_key: str) -> bool:
        """检查智能体是否完成分析"""
        completion_markers = {
            "technical_analyst": "[技术分析完成]",
            "fundamental_analyst": "[基本面分析完成]",
            "quantitative_analyst": "[量化分析完成]",
            "sentiment_analyst": "[情绪分析完成]",
            "risk_manager": "[风险分析完成]"
        }
        
        marker = completion_markers.get(agent_key, "[分析完成]")
        return marker in response
    
    def _check_agent_debate_end(self, response: str, agent_key: str) -> bool:
        """检查智能体是否要求结束辩论"""
        end_markers = {
            "technical_analyst": "[辩论结束-技术分析师]",
            "fundamental_analyst": "[辩论结束-基本面分析师]",
            "quantitative_analyst": "[辩论结束-量化分析师]",
            "sentiment_analyst": "[辩论结束-情绪分析师]",
            "risk_manager": "[辩论结束-风险管理师]"
        }
        
        marker = end_markers.get(agent_key, "[辩论结束]")
        return marker in response
    
    async def make_final_decisions(self, stock_code: str) -> List[Dict[str, Any]]:
        """做出最终投资决策"""
        print(f"\n🎯 开始最终决策: {stock_code}")
        
        # 构建分析和辩论总结
        analysis_summary = self._create_analysis_summary()
        
        final_decisions = []
        
        # 每个智能体基于完整信息做出最终决策
        for agent_key, agent in self.agents.items():
            try:
                decision = await agent.make_decision(analysis_summary)
                final_decisions.append(decision)
                print(f"✅ {agent.name} 决策完成")
                
            except Exception as e:
                print(f"❌ {agent.name} 决策失败: {e}")
                final_decisions.append({
                    "agent_name": agent.name,
                    "role": agent.role,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
        
        # 保存最终决策
        self.final_decisions = final_decisions
        
        return final_decisions
    
    def _create_analysis_summary(self) -> str:
        """创建分析和辩论总结"""
        summary = "## 团队分析总结\n\n"
        
        # 添加初始分析结果
        summary += "### 初始分析结果\n"
        for result in self.analysis_results:
            if "error" not in result:
                summary += f"**{result.get('agent_name', '未知')}({result.get('role', '未知')})**:\n"
                summary += f"{result.get('analysis', '')}\n\n"
        
        # 添加辩论要点
        if self.debate_history:
            summary += "### 辩论要点\n"
            for debate in self.debate_history:
                summary += f"**{debate.get('agent_name', '未知')}** (第{debate.get('round', 0)}轮):\n"
                summary += f"{debate.get('response', '')}\n\n"
        
        return summary
    
    def get_team_status(self) -> Dict[str, Any]:
        """获取团队状态"""
        agent_statuses = {}
        for agent_key, agent in self.agents.items():
            agent_statuses[agent_key] = agent.get_status()
        
        return {
            "team_size": len(self.agents),
            "agents": agent_statuses,
            "analysis_count": len(self.analysis_results),
            "debate_rounds": len(set(d.get('round', 0) for d in self.debate_history)),
            "decisions_count": len(self.final_decisions),
            "last_activity": datetime.now().isoformat()
        }
    
    async def close_team(self):
        """关闭团队，清理资源"""
        print("🔄 正在关闭智能体团队...")
        
        for agent_key, agent in self.agents.items():
            try:
                await agent.close()
                print(f"✅ {agent.name} 已关闭")
            except Exception as e:
                print(f"❌ 关闭 {agent.name} 失败: {e}")
        
        print("👋 团队已关闭")
    
    def export_results(self, filename: str = None) -> str:
        """导出分析结果"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"analysis_results_{timestamp}.json"
        
        results = {
            "analysis_results": self.analysis_results,
            "debate_history": self.debate_history,
            "final_decisions": self.final_decisions,
            "team_status": self.get_team_status(),
            "export_time": datetime.now().isoformat()
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"📄 结果已导出到: {filename}")
            return filename
        except Exception as e:
            print(f"❌ 导出失败: {e}")
            return ""