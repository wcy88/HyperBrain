"""
微调触发器

3 个 backend 适配：
- ollama       : HTTP API（modelfile + adapter 占位）
- llamafactory : subprocess + YAML
- unsloth      : subprocess + 脚本

真实微调需要 GPU + 训练框架；本模块在 hyperbrain 现有环境（无 GPU）下做"接口完整 + dry-run 友好"的实现：
- 当 `dry_run=True`（默认）或 backend 不可用时，返回模拟 TrainingRun
- 仍会更新 model_versions.status 流转
"""
from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from hyperbrain.hermes.common import get_hermes_logger

logger = get_hermes_logger("trainer")


@dataclass
class TrainingRun:
    version_id: str
    backend: str
    status: str  # queued / running / done / failed
    started_at: float = 0.0
    ended_at: float = 0.0
    error: str = ""
    adapter_path: str = ""
    dataset_path: str = ""
    base_model: str = ""
    log: List[str] = field(default_factory=list)


class Trainer:
    def __init__(self, config, model_registry):
        self.config = config
        self.registry = model_registry

    async def run(
        self,
        *,
        dataset_path: str,
        base_model: Optional[str] = None,
        dry_run: bool = True,
    ) -> TrainingRun:
        """
        启动一次微调。

        真实环境：dry_run=False 时调用对应 backend 子进程
        沙箱 / 测试：dry_run=True（默认）→ 10s 后返回 done，写占位 adapter 文件
        """
        version_id = self.registry.register(
            base_model=base_model or self.config.base_model,
            dataset_path=dataset_path,
            metadata={"backend": self.config.backend, "dry_run": dry_run},
        )
        run = TrainingRun(
            version_id=version_id,
            backend=self.config.backend,
            status="running",
            started_at=time.time(),
            base_model=base_model or self.config.base_model,
            dataset_path=dataset_path,
        )
        self.registry.update_status(version_id, "running")

        try:
            if dry_run or not self._backend_available():
                run.log.append(
                    f"[dry_run] backend={self.config.backend} unavailable or dry_run=True, "
                    f"simulating training"
                )
                await asyncio.sleep(0.1)  # 模拟耗时
                run.adapter_path = self._write_placeholder_adapter(run)
                run.status = "done"
            else:
                if self.config.backend == "ollama":
                    await self._run_ollama(run)
                elif self.config.backend == "llamafactory":
                    await self._run_llamafactory(run)
                elif self.config.backend == "unsloth":
                    await self._run_unsloth(run)
                else:
                    raise ValueError(f"unknown backend: {self.config.backend}")
                run.status = "done"
        except Exception as e:  # noqa: BLE001
            run.status = "failed"
            run.error = f"{type(e).__name__}: {e}"
            logger.error(f"training run {version_id} failed: {e}")
        finally:
            run.ended_at = time.time()
            self.registry.update_status(version_id, run.status)

        return run

    # ---------- backends ----------

    def _backend_available(self) -> bool:
        if self.config.backend == "ollama":
            return True  # 通过 HTTP API 调用
        if self.config.backend in {"llamafactory", "unsloth"}:
            return shutil.which(self.config.backend) is not None
        return False

    async def _run_ollama(self, run: TrainingRun) -> None:
        """
        Ollama 走 Modelfile + adapter（占位）。
        真实生产应使用 ollama create + 自定义 Modelfile + GGUF 导出。
        """
        run.log.append("[ollama] preparing Modelfile + adapter symlink")
        Path(self.config.adapter_dir).mkdir(parents=True, exist_ok=True)
        run.adapter_path = self._write_placeholder_adapter(run)

    async def _run_llamafactory(self, run: TrainingRun) -> None:
        """LLaMA-Factory：subprocess 调 llamafactory-cli train。"""
        cfg = Path(self.config.working_dir) / f"llamafactory_{run.version_id}.yaml"
        cfg.write_text(self._llamafactory_yaml(run), encoding="utf-8")
        cmd = ["llamafactory-cli", "train", str(cfg)]
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
        )
        stdout, _ = await proc.communicate()
        run.log.append(stdout.decode("utf-8", errors="ignore")[:5000])
        if proc.returncode != 0:
            raise RuntimeError(f"llamafactory exit {proc.returncode}")
        run.adapter_path = str(Path(self.config.adapter_dir) / run.version_id)

    async def _run_unsloth(self, run: TrainingRun) -> None:
        """unsloth：subprocess 调 python 训练脚本（占位）。"""
        script = Path(self.config.working_dir) / f"unsloth_{run.version_id}.py"
        script.write_text(self._unsloth_script(run), encoding="utf-8")
        cmd = ["python", str(script)]
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
        )
        stdout, _ = await proc.communicate()
        run.log.append(stdout.decode("utf-8", errors="ignore")[:5000])
        if proc.returncode != 0:
            raise RuntimeError(f"unsloth exit {proc.returncode}")
        run.adapter_path = str(Path(self.config.adapter_dir) / run.version_id)

    # ---------- 辅助 ----------

    def _write_placeholder_adapter(self, run: TrainingRun) -> str:
        Path(self.config.adapter_dir).mkdir(parents=True, exist_ok=True)
        p = Path(self.config.adapter_dir) / f"{run.version_id}.placeholder"
        p.write_text(
            json.dumps(
                {
                    "version_id": run.version_id,
                    "base_model": run.base_model,
                    "dataset": run.dataset_path,
                    "created_at": time.time(),
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return str(p)

    def _llamafactory_yaml(self, run: TrainingRun) -> str:
        return (
            f"model_name_or_path: {run.base_model}\n"
            f"output_dir: {self.config.adapter_dir}/{run.version_id}\n"
            f"train_file: {run.dataset_path}\n"
            f"stage: sft\n"
            f"do_train: true\n"
            f"finetuning_type: lora\n"
            f"lora_target: q_proj,v_proj\n"
        )

    def _unsloth_script(self, run: TrainingRun) -> str:
        return (
            "from unsloth import FastLanguageModel\n"
            "import sys\n"
            f"model, tokenizer = FastLanguageModel.from_pretrained('{run.base_model}')\n"
            f"# dataset: {run.dataset_path}\n"
            "print('train stub done')\n"
        )
