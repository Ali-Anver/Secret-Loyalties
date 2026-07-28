"""Repo-relative paths, so every script works from any working directory."""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
CHECKPOINTS = RESULTS / "checkpoints"
FIGURES = ROOT / "figures"

for _d in (RESULTS, CHECKPOINTS, FIGURES):
    _d.mkdir(parents=True, exist_ok=True)


def result(name):
    """Resolve a results filename; accepts a bare name or an existing path."""
    p = pathlib.Path(name)
    return str(p if p.is_absolute() or p.exists() else RESULTS / p.name)


def checkpoint(name):
    p = pathlib.Path(name)
    return str(p if p.is_absolute() or p.exists() else CHECKPOINTS / p.name)


def figure(name):
    return str(FIGURES / pathlib.Path(name).name)
