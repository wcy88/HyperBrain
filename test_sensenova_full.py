"""
完整测试：SenseNova Skills 官方集成
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hyperbrain.skills import SkillLoader
from hyperbrain.skills.sensenova_integration import (
    initialize_sensenova_skills,
    get_sensenova_loader,
)


async def test_full_integration():
    """测试完整集成"""
    print("=" * 80)
    print("SenseNova Skills 官方集成 - 完整测试")
    print("=" * 80)

    # 1. 初始化
    print("\n[1/5] 初始化 SenseNova Skills...")
    count = initialize_sensenova_skills()
    print(f"加载了 {count} 个 SenseNova Skills")

    sn_loader = get_sensenova_loader()
    if sn_loader:
        # 2. 列出所有技能
        print("\n[2/5] 列出所有 SenseNova Skills...")
        skills = sn_loader.list_skills()

        print(f"\n找到 {len(skills)} 个官方 Skills:")
        for idx, skill in enumerate(skills, 1):
            category = skill.get("metadata", {}).get("category", "unknown")
            user_visible = skill.get("metadata", {}).get("user_visible", True)
            visibility = "用户可见" if user_visible else "基础设施"

            print(f"\n{idx}. {skill['name']} ({category})")
            print(f"   可见性: {visibility}")

            desc = skill.get("description", "")[:100]
            if desc:
                print(f"   描述: {desc}...")

            if skill.get("triggers"):
                print(f"   触发器: {skill['triggers'][:3]}")

        # 3. 分类统计
        print("\n" + "=" * 80)
        print("[3/5] 分类统计")
        print("=" * 80)

        categories = {}
        for skill in skills:
            cat = skill.get("metadata", {}).get("category", "unknown")
            categories[cat] = categories.get(cat, 0) + 1

        for cat, cnt in sorted(categories.items()):
            print(f"  {cat}: {cnt} 个 Skills")

        # 4. 测试 SkillLoader 集成
        print("\n" + "=" * 80)
        print("[4/5] 测试 SkillLoader 集成")
        print("=" * 80)

        loader = SkillLoader()
        total_loaded = loader.load_skills()
        print(f"SkillLoader 共加载 {total_loaded} 个 Skills")

        # 5. 执行一个示例 Skill
        print("\n" + "=" * 80)
        print("[5/5] 测试执行一个 SenseNova Skill")
        print("=" * 80)

        if skills:
            first_skill = skills[0]["name"]
            print(f"尝试执行: {first_skill}")

            result = await loader.execute_skill(first_skill)
            print(f"\n执行结果: {'成功' if result.success else '失败'}")
            print(f"消息: {result.message}")

            if result.data:
                print(f"数据: {result.data}")

    print("\n" + "=" * 80)
    print("✅ 测试完成！")
    print("=" * 80)
    print("\n下一步:")
    print("1. 要使用完整的 SenseNova Skills 功能，请配合 OpenClaw 或 hermes-agent")
    print("2. 安装依赖: pip install -r hyperbrain/sensenova_skills/official_skills/.../requirements.txt")
    print("3. 设置 SenseNova API Key: export SN_API_KEY=your-key")


if __name__ == "__main__":
    asyncio.run(test_full_integration())
