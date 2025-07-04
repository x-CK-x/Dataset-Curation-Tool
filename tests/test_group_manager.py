import utils.group_manager as gm


def test_save_and_load():
    groups = {}
    items = [["png", "a"], ["jpg", "b"]]
    groups = gm.save_group(groups, "grp1", items)
    assert "grp1" in groups
    loaded = gm.load_groups(groups, ["grp1"])
    assert sorted(loaded) == sorted(items)


def test_delete_group():
    groups = gm.save_group({}, "grp1", [["png", "a"]])
    groups = gm.delete_groups(groups, ["grp1"])
    assert groups == {}


def test_rename_duplicate():
    groups = gm.save_group({}, "g1", [["png", "a"]])
    groups = gm.rename_group(groups, "g1", "g2")
    assert "g2" in groups and "g1" not in groups
    groups = gm.duplicate_group(groups, "g2", "g3")
    assert groups["g2"] == groups["g3"]


def test_file_roundtrip(tmp_path):
    groups = gm.save_group({}, "grp", [["png", "1"], ["jpg", "2"]])
    fp = tmp_path / "groups.json"
    gm.save_groups_file(groups, fp)
    loaded = gm.load_groups_file(fp)
    assert loaded == groups
