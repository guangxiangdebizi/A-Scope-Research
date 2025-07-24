#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A-Scope Research - 金融智能体团队主入口
基于MCP的中国A股市场分析系统

使用方法:
1. 命令行模式: python main.py --mode cli --stock 000001
2. Web界面模式: python main.py --mode web
3. 演示模式: python main.py --mode demo
"""

import argparse
import asyncio
import sys
import os
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.dirname(__file__))

from src.agents.team_manager import AgentTeamManager

def print_banner():
    """打印系统横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                    A-Scope Research                         ║
║                   金融智能体团队分析系统                        ║
║                                                              ║
║  🤖 技术分析师 | 📊 基本面分析师 | 🔢 量化分析师                ║
║  😊 情绪分析师 | 🛡️ 风险管理师                                ║
║                                                              ║
║  基于MCP协议的中国A股市场智能分析平台                          ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

async def cli_mode(stock_code: str):
    """命令行模式"""
    print(f"\n🚀 启动命令行分析模式 - 股票代码: {stock_code}")
    
    # 初始化团队管理器
    team_manager = AgentTeamManager("config.yaml")
    
    try:
        # 初始化团队
        print("\n📋 正在初始化智能体团队...")
        await team_manager.initialize_team()
        
        # 分析股票
        print(f"\n📊 开始分析股票 {stock_code}...")
        analysis_result = await team_manager.analyze_stock(stock_code)
        
        # 显示分析结果
        print("\n" + "="*60)
        print("📈 初始分析结果")
        print("="*60)
        
        for result in analysis_result.get('analysis_results', []):
            if 'error' not in result:
                print(f"\n🤖 {result.get('agent_name', '未知')} ({result.get('role', '未知')})")
                print("-" * 40)
                print(result.get('analysis', '无分析内容'))
                
                # 显示工具调用
                tool_calls = result.get('tool_calls', [])
                if tool_calls:
                    print("\n🔧 工具调用:")
                    for tool_call in tool_calls:
                        print(f"  - {tool_call.get('tool', '未知工具')}: {tool_call.get('args', {})}")
            else:
                print(f"\n❌ {result.get('agent_name', '未知')} 分析失败: {result.get('error', '未知错误')}")
        
        # 进行团队辩论
        print("\n" + "="*60)
        print("🗣️ 开始团队辩论")
        print("="*60)
        
        debate_results = await team_manager.conduct_debate(stock_code, analysis_result.get('analysis_results', []))
        
        # 显示辩论结果
        current_round = 0
        for debate in debate_results:
            round_num = debate.get('round', 1)
            if round_num != current_round:
                current_round = round_num
                print(f"\n🔄 第 {round_num} 轮辩论")
                print("-" * 40)
            
            print(f"\n💬 {debate.get('agent_name', '未知')} ({debate.get('role', '未知')})")
            print(debate.get('response', '无回应内容'))
        
        # 做出最终决策
        print("\n" + "="*60)
        print("🎯 最终投资决策")
        print("="*60)
        
        final_decisions = await team_manager.make_final_decisions(stock_code)
        
        # 显示最终决策
        for decision in final_decisions:
            if 'error' not in decision:
                print(f"\n🎯 {decision.get('agent_name', '未知')} ({decision.get('role', '未知')})")
                print("-" * 40)
                print(decision.get('decision', '无决策内容'))
            else:
                print(f"\n❌ {decision.get('agent_name', '未知')} 决策失败: {decision.get('error', '未知错误')}")
        
        # 导出结果
        print("\n📄 正在导出分析结果...")
        filename = team_manager.export_results()
        if filename:
            print(f"✅ 结果已导出到: {filename}")
        
        print("\n🎉 分析完成！")
        
    except Exception as e:
        print(f"\n❌ 分析过程中发生错误: {e}")
    
    finally:
        # 清理资源
        await team_manager.close_team()

def web_mode():
    """Web界面模式"""
    print("\n🌐 启动Web界面模式...")
    
    # 加载配置获取端口设置
    try:
        import yaml
        with open('config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        ui_config = config.get('ui', {})
        port = ui_config.get('port', 8501)
        host = ui_config.get('host', 'localhost')
        
        print(f"📱 请在浏览器中访问: http://{host}:{port}")
        
        # 启动Streamlit应用
        import subprocess
        import sys
        
        cmd = [sys.executable, "-m", "streamlit", "run", "src/ui/streamlit_app.py", f"--server.port={port}", f"--server.address={host}"]
        subprocess.run(cmd)
        
    except ImportError:
        print("❌ 未安装streamlit，请运行: pip install streamlit")
    except Exception as e:
        print(f"❌ 启动Web界面失败: {e}")

async def demo_mode():
    """演示模式"""
    print("\n🎭 启动演示模式...")
    
    # 演示股票列表
    demo_stocks = [
        ("000001", "平安银行"),
        ("600036", "招商银行"),
        ("000002", "万科A")
    ]
    
    print("\n📋 演示股票列表:")
    for i, (code, name) in enumerate(demo_stocks, 1):
        print(f"  {i}. {code} - {name}")
    
    try:
        choice = input("\n请选择要分析的股票 (1-3): ").strip()
        choice_idx = int(choice) - 1
        
        if 0 <= choice_idx < len(demo_stocks):
            stock_code, stock_name = demo_stocks[choice_idx]
            print(f"\n✅ 已选择: {stock_code} - {stock_name}")
            
            # 执行分析
            await cli_mode(stock_code)
        else:
            print("❌ 无效选择")
            
    except (ValueError, KeyboardInterrupt):
        print("\n👋 演示已取消")
    except Exception as e:
        print(f"\n❌ 演示过程中发生错误: {e}")

def check_dependencies():
    """检查依赖项"""
    # 包名映射：pip包名 -> 导入名
    required_packages = {
        'langchain-openai': 'langchain_openai',
        'langchain-mcp-adapters': 'langchain_mcp_adapters', 
        'langgraph': 'langgraph',
        'python-dotenv': 'dotenv',
        'pyyaml': 'yaml',
        'streamlit': 'streamlit'
    }
    
    missing_packages = []
    
    for pip_name, import_name in required_packages.items():
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(pip_name)
    
    if missing_packages:
        print("❌ 缺少以下依赖包:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\n请运行以下命令安装:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True

def main():
    """主函数"""
    print_banner()
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description="A-Scope Research - 金融智能体团队分析系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python main.py --mode cli --stock 000001     # 命令行分析平安银行
  python main.py --mode web                    # 启动Web界面
  python main.py --mode demo                   # 演示模式
        """
    )
    
    parser.add_argument(
        "--mode",
        choices=["cli", "web", "demo"],
        default="demo",
        help="运行模式 (默认: demo)"
    )
    
    parser.add_argument(
        "--stock",
        type=str,
        help="股票代码 (仅在cli模式下需要)"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="配置文件路径 (默认: config.yaml)"
    )
    
    args = parser.parse_args()
    
    # 检查配置文件
    if not os.path.exists(args.config):
        print(f"⚠️ 配置文件 {args.config} 不存在，将使用默认配置")
    
    # 根据模式执行
    try:
        if args.mode == "cli":
            if not args.stock:
                print("❌ CLI模式需要指定股票代码，使用 --stock 参数")
                parser.print_help()
                sys.exit(1)
            
            asyncio.run(cli_mode(args.stock))
            
        elif args.mode == "web":
            web_mode()
            
        elif args.mode == "demo":
            asyncio.run(demo_mode())
            
    except KeyboardInterrupt:
        print("\n👋 程序已被用户中断")
    except Exception as e:
        print(f"\n❌ 程序执行失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()