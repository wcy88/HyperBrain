"""
完整下载和安装SenseNova-Skills
"""
import os
import sys
import shutil
import zipfile
from pathlib import Path
import urllib.request
import time


def download_with_progress(url: str, dest: Path) -> bool:
    """带进度条下载"""
    print(f"正在下载: {url}")
    try:
        def report_progress(block_num, block_size, total_size):
            downloaded = block_num * block_size
            percent = min(100, int(downloaded * 100 / total_size))
            sys.stdout.write(f"\r  下载进度: {percent}% ({downloaded/1024/1024:.1f} MB / {total_size/1024/1024:.1f} MB)")
            sys.stdout.flush()
        
        urllib.request.urlretrieve(url, dest, reporthook=report_progress)
        print("\n  下载完成!")
        return True
    except Exception as e:
        print(f"\n  下载失败: {e}")
        return False


def extract_zip(zip_path: Path, extract_to: Path) -> bool:
    """解压zip文件"""
    print(f"正在解压: {zip_path}")
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        print("  解压完成!")
        return True
    except Exception as e:
        print(f"  解压失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def organize_directory(base_dir: Path):
    """整理目录结构"""
    print(f"整理目录: {base_dir}")
    extract_dir = base_dir / "SenseNova-Skills-main"
    target_dir = base_dir / "sensenova-skills"
    
    if target_dir.exists():
        print(f"  删除旧目录: {target_dir}")
        shutil.rmtree(target_dir)
    
    if extract_dir.exists():
        print(f"  重命名: {extract_dir} -> {target_dir}")
        extract_dir.rename(target_dir)
        return target_dir
    else:
        return None


def analyze_structure(target_dir: Path):
    """分析目录结构"""
    print("\n" + "=" * 60)
    print("SenseNova-Skills 目录结构分析:")
    print("=" * 60)
    
    skills_dir = target_dir / "skills"
    if skills_dir.exists():
        print("\n📁 技能目录:")
        for skill_dir in sorted(skills_dir.iterdir()):
            if skill_dir.is_dir():
                print(f"\n  📁 {skill_dir.name}")
                for file in sorted(skill_dir.iterdir()):
                    print(f"    📄 {file.name}")
    
    # 查看README
    readme_cn = target_dir / "README_CN.md"
    if readme_cn.exists():
        print("\n📖 中文README存在")
    
    readme_en = target_dir / "README.md"
    if readme_en.exists():
        print("📖 英文README存在")
    
    print("\n" + "=" * 60)
    return skills_dir.exists()


def integrate_to_hyperbrain(target_dir: Path, hyperbrain_dir: Path):
    """将SenseNova-Skills集成到HyperBrain"""
    print("\n" + "=" * 60)
    print("集成到HyperBrain:")
    print("=" * 60)
    
    # 1. 创建sensenova_skills目录
    sn_skills_dir = hyperbrain_dir / "hyperbrain" / "sensenova_skills"
    if not sn_skills_dir.exists():
        sn_skills_dir.mkdir(parents=True)
        print(f"✅ 创建目录: {sn_skills_dir}")
    
    # 2. 复制skills目录
    source_skills = target_dir / "skills"
    dest_skills = sn_skills_dir / "official_skills"
    if source_skills.exists() and source_skills.is_dir():
        if dest_skills.exists():
            shutil.rmtree(dest_skills)
        shutil.copytree(source_skills, dest_skills)
        print(f"✅ 复制Skills: {source_skills} -> {dest_skills}")
    
    # 3. 复制docs
    source_docs = target_dir / "docs"
    dest_docs = sn_skills_dir / "official_docs"
    if source_docs.exists() and source_docs.is_dir():
        if dest_docs.exists():
            shutil.rmtree(dest_docs)
        shutil.copytree(source_docs, dest_docs)
        print(f"✅ 复制Docs: {source_docs} -> {dest_docs}")
    
    # 4. 复制README
    for readme_name in ["README.md", "README_CN.md"]:
        readme = target_dir / readme_name
        if readme.exists():
            shutil.copy(readme, sn_skills_dir / readme_name)
            print(f"✅ 复制README: {readme_name}")
    
    print("\n" + "=" * 60)
    print("集成完成!")
    print("=" * 60)
    
    return sn_skills_dir


def create_bridge_file(sn_skills_dir: Path, hyperbrain_dir: Path):
    """创建桥接文件，让HyperBrain能正确加载SenseNova Skills"""
    print("\n创建桥接文件...")
    
    bridge_content = '''"""
SenseNova Skills 官方集成
本目录包含来自OpenSenseNova/SenseNova-Skills的官方Skills
"""
import os
import sys
from pathlib import Path

SENSENOVA_DIR = Path(__file__).parent
OFFICIAL_SKILLS_DIR = SENSENOVA_DIR / "official_skills"

def get_official_skills_list():
    """获取官方Skill列表"""
    if not OFFICIAL_SKILLS_DIR.exists():
        return []
    
    skills = []
    for skill_dir in OFFICIAL_SKILLS_DIR.iterdir():
        if skill_dir.is_dir() and not skill_dir.name.startswith("_"):
            skills.append(skill_dir.name)
    
    return sorted(skills)

# 信息
__version__ = "0.1.0"
__author__ = "OpenSenseNova"
'''
    
    bridge_file = sn_skills_dir / "__init__.py"
    bridge_file.write_text(bridge_content, encoding="utf-8")
    print(f"✅ 创建桥接文件: {bridge_file}")
    
    # 创建README
    readme_content = '''# SenseNova-Skills 官方集成

本目录包含来自GitHub仓库 [OpenSenseNova/SenseNova-Skills](https://github.com/opensensenova/sensenova-skills) 的官方Skills

## 目录结构

- `official_skills/` - 官方Skills目录
- `official_docs/` - 官方文档目录

## 使用方法

参考官方文档了解如何使用这些Skills。
'''
    readme_file = sn_skills_dir / "README_INTEGRATION.md"
    readme_file.write_text(readme_content, encoding="utf-8")
    print(f"✅ 创建README: {readme_file}")


def main():
    """主函数"""
    base_dir = Path(__file__).parent
    zip_path = base_dir / "sensenova-skills.zip"
    
    print("=" * 70)
    print("SenseNova-Skills 完整安装程序")
    print("=" * 70)
    
    # 1. 下载
    url = "https://github.com/opensensenova/sensenova-skills/archive/refs/heads/main.zip"
    print("\n[步骤 1/5] 下载仓库...")
    if not download_with_progress(url, zip_path):
        print("\n❌ 下载失败")
        return
    
    # 2. 解压
    print("\n[步骤 2/5] 解压文件...")
    if not extract_zip(zip_path, base_dir):
        print("\n❌ 解压失败")
        return
    
    # 3. 整理目录
    print("\n[步骤 3/5] 整理目录...")
    target_dir = organize_directory(base_dir)
    if not target_dir:
        print("\n❌ 目录整理失败")
        return
    
    # 4. 分析结构
    print("\n[步骤 4/5] 分析结构...")
    has_skills = analyze_structure(target_dir)
    
    # 5. 集成到HyperBrain
    print("\n[步骤 5/5] 集成到HyperBrain...")
    sn_skills_dir = integrate_to_hyperbrain(target_dir, base_dir)
    create_bridge_file(sn_skills_dir, base_dir)
    
    # 清理zip
    if zip_path.exists():
        zip_path.unlink()
        print("\n✅ 清理zip文件")
    
    print("\n" + "=" * 70)
    print("✅ SenseNova-Skills 完整安装成功!")
    print("=" * 70)
    print(f"\n安装位置: {sn_skills_dir}")
    print(f"\n可用Skills: {len(get_official_skills_list(target_dir))} 个")


def get_official_skills_list(target_dir: Path):
    """获取Skill列表"""
    skills_dir = target_dir / "skills"
    if not skills_dir.exists():
        return []
    
    skills = []
    for skill_dir in sorted(skills_dir.iterdir()):
        if skill_dir.is_dir() and not skill_dir.name.startswith("_"):
            skills.append(skill_dir.name)
    
    return skills


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n操作已取消")
    except Exception as e:
        print(f"\n\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
