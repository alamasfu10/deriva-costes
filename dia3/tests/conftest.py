import shutil
from pathlib import Path

import pytest

import main

DB_ORIGINAL = Path(__file__).resolve().parent.parent / "datos" / "deriva.db"


@pytest.fixture
def db(tmp_path, monkeypatch):
    """Copia de la base de datos de ejemplo. Los tests nunca tocan la original."""
    copia = tmp_path / "deriva.db"
    shutil.copy(DB_ORIGINAL, copia)
    monkeypatch.setattr(main, "RUTA_DB", str(copia))
    return copia
