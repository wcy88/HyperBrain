#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HyperBrain 打包脚本

支持 Windows / Linux / macOS 跨平台打包
功能：
- 自动清理旧构建文件
- 支持单文件/单目录模式
- 自动组织输出文件
- 生成便携版压缩包

使用方法:
    python build.py                    # 默认单目录模式
    python build.py --onefile          # 单文件模式
    python build.py --clean            # 清理并重新构建
    python build.py --portable         # 生成便携版压缩包
"""

import argparse
import os
import platform
import shutil
import subprocess
import sys
import zipfile
import tarfile
from datetime import datetime
from pathlib import Path

# 项目信息
PROJECT_NAME = "HyperBrain"
VERSION = "0.2.0"
AUTHOR = "HyperBrain Team"
DESCRIPTION = "拟人脑认知架构系统"

# 路径配置
PROJECT_ROOT = Path(__file__).parent.resolve()
BUILD_DIR = PROJECT_ROOT / "build"
DIST_DIR = PROJECT_ROOT / "dist"
SPEC_FILE = PROJECT_ROOT / "hyperbrain.spec"
OUTPUT_DIR = PROJECT_ROOT / "output"

# 平台信息
SYSTEM = platform.system().lower()
MACHINE = platform.machine().lower()
PLATFORM_TAG = f"{SYSTEM}-{MACHINE}"


def print_banner():
    """打印构建横幅"""
    print("=" * 60)
    print(f" {PROJECT_NAME} 构建系统")
    print(f" 版本: {VERSION}")
    print(f" 平台: {PLATFORM_TAG}")
    print(f" Python: {sys.version.split()[0]}")
    print("=" * 60)
    print()


def clean_build():
    """清理构建文件"""
    print("[1/5] 清理旧构建文件...")
    
    dirs_to_clean = [BUILD_DIR, DIST_DIR, OUTPUT_DIR]
    files_to_clean = [PROJECT_ROOT / f"{PROJECT_NAME}.spec"]
    
    for dir_path in dirs_to_clean:
        if dir_path.exists():
            print(f"  删除目录: {dir_path}")
            shutil.rmtree(dir_path)
    
    for file_path in files_to_clean:
        if file_path.exists():
            print(f"  删除文件: {file_path}")
            file_path.unlink()
    
    # 清理 __pycache__
    for pycache in PROJECT_ROOT.rglob("__pycache__"):
        if pycache.is_dir():
            shutil.rmtree(pycache)
    
    # 清理 .pyc 文件
    for pyc in PROJECT_ROOT.rglob("*.pyc"):
        pyc.unlink()
    
    print("  清理完成")
    print()


def install_dependencies():
    """安装依赖"""
    print("[2/5] 检查依赖...")
    
    requirements = PROJECT_ROOT / "requirements.txt"
    if not requirements.exists():
        print("  警告: requirements.txt 不存在")
        return
    
    # 检查 PyInstaller
    try:
        import PyInstaller
        print(f"  PyInstaller 已安装: {PyInstaller.__version__}")
    except ImportError:
        print("  安装 PyInstaller...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "pyinstaller>=6.3.0"],
            check=True
        )
    
    print("  依赖检查完成")
    print()


def build_executable(onefile: bool = False, console: bool = True):
    """构建可执行文件"""
    print("[3/5] 构建可执行文件...")
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        str(SPEC_FILE),
        "--noconfirm",
    ]
    
    if onefile:
        cmd.append("--onefile")
    else:
        cmd.append("--onedir")
    
    if console:
        cmd.append("--console")
    else:
        cmd.append("--windowed")
    
    print(f"  执行: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, capture_output=False, text=True)
    
    if result.returncode != 0:
        print("  错误: 构建失败")
        sys.exit(1)
    
    print("  构建完成")
    print()


def organize_output(onefile: bool = False):
    """组织输出文件"""
    print("[4/5] 组织输出文件...")
    
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # 构建输出目录名
    build_type = "onefile" if onefile else "onedir"
    output_name = f"{PROJECT_NAME}-{VERSION}-{PLATFORM_TAG}-{build_type}"
    target_dir = OUTPUT_DIR / output_name
    
    if target_dir.exists():
        shutil.rmtree(target_dir)
    target_dir.mkdir(parents=True)
    
    # 复制构建产物
    dist_path = DIST_DIR / PROJECT_NAME
    
    if onefile:
        # 单文件模式
        exe_name = PROJECT_NAME
        if SYSTEM == "windows":
            exe_name += ".exe"
        
        source = DIST_DIR / exe_name
        if source.exists():
            shutil.copy2(source, target_dir / exe_name)
            print(f"  复制: {exe_name}")
    else:
        # 单目录模式
        if dist_path.exists():
            shutil.copytree(dist_path, target_dir / PROJECT_NAME)
            print(f"  复制目录: {PROJECT_NAME}/")
    
    # 复制文档
    docs_dir = PROJECT_ROOT / "docs"
    if docs_dir.exists():
        target_docs = target_dir / "docs"
        shutil.copytree(docs_dir, target_docs)
        print("  复制文档: docs/")
    
    # 复制配置文件示例
    env_example = PROJECT_ROOT / ".env.example"
    if env_example.exists():
        shutil.copy2(env_example, target_dir / ".env.example")
        print("  复制: .env.example")
    
    # 复制 README
    readme = PROJECT_ROOT / "README.md"
    if readme.exists():
        shutil.copy2(readme, target_dir / "README.md")
        print("  复制: README.md")
    
    # 创建启动脚本
    create_launcher(target_dir, onefile)
    
    print(f"  输出目录: {target_dir}")
    print("  组织完成")
    print()
    
    return target_dir


def create_launcher(target_dir: Path, onefile: bool):
    """创建启动脚本"""
    if SYSTEM == "windows":
        launcher = target_dir / "启动 HyperBrain.bat"
        exe_path = PROJECT_NAME if onefile else f"{PROJECT_NAME}\\{PROJECT_NAME}.exe"
        content = f"""@echo off
chcp 65001 >nul
echo ==========================================
echo  {PROJECT_NAME} - {DESCRIPTION}
echo  版本: {VERSION}
echo ==========================================
echo.

REM 检查 .env 文件
if not exist .env (
    echo 首次运行，请配置 .env 文件
    copy .env.example .env
    echo 已创建 .env 文件，请编辑后重新运行
    pause
    exit /b 1
)

REM 启动程序
{exe_path} --mode gui

pause
"""
        launcher.write_text(content, encoding="utf-8")
    else:
        launcher = target_dir / "start.sh"
        exe_path = f"./{PROJECT_NAME}" if onefile else f"./{PROJECT_NAME}/{PROJECT_NAME}"
        content = f"""#!/bin/bash
# {PROJECT_NAME} 启动脚本

echo "=========================================="
echo " {PROJECT_NAME} - {DESCRIPTION}"
echo " 版本: {VERSION}"
echo "=========================================="
echo

# 检查 .env 文件
if [ ! -f .env ]; then
    echo "首次运行，请配置 .env 文件"
    cp .env.example .env
    echo "已创建 .env 文件，请编辑后重新运行"
    exit 1
fi

# 启动程序
{exe_path} --mode gui
"""
        launcher.write_text(content, encoding="utf-8")
        launcher.chmod(0o755)
    
    print(f"  创建启动脚本: {launcher.name}")


def create_portable_package(target_dir: Path):
    """创建便携版压缩包"""
    print("[5/5] 创建便携版压缩包...")
    
    archive_name = target_dir.name
    
    if SYSTEM == "windows":
        # ZIP 格式
        archive_path = OUTPUT_DIR / f"{archive_name}.zip"
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_path in target_dir.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(target_dir)
                    zf.write(file_path, arcname)
        print(f"  创建: {archive_path.name}")
    else:
        # tar.gz 格式
        archive_path = OUTPUT_DIR / f"{archive_name}.tar.gz"
        with tarfile.open(archive_path, "w:gz") as tf:
            tf.add(target_dir, arcname=target_dir.name)
        print(f"  创建: {archive_path.name}")
    
    # 计算文件大小
    size = archive_path.stat().st_size
    size_mb = size / (1024 * 1024)
    print(f"  大小: {size_mb:.2f} MB")
    print("  便携版创建完成")
    print()
    
    return archive_path


def print_summary(output_dir: Path, archive_path: Path = None):
    """打印构建摘要"""
    print("=" * 60)
    print(" 构建摘要")
    print("=" * 60)
    print(f" 项目名称: {PROJECT_NAME}")
    print(f" 版本: {VERSION}")
    print(f" 平台: {PLATFORM_TAG}")
    print(f" 输出目录: {output_dir}")
    if archive_path:
        print(f" 压缩包: {archive_path}")
    print()
    print(" 文件列表:")
    for item in sorted(output_dir.iterdir()):
        if item.is_dir():
            print(f"   [DIR]  {item.name}/")
        else:
            size = item.stat().st_size
            if size > 1024 * 1024:
                size_str = f"{size / (1024 * 1024):.2f} MB"
            elif size > 1024:
                size_str = f"{size / 1024:.2f} KB"
            else:
                size_str = f"{size} B"
            print(f"   [FILE] {item.name} ({size_str})")
    print()
    print("=" * 60)
    print(" 构建完成!")
    print("=" * 60)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description=f"{PROJECT_NAME} 打包脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python build.py                    # 默认单目录模式
  python build.py --onefile          # 单文件模式
  python build.py --clean            # 清理并重新构建
  python build.py --portable         # 生成便携版压缩包
  python build.py --windowed         # 无控制台窗口（仅GUI）
        """
    )
    
    parser.add_argument(
        "--onefile",
        action="store_true",
        help="单文件模式（所有内容打包到一个可执行文件中）"
    )
    
    parser.add_argument(
        "--clean",
        action="store_true",
        help="清理旧构建文件后重新构建"
    )
    
    parser.add_argument(
        "--portable",
        action="store_true",
        help="生成便携版压缩包"
    )
    
    parser.add_argument(
        "--windowed",
        action="store_true",
        help="无控制台窗口（仅GUI模式）"
    )
    
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="跳过构建，仅组织输出文件"
    )
    
    args = parser.parse_args()
    
    print_banner()
    
    # 清理
    if args.clean:
        clean_build()
    
    # 安装依赖
    install_dependencies()
    
    # 构建
    if not args.skip_build:
        build_executable(
            onefile=args.onefile,
            console=not args.windowed
        )
    
    # 组织输出
    target_dir = organize_output(onefile=args.onefile)
    
    # 创建便携版
    archive_path = None
    if args.portable:
        archive_path = create_portable_package(target_dir)
    
    # 摘要
    print_summary(target_dir, archive_path)


if __name__ == "__main__":
    main()
