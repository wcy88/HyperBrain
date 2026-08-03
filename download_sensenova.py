"""
下载并分析 SenseNova-Skills
"""
import os
import urllib.request
import zipfile
from pathlib import Path


def download_github_repo(repo_url: str, extract_to: Path):
    """下载 GitHub 仓库"""
    # 转换为 zipball URL
    zip_url = f"{repo_url}/archive/refs/heads/main.zip"
    zip_path = extract_to / "sensenova-skills.zip"
    
    print(f"下载: {zip_url}")
    
    try:
        urllib.request.urlretrieve(zip_url, zip_path)
        print(f"下载完成: {zip_path}")
        
        # 解压
        print("解压中...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        
        # 重命名目录
        extracted_dir = extract_to / "SenseNova-Skills-main"
        target_dir = extract_to / "sensenova-skills"
        
        if extracted_dir.exists():
            if target_dir.exists():
                import shutil
                shutil.rmtree(target_dir)
            extracted_dir.rename(target_dir)
            print(f"移动到: {target_dir}")
        
        # 删除 zip 文件
        os.remove(zip_path)
        print("清理完成")
        
        return target_dir
    except Exception as e:
        print(f"下载失败: {e}")
        return None


if __name__ == "__main__":
    base_dir = Path(__file__).parent
    target_dir = download_github_repo(
        "https://github.com/opensensenova/sensenova-skills",
        base_dir
    )
    
    if target_dir and target_dir.exists():
        print("\n" + "=" * 60)
        print("下载成功！分析目录结构...")
        print("=" * 60)
        
        # 分析 skills 目录
        skills_dir = target_dir / "skills"
        if skills_dir.exists():
            print(f"\nSkills 目录 ({skills_dir}):")
            for item in sorted(skills_dir.iterdir()):
                if item.is_dir():
                    print(f"\n📁 {item.name}")
                    # 列出文件
                    for f in item.iterdir():
                        print(f"   📄 {f.name}")
        
        print("\n" + "=" * 60)
        print(f"所有文件已下载到: {target_dir}")
        print("=" * 60)
