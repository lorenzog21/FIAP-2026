import os
import sys

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)


@pytest.fixture
def pasta_tmp(tmp_path, monkeypatch):
    """Os modulos usam caminhos relativos (data/...); roda cada teste numa pasta limpa."""
    monkeypatch.chdir(tmp_path)
    return tmp_path
