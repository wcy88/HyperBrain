"""
测试增强后的自然语言识别
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hyperbrain.gateway import Gateway


async def test_natural_language():
    """测试自然语言处理"""
    print("=" * 70)
    print("HyperBrain SenseNova 自然语言识别测试")
    print("=" * 70)
    
    gateway = Gateway()
    await gateway.initialize()
    
    test_messages = [
        "生成一张机器人的图片",
        "制作一个关于AI的PPT，20页",
        "搜索最新的深度学习论文",
        "研究量子计算的发展现状",
        "帮我分析一下销售数据",
        "制作一个关于区块链的信息图",
        "技能列表",
    ]
    
    print("\n测试自然语言识别：\n")
    
    for msg in test_messages:
        print(f"用户: {msg}")
        result = await gateway.process_message(msg)
        print(f"系统: {result['message']}")
        print(f"执行时间: {result.get('execution_time_ms', 0):.2f}ms")
        print("-" * 70)
    
    print("\n✅ 测试完成！")


if __name__ == "__main__":
    asyncio.run(test_natural_language())
