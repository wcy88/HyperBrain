"""
测试 SenseNova Skills 安装和运行
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hyperbrain.gateway import Gateway


async def test_sensenova_skills():
    """测试 SenseNova Skills"""
    print("=" * 70)
    print("HyperBrain SenseNova Skills 安装测试")
    print("=" * 70)
    
    # 设置环境变量（用于演示）
    os.environ.setdefault("SENSENOVA_API_KEY", "your-api-key-here")
    
    gateway = Gateway()
    await gateway.initialize()
    
    print("\n1. 列出所有 Skills（包含 SenseNova）")
    skills = gateway.list_skills()
    print(f"\n找到 {len(skills)} 个 Skills:\n")
    
    # 分类显示
    sensenova_skills = []
    builtin_skills = []
    
    for skill in skills:
        name = skill['name']
        if name.startswith('sn_'):
            sensenova_skills.append(skill)
        else:
            builtin_skills.append(skill)
    
    print("📦 内置 Skills:")
    for skill in builtin_skills:
        info = skill.get('info', {})
        print(f"  - {skill['name']}: {info.get('description', 'N/A')}")
    
    print("\n🧠 SenseNova Skills (商汤):")
    for skill in sensenova_skills:
        info = skill.get('info', {})
        print(f"  - {skill['name']}: {info.get('description', 'N/A')}")
    
    print("\n" + "=" * 70)
    print("2. 测试 SenseNova Skills 调用")
    print("=" * 70)
    
    # 测试各个 SenseNova Skill
    test_cases = [
        ("图像生成", "sn_image_generate", {"prompt": "一只可爱的熊猫在吃竹子"}),
        ("PPT生成", "sn_ppt_generate", {"topic": "人工智能发展趋势", "slides": 10}),
        ("数据分析", "sn_data_analysis", {"file_path": "example.xlsx", "analysis_type": "summary"}),
        ("深度研究", "sn_deep_research", {"topic": "量子计算最新进展", "depth": "standard"}),
        ("网络搜索", "sn_web_search", {"query": "Python 3.14 新特性", "platform": "all"}),
        ("信息图生成", "sn_infographic", {"content": "年度销售报告数据", "layout": "auto"}),
    ]
    
    for name, skill_name, params in test_cases:
        print(f"\n测试 {name} ({skill_name}):")
        result = await gateway.skill_loader.execute_skill(skill_name, **params)
        print(f"  状态: {'✅ 成功' if result.success else '❌ 失败'}")
        if result.success:
            print(f"  消息: {result.message}")
        else:
            print(f"  错误: {result.error}")
    
    print("\n" + "=" * 70)
    print("3. 测试 Gateway 消息处理（自然语言）")
    print("=" * 70)
    
    test_messages = [
        "生成一张机器人的图片",
        "制作一个关于AI的PPT，20页",
        "搜索最新的深度学习论文",
        "研究量子计算的发展现状",
    ]
    
    for msg in test_messages:
        print(f"\n用户: {msg}")
        result = await gateway.process_message(msg)
        print(f"系统: {result['message']}")
    
    print("\n" + "=" * 70)
    print("✅ SenseNova Skills 安装和测试完成！")
    print("=" * 70)
    
    print("\n📋 使用说明:")
    print("1. 要使用 SenseNova API，请设置环境变量:")
    print("   SENSENOVA_API_KEY=你的API密钥")
    print("   SENSENOVA_API_URL=https://api.sensenova.cn/v1")
    print("\n2. 或者在代码中设置:")
    print("   os.environ['SENSENOVA_API_KEY'] = '你的API密钥'")
    print("\n3. 查看 GitHub 获取更多技能:")
    print("   https://github.com/opensensenova/sensenova-skills")


if __name__ == "__main__":
    asyncio.run(test_sensenova_skills())
