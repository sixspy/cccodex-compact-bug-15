import pytest

from app.seed import reset_seed


@pytest.fixture()
def db(tmp_path):
    path = str(tmp_path / "t.db")
    reset_seed(path)
    return path
