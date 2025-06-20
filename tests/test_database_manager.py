import os
import tempfile
from utils.database import DatabaseManager

def setup_db(tmp_path):
    db_path = os.path.join(tmp_path, 'test.db')
    db = DatabaseManager(db_path)
    return db

def test_get_table_names(tmp_path):
    db = setup_db(tmp_path)
    tables = db.get_table_names()
    assert 'downloads' in tables
    db.close()

def test_search_files(tmp_path):
    db = setup_db(tmp_path)
    dl = db.add_download_record('site')
    img_path = os.path.join(tmp_path, 'img.png')
    with open(img_path, 'wb') as f:
        f.write(b'0')
    db.add_file(dl, 'tag1 tag2', '2020-01-01', '2020-01-02', 'url', img_path, '', '')
    headers, rows = db.search_files(['tag1'], [])
    assert rows and rows[0][headers.index('post_tags')].startswith('tag1')
    db.close()

def test_get_latest_config(tmp_path):
    db = setup_db(tmp_path)
    assert db.get_latest_config() is None
    cfg = {"a": 1}
    db.add_config(cfg)
    loaded = db.get_latest_config()
    assert loaded == cfg
    db.close()

def test_fetch_table_limits(tmp_path):
    db = setup_db(tmp_path)
    dl = db.add_download_record('site')
    img_path = os.path.join(tmp_path, 'img1.png')
    with open(img_path, 'wb') as f:
        f.write(b'0')
    img_path2 = os.path.join(tmp_path, 'img2.png')
    with open(img_path2, 'wb') as f:
        f.write(b'1')
    # add two distinct rows
    db.add_file(dl, 'tag1', '2020-01-01', '2020-01-01', 'url1', img_path, '', '')
    db.add_file(dl, 'tag2', '2020-01-02', '2020-01-02', 'url2', img_path2, '', '')

    headers, rows = db.fetch_table('files', limit=None)
    assert len(rows) == 2

    headers, rows = db.fetch_table('files', limit=1)
    assert len(rows) == 1
    db.close()

