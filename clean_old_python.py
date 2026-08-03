import os
import shutil
import sys
import ctypes
import time

print("=" * 60)
print("HyperBrain - 清理旧版本Python")
print("=" * 60)

paths_to_remove = [
    r"E:\software\python311",
    os.path.abspath("venv_old")
]

success = True
for path in paths_to_remove:
    if os.path.exists(path):
        try:
            print(f"\n正在删除: {path}")
            # 尝试多种方法
            try:
                if os.path.isfile(path):
                    os.remove(path)
                else:
                    shutil.rmtree(path)
            except PermissionError:
                print("   权限被拒绝，尝试更改属性...")
                # 尝试更改文件属性
                for root, dirs, files in os.walk(path):
                    for d in dirs:
                        try:
                            os.chmod(os.path.join(root, d), 0o777)
                        except:
                            pass
                    for f in files:
                        try:
                            os.chmod(os.path.join(root, f), 0o777)
                        except:
                            pass
                time.sleep(0.5)
                shutil.rmtree(path)
            print(f"✅ {path} 已删除")
        except Exception as e:
            print(f"❌ 删除失败: {path}")
            print(f"   错误: {e}")
            print(f"   请手动删除: {path}")
            success = False
    else:
        print(f"ℹ️  不存在: {path}")

print("\n" + "=" * 60)
if success:
    print("✅ 清理完成！")
    print("\n当前环境:")
    print(f"  Python: {sys.version}")
    print(f"  虚拟环境: venv (Python 3.14.5)")
else:
    print("⚠️ 部分清理需要手动处理")
print("=" * 60)
