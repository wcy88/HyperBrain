"""一次性迁移脚本：重新生成现有长期记忆的嵌入向量

用法：
    py rebuild_embeddings.py [--batch-size 100]

会将 `memory.db` 中所有长期记忆的 embedding 字段从旧的随机向量
升级为新的确定性文本嵌入向量，从而让 AI 能真正"记住"之前的内容。
"""
import sys
import os
import argparse

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hyperbrain.core.config import get_config
from hyperbrain.layers.memory.memory_manager import MemoryManager
from loguru import logger


def main():
    parser = argparse.ArgumentParser(description="重建长期记忆的嵌入向量")
    parser.add_argument("--batch-size", type=int, default=200, help="每批处理的记忆数量")
    args = parser.parse_args()

    config = get_config()
    db_path = config.memory.db_path

    if not os.path.exists(db_path):
        logger.error(f"数据库文件不存在: {db_path}")
        return 1

    logger.info(f"开始重建嵌入向量，db={db_path}, batch_size={args.batch_size}")

    mm = MemoryManager(db_path=db_path, vector_dim=config.memory.vector_dim, enable_faiss=False)
    total = len(mm.long_term_memory)
    logger.info(f"总共需要重建 {total} 条记忆的嵌入")

    rebuilt = mm.long_term_memory.rebuild_embeddings(batch_size=args.batch_size)
    logger.info(f"成功重建 {rebuilt} 条记忆的嵌入")

    # 显示统计
    stats = mm.get_stats()
    ltm = stats["long_term_memory"]
    logger.info(f"完成后统计: total={ltm['total_memories']}, faiss={ltm['faiss_enabled']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
