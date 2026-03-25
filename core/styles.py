from functools import lru_cache
from pathlib import Path


STYLES_DIR = Path(__file__).resolve().parent.parent / "styles"


@lru_cache(maxsize=None)
def load_stylesheet(*filenames: str) -> str:
    chunks: list[str] = []
    for filename in filenames:
        path = STYLES_DIR / filename
        chunks.append(path.read_text(encoding="utf-8"))
    return "\n\n".join(chunks)


def apply_stylesheet(widget, *filenames: str) -> None:
    widget.setStyleSheet(load_stylesheet(*filenames))


def repolish(widget) -> None:
    style = widget.style()
    style.unpolish(widget)
    style.polish(widget)
    widget.update()


def set_dynamic_property(widget, name: str, value) -> None:
    widget.setProperty(name, value)
    repolish(widget)
