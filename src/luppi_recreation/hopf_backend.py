"""Locate and load the upstream compiled Hopf extension."""

from importlib import machinery, util
from pathlib import Path
from types import ModuleType


def load_hopf_extension(upstream_root: str | Path) -> ModuleType:
    """Load the compiled ``hopf`` module from the upstream repository root."""

    upstream_root = Path(upstream_root)
    candidates: list[Path] = []
    for suffix in machinery.EXTENSION_SUFFIXES:
        candidates.extend(upstream_root.glob(f"hopf*{suffix}"))

    candidates = sorted(set(candidates))
    if not candidates:
        raise FileNotFoundError(
            "Compiled Hopf extension not found. Run "
            "'python cpp/build_hopf.py' from the upstream repository first."
        )
    if len(candidates) > 1:
        raise RuntimeError(f"Multiple compiled Hopf extensions found: {candidates}")

    extension_path = candidates[0]
    spec = util.spec_from_file_location("hopf", extension_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to create an import specification for {extension_path}")

    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
