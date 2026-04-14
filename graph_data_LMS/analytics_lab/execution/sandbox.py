"""Launch learner code in a separate process with a timeout.

Trust model (single local user): the learner is also the machine owner, so the
goal is *robustness*, not containment of a malicious adversary. Measures taken:

* code runs in a child process, never inside the Streamlit server process;
* wall-clock timeout, after which the child is killed;
* a fresh temporary working directory that is deleted afterwards;
* a minimal environment (no inherited secrets such as API keys or tokens);
* Python runs in isolated mode (``-I``); on POSIX, memory/CPU rlimits are applied;
* SQL runs read-only with DuckDB external access disabled.

A subprocess is NOT a security boundary. For stronger isolation enable the
optional Docker backend (no network, read-only mounts, memory/CPU/pids caps).
"""

from __future__ import annotations

import json
import os
import secrets
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

from analytics_lab.config import get_paths
from analytics_lab.i18n import t

HARNESS_DIR = Path(__file__).resolve().parent
_ENV_KEEP = ("SYSTEMROOT", "WINDIR", "PATH", "PATHEXT", "NUMBER_OF_PROCESSORS", "PROCESSOR_ARCHITECTURE", "LANG", "LC_ALL", "TZ", "COMSPEC")


@dataclass
class ProcessOutcome:
    payload: dict | None
    stdout: str = ""
    stderr: str = ""
    timed_out: bool = False
    returncode: int | None = None
    duration: float = 0.0
    workdir_files: dict[str, bytes] = field(default_factory=dict)
    error: str | None = None


def safe_env(workdir: Path) -> dict[str, str]:
    env = {k: os.environ[k] for k in _ENV_KEEP if k in os.environ}
    cache = get_paths().data_dir / ".cache"
    (cache / "matplotlib").mkdir(parents=True, exist_ok=True)
    env.update(
        {
            "TEMP": str(workdir),
            "TMP": str(workdir),
            "TMPDIR": str(workdir),
            "HOME": str(workdir),
            "USERPROFILE": str(workdir),
            "MPLBACKEND": "Agg",
            "MPLCONFIGDIR": str(cache / "matplotlib"),  # persistent so the font cache is built once
            "PYTHONIOENCODING": "utf-8",
            "PYTHONDONTWRITEBYTECODE": "1",
            "OMP_NUM_THREADS": "2",
        }
    )
    return env


def _posix_limits(timeout: int):  # pragma: no cover - not used on Windows
    def apply():
        import resource

        mem = 2 * 1024**3
        resource.setrlimit(resource.RLIMIT_AS, (mem, mem))
        resource.setrlimit(resource.RLIMIT_CPU, (timeout + 5, timeout + 10))
        os.setsid()

    return apply


def docker_available() -> bool:
    exe = shutil.which("docker")
    if not exe:
        return False
    try:
        r = subprocess.run([exe, "info", "--format", "{{.ServerVersion}}"], capture_output=True, timeout=8, text=True)
        return r.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def docker_command(image: str, workdir: Path, data_dir: Path, script: str, interpreter: list[str]) -> list[str]:
    """Build a locked-down ``docker run`` invocation (used when backend == 'docker')."""
    return [
        "docker", "run", "--rm", "-i",
        "--network", "none",
        "--memory", "1g", "--cpus", "1", "--pids-limit", "256",
        "--read-only", "--tmpfs", "/tmp:rw,size=64m",
        "--security-opt", "no-new-privileges",
        "-e", "MPLBACKEND=Agg", "-e", "MPLCONFIGDIR=/tmp", "-e", "HOME=/tmp",
        "-v", f"{workdir}:/work",
        "-v", f"{data_dir}:/labdata:ro",
        "-w", "/work",
        image, *interpreter, f"/work/{script}",
    ]


def run_job(
    harness: str,
    job: dict,
    timeout: int,
    backend: str = "local",
    docker_image: str = "analytics-lab-runner:latest",
    interpreter: list[str] | None = None,
    extra_files: dict[str, str] | None = None,
    collect: tuple[str, ...] = (".png",),
) -> ProcessOutcome:
    """Run ``harness`` (a file name in this package, or a script written via
    ``extra_files``) with ``job`` as JSON on stdin and parse the nonce-tagged payload."""
    paths = get_paths()
    nonce = "@@LAB-" + secrets.token_hex(12) + "@@"
    workdir = Path(tempfile.mkdtemp(prefix="lab_run_"))
    try:
        src = HARNESS_DIR / harness
        if src.exists():
            shutil.copy(src, workdir / harness)
        for name, content in (extra_files or {}).items():
            (workdir / name).write_text(content, encoding="utf-8")

        job = dict(job, nonce=nonce)
        if backend == "docker":
            os.chmod(workdir, 0o777)  # the container runs as an unprivileged user and must write figures here
            data_dir = paths.data_dir
            job = _rewrite_for_docker(job, data_dir)
            cmd = docker_command(docker_image, workdir, data_dir, harness, interpreter or ["python", "-I"])
            env = None
            preexec = None
        else:
            job["out_dir"] = str(workdir)
            cmd = [*(interpreter or [sys.executable, "-I", "-X", "utf8"]), str(workdir / harness)]
            env = safe_env(workdir)
            preexec = _posix_limits(timeout) if os.name == "posix" else None

        start = time.perf_counter()
        try:
            proc = subprocess.run(
                cmd,
                input=json.dumps(job),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                cwd=str(workdir),
                env=env,
                preexec_fn=preexec,  # noqa: PLW1509 - only set on POSIX
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0,
            )
        except subprocess.TimeoutExpired as exc:
            return ProcessOutcome(
                payload=None,
                stdout=(exc.stdout or "") if isinstance(exc.stdout, str) else "",
                timed_out=True,
                duration=time.perf_counter() - start,
                error=t("Execution stopped after {n} seconds. Look for infinite loops, very large joins or loops over rows that could be vectorised.", n=timeout),
            )
        except OSError as exc:
            return ProcessOutcome(payload=None, error=f"Could not start the runner: {exc}")
        duration = time.perf_counter() - start

        payload = None
        stdout = proc.stdout or ""
        idx = stdout.rfind(nonce)
        if idx >= 0:
            try:
                payload = json.loads(stdout[idx + len(nonce):].strip().splitlines()[0])
            except (ValueError, IndexError):
                payload = None
            stdout = stdout[:idx]
        files = {}
        for p in workdir.iterdir():
            if p.suffix in collect and p.stat().st_size < 10 * 1024 * 1024:
                files[p.name] = p.read_bytes()
        err = None
        if payload is None:
            err = _crash_message(proc.returncode, proc.stderr)
        return ProcessOutcome(payload, stdout, proc.stderr or "", False, proc.returncode, duration, files, err)
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def _crash_message(code: int | None, stderr: str) -> str:
    tail = (stderr or "").strip().splitlines()[-6:]
    hint = ""
    if code in (-9, 137, 3221225477) or "MemoryError" in (stderr or ""):
        hint = " The process probably ran out of memory; work with a sample or aggregate earlier."
    return f"The runner exited unexpectedly (exit code {code}).{hint}" + ("\n" + "\n".join(tail) if tail else "")


def _rewrite_for_docker(job: dict, data_dir: Path) -> dict:
    """Map host paths under the data directory to the container mount point."""
    out = dict(job)
    for key in ("db_path", "uploads_path", "csv_dir"):
        val = out.get(key)
        if val:
            rel = Path(val).resolve().relative_to(data_dir.resolve())
            out[key] = "/labdata/" + rel.as_posix()
    out["out_dir"] = "/work"
    return out
