from pathlib import Path


def test_horus_spec_does_not_exclude_unittest():
    spec_text = Path("horus.spec").read_text(encoding="utf-8")

    assert "'unittest'" not in spec_text
