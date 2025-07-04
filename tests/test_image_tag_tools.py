import os
from utils.image_tag_tools import (
    load_image_tags,
    transfer_tags,
    invert_selection,
    compare_tags,
    apply_tag_modifications,
)


def test_load_and_transfer_tags(tmp_path):
    img1 = tmp_path / "img1.png"
    img2 = tmp_path / "img2.png"
    img1.write_bytes(b"1")
    img2.write_bytes(b"1")
    (tmp_path / "img1.txt").write_text("tagA\ntagB\n")
    (tmp_path / "img2.txt").write_text("tagB\n")

    tags = load_image_tags(str(img1))
    assert tags == ["tagA", "tagB"]

    transfer_tags(str(img1), str(img2), ["tagA"], remove=True)

    assert load_image_tags(str(img2)) == ["tagB", "tagA"]
    assert load_image_tags(str(img1)) == ["tagB"]


def test_invert_selection():
    all_items = [1, 2, 3, 4]
    selected = [2, 4]
    assert invert_selection(selected, all_items) == [1, 3]


def test_compare_and_apply(tmp_path):
    img1 = tmp_path / "img1.png"
    img2 = tmp_path / "img2.png"
    img3 = tmp_path / "img3.png"
    for img in (img1, img2, img3):
        img.write_bytes(b"1")

    (tmp_path / "img1.txt").write_text("a\nb\nc")
    (tmp_path / "img2.txt").write_text("b\nc\nd")
    (tmp_path / "img3.txt").write_text("c")

    diff = compare_tags(str(img1), str(img2))
    assert diff["a_only"] == ["a"]
    assert diff["b_only"] == ["d"]
    assert diff["common"] == ["b", "c"]

    apply_tag_modifications([str(img3)], add_tags=diff["a_only"], remove_tags=[])
    assert load_image_tags(str(img3)) == ["a", "c"]


def test_apply_modifications_multiple(tmp_path):
    img1 = tmp_path / "imgA.png"
    img2 = tmp_path / "imgB.png"
    for img in (img1, img2):
        img.write_bytes(b"1")
    (tmp_path / "imgA.txt").write_text("a\nb\n")
    (tmp_path / "imgB.txt").write_text("b\nc\n")

    apply_tag_modifications([str(img1), str(img2)], add_tags=["d"], remove_tags=["a"])

    assert load_image_tags(str(img1)) == ["b", "d"]
    assert load_image_tags(str(img2)) == ["b", "c", "d"]


def test_apply_modifications_strips_newlines(tmp_path):
    img = tmp_path / "imgC.png"
    img.write_bytes(b"1")
    (tmp_path / "imgC.txt").write_text("x\ny\n")

    apply_tag_modifications([str(img)], add_tags=["z\n"], remove_tags=["x\n"])

    assert load_image_tags(str(img)) == ["y", "z"]
