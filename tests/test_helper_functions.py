import utils.helper_functions as hf


def test_get_os_delimiter_windows(monkeypatch):
    monkeypatch.setattr(hf.os, 'name', 'nt')
    assert hf.get_OS_delimeter() == '\\'


def test_get_os_delimiter_non_windows(monkeypatch):
    monkeypatch.setattr(hf.os, 'name', 'posix')
    assert hf.get_OS_delimeter() == '/'


def test_from_padded_removes_leading_zero():
    assert hf.from_padded('05') == 5


def test_from_padded_returns_int_when_unpadded():
    assert hf.from_padded('12') == 12


def test_from_padded_single_digit():
    assert hf.from_padded('7') == 7


def test_gather_media_tags(tmp_path):
    folder = tmp_path / "data"
    folder.mkdir()

    # create png
    (folder / "img1.png").write_bytes(b"1")
    (folder / "img1.txt").write_text("tag1,tag2")

    # create webp
    (folder / "img2.webp").write_bytes(b"1")
    (folder / "img2.txt").write_text("tag3")

    result = hf.gather_media_tags(str(folder))
    assert "png" in result and "webp" in result
    assert result["png"]["img1"] == ["tag1", "tag2"]
    assert result["webp"]["img2"] == ["tag3"]
    assert "searched" in result


def test_sort_tags_by_priority():
    tags = ["tagA", "artist1", "2024", "charA", "dog"]

    def cat(tag):
        mapping = {
            "charA": "character",
            "dog": "species",
            "artist1": "artist",
            "tagA": "general",
        }
        return mapping.get(tag, "invalid")

    sorted_tags = hf.sort_tags_by_priority(tags, cat)
    assert sorted_tags == ["charA", "dog", "artist1", "2024", "tagA"]
