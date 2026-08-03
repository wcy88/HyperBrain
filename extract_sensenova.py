"""
解压 SenseNova-Skills
"""
import os
import zipfile
from pathlib import Path


def extract_and_analyze(zip_path: Path, base_dir: Path):
    """解压并分析"""
    if not zip_path.exists():
        print(f"ZIP 文件不存在: {zip_path}")
        return
    
    print(f"解压: {zip_path}")
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(base_dir)
        print("解压完成")
        
        # 重命名目录
        extracted_dir = base_dir / "SenseNova-Skills-main"
        target_dir = base_dir / "sensenova-skills"
        
        if extracted_dir.exists():
            if target_dir.exists():
                import shutil
                shutil.rmtree(target_dir)
            extracted_dir.rename(target_dir)
            print(f"移动到: {target_dir}")
        
        # 删除 zip 文件
        os.remove(zip_path)
        print("清理完成")
        
        # 分析 skills 目录
        skills_dir = target_dir / "skills"
        if skills_dir.exists():
            print("\n" + "=" * 60)
            print("SenseNova Skills 目录结构:")
            print("=" * 60)
            
            for item in sorted(skills_dir.iterdir()):
                if item.is_dir():
                    print(f"\n📁 {item.name}")
                    for f in item.iterdir():
                        print(f"   📄 {f.name}")
        
        print("\n" + "=" * 60)
        print(f"分析完成！文件位于: {target_dir}")
        print("=" * 60)
        
    except Exception as e:
        print(f"处理失败: {e}")


if __name__ == "__main__":
    base_dir = Path(__file__).parent
    zip_path = base_dir / "sensenova-skills.zip"
    extract_and_analyze(zip_path, base_dir)
