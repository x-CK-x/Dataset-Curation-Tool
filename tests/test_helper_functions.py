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
