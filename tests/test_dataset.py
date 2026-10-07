from structroute.data.dataset import inspect_splits, normalize_code


def test_normalize_code_collapses_whitespace() -> None:
    assert normalize_code("int  f() {\n return 0; } ") == "int f() { return 0; }"


def test_inspection_finds_cross_split_duplicates() -> None:
    splits = {
        "train": [
            {"func": "int f() { return 0; }", "target": False, "project": "a"},
            {"func": "int g() { return 1; }", "target": True, "project": "b"},
        ],
        "validation": [
            {"func": "int  f() {\nreturn 0; }", "target": False, "project": "a"},
            {"func": "int g() { return 1; }", "target": True, "project": "b"},
        ],
    }

    report = inspect_splits(splits)

    assert report["splits"]["train"]["label_counts"] == {0: 1, 1: 1}
    assert report["cross_split_duplicates"] == {
        "exact_hashes": 1,
        "whitespace_normalized_hashes": 2,
    }

