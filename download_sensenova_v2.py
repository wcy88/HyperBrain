"""
重新下载 SenseNova-Skills
"""
import urllib.request
import zipfile
from pathlib import Path
import time


def download_with_retry(url: str, dest: Path, max_retries: int = 3):
    """带重试的下载"""
    for attempt in range(max_retries):
        try:
            print(f"尝试 {attempt + 1}/{max_retries}...")
            print(f"下载: {url}")
            
            # 添加 User-Agent 头
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            with urllib.request.urlopen(req, timeout=60) as response:
                content = response.read()
                
            print(f"下载完成，大小: {len(content) / 1024:.1f} KB")
            
            with open(dest, 'wb') as f:
                f.write(content)
            
            print(f"保存到: {dest}")
            return True
            
        except Exception as e:
            print(f"尝试 {attempt + 1} 失败: {e}")
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 5
                print(f"等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
    
    return False


def extract_sensenova(zip_path: Path, base_dir: Path):
    """解压"""
    if not zip_path.exists():
        print(f"ZIP 不存在: {zip_path}")
        return False
    
    print(f"\n解压: {zip_path}")
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(base_dir)
        print("解压完成")
        
        # 重命名
        extracted_dir = base_dir / "SenseNova-Skills-main"
        target_dir = base_dir / "sensenova-skills"
        
        if extracted_dir.exists():
            import shutil
            if target_dir.exists():
                shutil.rmtree(target_dir)
            extracted_dir.rename(target_dir)
            print(f"移动到: {target_dir}")
        
        # 分析
        print("\n" + "=" * 60)
        print("SenseNova Skills 目录结构:")
        print("=" * 60)
        
        skills_dir = target_dir / "skills"
        if skills_dir.exists():
            for item in sorted(skills_dir.iterdir()):
                if item.is_dir():
                    print(f"\n📁 {item.name}")
                    for f in item.iterdir():
                        print(f"   📄 {f.name}")
        
        print("\n" + "=" * 60)
        print(f"✅ 安装完成！位置: {target_dir}")
        print("=" * 60)
        
        # 删除 zip
        zip_path.unlink()
        print("清理完成")
        
        return True
        
    except Exception as e:
        print(f"解压失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    base_dir = Path(__file__).parent
    zip_url = "https://github.com/opensensenova/sensenova-skills/archive/refs/heads/main.zip"
    zip_path = base_dir / "sensenova-skills.zip"
    
    # 删除旧文件
    if zip_path.exists():
        zip_path.unlink()
    
    # 下载
    if download_with_retry(zip_url, zip_path):
        # 解压
        extract_sensenova(zip_path, base_dir)
    else:
        print("\n❌ 下载失败！")
