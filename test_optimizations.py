"""
测试新的优化功能

验证 Skill 系统和 Gateway 网关
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hyperbrain.gateway import Gateway


async def test_gateway():
    """测试 Gateway"""
    print("=" * 60)
    print("测试 Gateway")
    print("=" * 60)
    
    gateway = Gateway()
    await gateway.initialize()
    
    print("\n1. 列出所有 Skills")
    skills = gateway.list_skills()
    print(f"找到 {len(skills)} 个 Skills:")
    for skill in skills:
        print(f"  - {skill['name']}: {skill.get('info', {}).get('description', '')}")
    
    print("\n2. 测试消息处理")
    test_messages = [
        "你好",
        "技能列表",
        "计算 2 + 3",
        "系统信息",
        "计算 10 * 5"
    ]
    
    for msg in test_messages:
        print(f"\n  用户: {msg}")
        result = await gateway.process_message(msg)
        print(f"  系统: {result['message']}")
        if result.get('data'):
            print(f"  数据: {result['data']}")
        if 'execution_time_ms' in result:
            print(f"  耗时: {result['execution_time_ms']:.2f}ms")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


async def test_skills_direct():
    """直接测试 Skills"""
    from hyperbrain.skills import SkillLoader
    
    print("=" * 60)
    print("直接测试 Skills")
    print("=" * 60)
    
    loader = SkillLoader()
    count = loader.load_skills()
    print(f"\n加载了 {count} 个 Skills")
    
    # 测试计算器
    print("\n测试计算器 Skill:")
    calc_result = await loader.execute_skill("calculator", expression="25 * 4")
    print(f"  25 * 4 = {calc_result.data['result']} (success={calc_result.success})")
    
    # 测试系统信息
    print("\n测试系统信息 Skill:")
    sys_result = await loader.execute_skill("system_info", info_type="basic")
    if sys_result.success:
        print(f"  Python: {sys_result.data['python']['version']}")
        print(f"  OS: {sys_result.data['os']['system']}")


if __name__ == "__main__":
    print("HyperBrain v0.3.0 优化测试\n")
    asyncio.run(test_gateway())
    print("\n" + "=" * 60 + "\n")
    asyncio.run(test_skills_direct())
