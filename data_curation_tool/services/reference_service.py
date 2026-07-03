from __future__ import annotations

import base64
import hashlib
import io
import json
import math
import random
import re
import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Sequence

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps

from ..database import Database, now_iso
from ..paths import AppPaths
from .media_service import MediaService
from .tag_service import TagService
from .annotation_models import AnnotationModelError, parse_json_proposals, propose_with_sam, propose_with_sam2, propose_with_yolo
from .pose_models import propose_with_mediapipe, propose_with_mmpose
from .annotation_classes import inspect_model_classes

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tif', '.tiff', '.jfif'}


class QuerySyntaxError(ValueError):
    pass


@dataclass(frozen=True)
class _Token:
    kind: str
    value: str


@dataclass
class _Node:
    op: str
    value: str | None = None
    children: list['_Node'] | None = None

    def terms(self) -> set[str]:
        if self.op == 'TERM' and self.value:
            return {self.value}
        out: set[str] = set()
        for child in self.children or []:
            out |= child.terms()
        return out


_OPERATORS = {'and': 'AND', 'or': 'OR', 'not': 'NOT'}


def _normalize_query_tag(raw: str) -> str:
    s = (raw or '').strip().strip('"\'')
    low = s.lower()
    for prefix in ('tag:', 'tag=', 'name:', 'name='):
        if low.startswith(prefix):
            s = s[len(prefix):].strip()
            break
    return s.replace(' ', '_').lower()


def _tokenize_query(query: str) -> list[_Token]:
    tokens: list[_Token] = []
    q = (query or '').strip()
    i = 0
    while i < len(q):
        ch = q[i]
        if ch.isspace():
            i += 1
            continue
        if ch in '()':
            tokens.append(_Token(ch, ch)); i += 1; continue
        if q.startswith('&&', i):
            tokens.append(_Token('AND', 'AND')); i += 2; continue
        if q.startswith('||', i):
            tokens.append(_Token('OR', 'OR')); i += 2; continue
        if ch in {'!', '-'}:
            tokens.append(_Token('NOT', 'NOT')); i += 1; continue
        if ch == '[':
            j = q.find(']', i + 1)
            if j < 0:
                raise QuerySyntaxError('Unclosed [tag] expression.')
            content = q[i + 1:j].strip()
            op = _OPERATORS.get(content.lower())
            tokens.append(_Token(op or 'TERM', op or _normalize_query_tag(content)))
            i = j + 1
            continue
        if ch in {'"', "'"}:
            quote = ch; j = i + 1; buf: list[str] = []
            while j < len(q) and q[j] != quote:
                buf.append(q[j]); j += 1
            if j >= len(q):
                raise QuerySyntaxError('Unclosed quoted tag.')
            tokens.append(_Token('TERM', _normalize_query_tag(''.join(buf))))
            i = j + 1
            continue
        j = i
        while j < len(q) and not q[j].isspace() and q[j] not in '()[]!':
            if q.startswith('&&', j) or q.startswith('||', j):
                break
            j += 1
        word = q[i:j]
        op = _OPERATORS.get(word.lower())
        tokens.append(_Token(op or 'TERM', op or _normalize_query_tag(word)))
        i = j
    return _insert_implicit_and(tokens)


def _insert_implicit_and(tokens: Sequence[_Token]) -> list[_Token]:
    out: list[_Token] = []
    prev: _Token | None = None
    for tok in tokens:
        if prev is not None and prev.kind in {'TERM', ')'} and tok.kind in {'TERM', 'NOT', '('}:
            out.append(_Token('AND', 'AND'))
        out.append(tok)
        prev = tok
    return out


class _Parser:
    def __init__(self, tokens: Sequence[_Token]):
        self.tokens = list(tokens)
        self.i = 0

    def peek(self) -> _Token | None:
        return self.tokens[self.i] if self.i < len(self.tokens) else None

    def pop(self) -> _Token:
        tok = self.peek()
        if tok is None:
            raise QuerySyntaxError('Unexpected end of query.')
        self.i += 1
        return tok

    def parse(self) -> _Node:
        if not self.tokens:
            return _Node('ALL')
        node = self.parse_or()
        if self.peek() is not None:
            raise QuerySyntaxError(f'Unexpected token: {self.peek()}')
        return node

    def parse_or(self) -> _Node:
        node = self.parse_and()
        while self.peek() and self.peek().kind == 'OR':
            self.pop()
            node = _Node('OR', children=[node, self.parse_and()])
        return node

    def parse_and(self) -> _Node:
        node = self.parse_not()
        while self.peek() and self.peek().kind == 'AND':
            self.pop()
            node = _Node('AND', children=[node, self.parse_not()])
        return node

    def parse_not(self) -> _Node:
        if self.peek() and self.peek().kind == 'NOT':
            self.pop()
            return _Node('NOT', children=[self.parse_not()])
        return self.parse_primary()

    def parse_primary(self) -> _Node:
        tok = self.pop()
        if tok.kind == 'TERM':
            return _Node('TERM', value=tok.value)
        if tok.kind == '(':
            node = self.parse_or()
            end = self.pop()
            if end.kind != ')':
                raise QuerySyntaxError('Expected closing parenthesis.')
            return node
        raise QuerySyntaxError(f'Expected tag or group, got {tok.kind}')


def _parse_query(query: str) -> _Node:
    return _Parser(_tokenize_query(query)).parse()


def _evaluate_ast(node: _Node, tag_lookup: Callable[[str], set[int]], universe: set[int]) -> set[int]:
    if node.op == 'ALL':
        return set(universe)
    if node.op == 'TERM':
        return set(tag_lookup(node.value or ''))
    if node.op == 'NOT':
        return set(universe) - _evaluate_ast(node.children[0], tag_lookup, universe)  # type: ignore[index]
    if node.op == 'AND':
        return _evaluate_ast(node.children[0], tag_lookup, universe) & _evaluate_ast(node.children[1], tag_lookup, universe)  # type: ignore[index]
    if node.op == 'OR':
        return _evaluate_ast(node.children[0], tag_lookup, universe) | _evaluate_ast(node.children[1], tag_lookup, universe)  # type: ignore[index]
    raise QuerySyntaxError(f'Unknown query op: {node.op}')


def _safe_div(num: float, den: float) -> float:
    return float(num) / float(den) if den else 0.0


def _f1(precision: float, recall: float) -> float:
    return 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0


def _safe_name(name: str) -> str:
    return ''.join(c if c.isalnum() or c in '-_' else '_' for c in (name or 'dataset')).strip('_') or 'dataset'


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def _fingerprint(paths: Sequence[str]) -> str:
    h = hashlib.sha256()
    for path in sorted(str(p) for p in paths):
        p = Path(path).expanduser()
        h.update(str(p).encode('utf-8', errors='replace'))
        if p.exists():
            try:
                h.update(_sha256_file(p).encode('ascii'))
            except Exception:
                pass
    return h.hexdigest()


def _image_meta(path: Path) -> dict[str, Any]:
    size = path.stat().st_size if path.exists() else 0
    width = height = None
    try:
        with Image.open(path) as im:
            width, height = im.size
    except Exception:
        pass
    return {'width': width, 'height': height, 'size_bytes': size, 'sha256': _sha256_file(path) if path.exists() else None}


def _histogram_embedding(path_or_image: Path | Image.Image) -> list[float]:
    import numpy as np
    if isinstance(path_or_image, Image.Image):
        im = path_or_image.convert('RGB')
    else:
        im = Image.open(path_or_image).convert('RGB')
    arr = np.asarray(im.resize((64, 64)), dtype=np.float32) / 255.0
    rows: list[float] = []
    for channel in range(3):
        hist, _ = np.histogram(arr[:, :, channel], bins=32, range=(0.0, 1.0), density=True)
        rows.extend([float(x) for x in hist])
    norm = math.sqrt(sum(x * x for x in rows)) or 1.0
    return [x / norm for x in rows]


def _cosine(a: Sequence[float], b: Sequence[float]) -> float:
    return float(sum(x * y for x, y in zip(a, b))) / max(math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)), 1e-12)


def _bbox_full(media: dict[str, Any]) -> dict[str, float]:
    return {'x1': 0.0, 'y1': 0.0, 'x2': float(media.get('width') or 0), 'y2': float(media.get('height') or 0)}


def _draw_annotation(image_path: Path, bbox: dict[str, Any], score: float, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        im = Image.open(image_path).convert('RGB')
        draw = ImageDraw.Draw(im)
        x1, y1, x2, y2 = float(bbox.get('x1', 0)), float(bbox.get('y1', 0)), float(bbox.get('x2', im.width)), float(bbox.get('y2', im.height))
        draw.rectangle((x1, y1, x2, y2), outline='red', width=max(2, im.width // 500))
        draw.text((x1 + 2, y1 + 2), f'{score:.3f}', fill='white')
        im.save(out_path)
    except Exception:
        pass


class ReferenceService:
    """Reference-image search, verification memory, query optimization, and training-label helpers.

    This service ports the reusable ideas from the prior character-reference prototype into the
    modern FastAPI/SQLite application. It keeps the actual feature work local-first and pluggable:
    a no-model color-hash backend is always available, while SigLIP/OWLv2/SAM/YOLO paths are exposed
    as model-aware contracts for machines with the optional dependencies and weights installed.
    """

    def __init__(self, db: Database, paths: AppPaths, media: MediaService, tags: TagService, models: Any | None = None):
        self.db = db
        self.paths = paths
        self.media = media
        self.tags = tags
        self.models = models
        self._annotation_model_cache: dict[str, Any] = {}
        self._annotation_class_cache: dict[str, dict[str, Any]] = {}
        self.exports_dir = paths.outputs / 'reference_finder'
        self.annotations_dir = paths.outputs / 'annotations'
        self.training_dir = paths.outputs / 'training'
        self.ensure_schema()

    def ensure_schema(self) -> None:
        with self.db._lock, self.db.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS reference_targets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    notes TEXT DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    active INTEGER NOT NULL DEFAULT 1
                );
                CREATE TABLE IF NOT EXISTS reference_images (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    target_id INTEGER NOT NULL REFERENCES reference_targets(id) ON DELETE CASCADE,
                    media_id INTEGER REFERENCES media(id) ON DELETE SET NULL,
                    path TEXT NOT NULL,
                    sha256 TEXT,
                    width INTEGER,
                    height INTEGER,
                    reference_set_name TEXT DEFAULT 'default',
                    created_at TEXT NOT NULL,
                    active INTEGER NOT NULL DEFAULT 1
                );
                CREATE TABLE IF NOT EXISTS reference_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    target_id INTEGER REFERENCES reference_targets(id) ON DELETE SET NULL,
                    name TEXT NOT NULL,
                    pipeline TEXT NOT NULL,
                    threshold REAL NOT NULL DEFAULT 0.55,
                    dataset_id INTEGER REFERENCES datasets(id) ON DELETE SET NULL,
                    folder TEXT DEFAULT '',
                    reference_fingerprint TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'running',
                    params_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    finished_at TEXT,
                    message TEXT DEFAULT ''
                );
                CREATE TABLE IF NOT EXISTS reference_detections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER REFERENCES reference_runs(id) ON DELETE CASCADE,
                    media_id INTEGER NOT NULL REFERENCES media(id) ON DELETE CASCADE,
                    target_id INTEGER REFERENCES reference_targets(id) ON DELETE SET NULL,
                    bbox_json TEXT DEFAULT '{}',
                    score_det REAL,
                    score_embed REAL,
                    score_final REAL,
                    decision TEXT NOT NULL DEFAULT 'unknown',
                    source TEXT NOT NULL DEFAULT 'model',
                    model_meta_json TEXT NOT NULL DEFAULT '{}',
                    crop_path TEXT DEFAULT '',
                    annotated_path TEXT DEFAULT '',
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS reference_verifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    detection_id INTEGER REFERENCES reference_detections(id) ON DELETE CASCADE,
                    media_id INTEGER NOT NULL REFERENCES media(id) ON DELETE CASCADE,
                    target_id INTEGER REFERENCES reference_targets(id) ON DELETE SET NULL,
                    user_label TEXT NOT NULL,
                    notes TEXT DEFAULT '',
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS reference_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    media_id INTEGER NOT NULL REFERENCES media(id) ON DELETE CASCADE,
                    target_id INTEGER REFERENCES reference_targets(id) ON DELETE SET NULL,
                    pipeline TEXT NOT NULL,
                    reference_fingerprint TEXT NOT NULL,
                    best_detection_id INTEGER REFERENCES reference_detections(id) ON DELETE SET NULL,
                    has_target INTEGER NOT NULL DEFAULT 0,
                    verified_label TEXT DEFAULT '',
                    best_score REAL,
                    last_decision TEXT DEFAULT '',
                    updated_at TEXT NOT NULL,
                    UNIQUE(media_id, target_id, pipeline, reference_fingerprint)
                );
                CREATE TABLE IF NOT EXISTS reference_query_trials (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    target_id INTEGER REFERENCES reference_targets(id) ON DELETE SET NULL,
                    query TEXT NOT NULL,
                    baseline_query TEXT DEFAULT '',
                    metrics_json TEXT NOT NULL DEFAULT '{}',
                    result_ids_json TEXT NOT NULL DEFAULT '[]',
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS annotations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    media_id INTEGER NOT NULL REFERENCES media(id) ON DELETE CASCADE,
                    target_id INTEGER REFERENCES reference_targets(id) ON DELETE SET NULL,
                    label TEXT NOT NULL DEFAULT 'object',
                    annotation_type TEXT NOT NULL DEFAULT 'bbox',
                    set_name TEXT NOT NULL DEFAULT 'default',
                    bbox_json TEXT NOT NULL DEFAULT '{}',
                    polygon_json TEXT NOT NULL DEFAULT '[]',
                    mask_path TEXT DEFAULT '',
                    source TEXT NOT NULL DEFAULT 'user',
                    model_key TEXT DEFAULT '',
                    confidence REAL,
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    layer_name TEXT NOT NULL DEFAULT '',
                    z_index INTEGER NOT NULL DEFAULT 0,
                    visible INTEGER NOT NULL DEFAULT 1,
                    opacity REAL NOT NULL DEFAULT 0.55,
                    locked INTEGER NOT NULL DEFAULT 0,
                    blend_mode TEXT NOT NULL DEFAULT 'normal',
                    color TEXT NOT NULL DEFAULT '',
                    parent_ids_json TEXT NOT NULL DEFAULT '[]',
                    revision INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS annotation_revisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    annotation_id INTEGER NOT NULL REFERENCES annotations(id) ON DELETE CASCADE,
                    revision INTEGER NOT NULL,
                    snapshot_json TEXT NOT NULL,
                    reason TEXT NOT NULL DEFAULT 'edit',
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS training_sets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    dataset_id INTEGER REFERENCES datasets(id) ON DELETE SET NULL,
                    query TEXT DEFAULT '',
                    description TEXT DEFAULT '',
                    root_path TEXT DEFAULT '',
                    export_format TEXT DEFAULT 'working_set',
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS training_set_items (
                    training_set_id INTEGER NOT NULL REFERENCES training_sets(id) ON DELETE CASCADE,
                    media_id INTEGER NOT NULL REFERENCES media(id) ON DELETE CASCADE,
                    split TEXT NOT NULL DEFAULT 'train',
                    include_reason TEXT DEFAULT '',
                    created_at TEXT NOT NULL,
                    PRIMARY KEY(training_set_id, media_id)
                );
                CREATE TABLE IF NOT EXISTS training_jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    task TEXT NOT NULL,
                    model_key TEXT DEFAULT '',
                    training_set_id INTEGER REFERENCES training_sets(id) ON DELETE SET NULL,
                    output_dir TEXT DEFAULT '',
                    config_json TEXT NOT NULL DEFAULT '{}',
                    status TEXT NOT NULL DEFAULT 'created',
                    message TEXT DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS training_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    training_job_id INTEGER NOT NULL REFERENCES training_jobs(id) ON DELETE CASCADE,
                    metric_name TEXT NOT NULL,
                    value REAL NOT NULL,
                    step INTEGER,
                    epoch REAL,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_reference_detections_run ON reference_detections(run_id);
                CREATE INDEX IF NOT EXISTS idx_reference_detections_media ON reference_detections(media_id);
                CREATE INDEX IF NOT EXISTS idx_reference_memory_target ON reference_memory(target_id);
                CREATE INDEX IF NOT EXISTS idx_annotations_media ON annotations(media_id);
                CREATE INDEX IF NOT EXISTS idx_training_set_items_set ON training_set_items(training_set_id);
                """
            )
            # Upgrade existing runtime DBs created before the annotation metadata column.
            cols = {row[1] for row in conn.execute("PRAGMA table_info(annotations)").fetchall()}
            if "metadata_json" not in cols:
                conn.execute("ALTER TABLE annotations ADD COLUMN metadata_json TEXT NOT NULL DEFAULT '{}'")
            layer_columns = {
                "layer_name": "TEXT NOT NULL DEFAULT ''",
                "z_index": "INTEGER NOT NULL DEFAULT 0",
                "visible": "INTEGER NOT NULL DEFAULT 1",
                "opacity": "REAL NOT NULL DEFAULT 0.55",
                "locked": "INTEGER NOT NULL DEFAULT 0",
                "blend_mode": "TEXT NOT NULL DEFAULT 'normal'",
                "color": "TEXT NOT NULL DEFAULT ''",
                "parent_ids_json": "TEXT NOT NULL DEFAULT '[]'",
                "revision": "INTEGER NOT NULL DEFAULT 1",
            }
            for column, definition in layer_columns.items():
                if column not in cols:
                    conn.execute(f"ALTER TABLE annotations ADD COLUMN {column} {definition}")
            # Existing rows predate explicit layer ordering.  Keep their relative
            # creation order while giving future rows a stable stack position.
            conn.execute(
                """
                UPDATE annotations
                SET z_index=id
                WHERE z_index=0
                """
            )

            # A development-only prerelease used a different revision schema.
            # Migrate it defensively so existing runtime folders remain usable.
            revision_cols = {row[1] for row in conn.execute("PRAGMA table_info(annotation_revisions)").fetchall()}
            required_revision_cols = {"id", "annotation_id", "revision", "snapshot_json", "reason", "created_at"}
            if revision_cols and not required_revision_cols.issubset(revision_cols):
                conn.execute("ALTER TABLE annotation_revisions RENAME TO annotation_revisions_legacy")
                conn.execute(
                    """
                    CREATE TABLE annotation_revisions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        annotation_id INTEGER NOT NULL REFERENCES annotations(id) ON DELETE CASCADE,
                        revision INTEGER NOT NULL,
                        snapshot_json TEXT NOT NULL,
                        reason TEXT NOT NULL DEFAULT 'edit',
                        created_at TEXT NOT NULL
                    )
                    """
                )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_annotations_media_layer ON annotations(media_id, z_index, id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_annotation_revisions_annotation ON annotation_revisions(annotation_id, revision, id)")

    def status(self) -> dict[str, Any]:
        counts = {}
        for table in ['reference_targets', 'reference_images', 'reference_runs', 'reference_detections', 'reference_verifications', 'reference_query_trials', 'annotations', 'training_sets', 'training_jobs']:
            try:
                row = self.db.query_one(f'SELECT COUNT(*) AS n FROM {table}') or {'n': 0}
                counts[table] = int(row['n'])
            except Exception:
                counts[table] = 0
        return {
            'pipelines': self.pipeline_catalog(),
            'counts': counts,
            'outputs_dir': str(self.exports_dir),
            'training_dir': str(self.training_dir),
        }

    def pipeline_catalog(self) -> list[dict[str, Any]]:
        return [
            {'key': 'demo_colorhash', 'label': 'Demo ColorHash verifier', 'available': True, 'requires': [], 'description': 'CPU-only whole-image/reference similarity sanity backend.'},
            {'key': 'siglip2_embedding_only', 'label': 'SigLIP2 embedding verifier', 'available': self._optional_available('torch', 'transformers'), 'requires': ['torch', 'transformers', 'SigLIP2 weights'], 'description': 'Whole-image embedding/prototype similarity path.'},
            {'key': 'owlv2_siglip2', 'label': 'OWLv2 proposals + SigLIP2 verification', 'available': self._optional_available('torch', 'transformers'), 'requires': ['torch', 'transformers', 'OWLv2', 'SigLIP2'], 'description': 'Image-guided box proposal + identity verification contract.'},
        ]

    @staticmethod
    def _optional_available(*modules: str) -> bool:
        import importlib.util
        return all(importlib.util.find_spec(m) is not None for m in modules)

    def list_targets(self) -> list[dict[str, Any]]:
        return self.db.query('SELECT * FROM reference_targets WHERE active=1 ORDER BY name COLLATE NOCASE')

    def upsert_target(self, name: str, notes: str = '') -> int:
        name = (name or '').strip()
        if not name:
            raise ValueError('Target/character name is required.')
        now = now_iso()
        with self.db._lock, self.db.connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO reference_targets(name, notes, created_at, updated_at, active)
                VALUES (?, ?, ?, ?, 1)
                ON CONFLICT(name) DO UPDATE SET notes=CASE WHEN excluded.notes<>'' THEN excluded.notes ELSE notes END, updated_at=excluded.updated_at, active=1
                """,
                (name, notes or '', now, now),
            )
            row = conn.execute('SELECT id FROM reference_targets WHERE name=?', (name,)).fetchone()
            return int(row['id']) if row else int(cur.lastrowid)

    def get_target_id(self, target_name_or_id: str | int) -> int:
        if isinstance(target_name_or_id, int) or str(target_name_or_id).isdigit():
            return int(target_name_or_id)
        row = self.db.query_one('SELECT id FROM reference_targets WHERE name=?', (str(target_name_or_id).strip(),))
        if not row:
            return self.upsert_target(str(target_name_or_id))
        return int(row['id'])

    def add_reference(self, target_name: str, path: str, reference_set_name: str = 'default') -> dict[str, Any]:
        target_id = self.upsert_target(target_name)
        p = Path(path).expanduser()
        if not p.exists():
            raise FileNotFoundError(str(p))
        meta = _image_meta(p)
        media_row = self.db.query_one('SELECT id FROM media WHERE path=?', (str(p),))
        now = now_iso()
        ref_id = self.db.execute(
            """
            INSERT INTO reference_images(target_id, media_id, path, sha256, width, height, reference_set_name, created_at, active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
            """,
            (target_id, media_row['id'] if media_row else None, str(p), meta.get('sha256'), meta.get('width'), meta.get('height'), reference_set_name or 'default', now),
        )
        return {'id': ref_id, 'target_id': target_id, 'path': str(p), **meta}

    def list_references(self, target_name: str | None = None) -> list[dict[str, Any]]:
        if target_name:
            target_id = self.get_target_id(target_name)
            return self.db.query('SELECT * FROM reference_images WHERE target_id=? AND active=1 ORDER BY id DESC', (target_id,))
        return self.db.query('SELECT * FROM reference_images WHERE active=1 ORDER BY id DESC LIMIT 500')

    def run_search(self, payload: dict[str, Any], job_id: int | None, progress=None) -> dict[str, Any]:
        target_name = (payload.get('target_name') or payload.get('character_name') or '').strip()
        if not target_name:
            raise ValueError('target_name is required.')
        target_id = self.upsert_target(target_name, payload.get('notes') or '')
        pipeline = payload.get('pipeline') or 'demo_colorhash'
        threshold = float(payload.get('threshold') if payload.get('threshold') is not None else 0.55)
        reference_paths = [str(x) for x in (payload.get('reference_paths') or []) if str(x).strip()]
        if not reference_paths:
            refs = self.list_references(target_name)
            reference_paths = [r['path'] for r in refs]
        if not reference_paths:
            raise ValueError('At least one reference path or saved reference image is required.')
        for rp in reference_paths:
            if Path(rp).expanduser().exists():
                # Avoid duplicate row noise by only inserting when this path is not present for the target.
                exists = self.db.query_one('SELECT id FROM reference_images WHERE target_id=? AND path=? AND active=1', (target_id, str(Path(rp).expanduser())))
                if not exists:
                    self.add_reference(target_name, rp, payload.get('reference_set_name') or 'default')
        ref_fingerprint = _fingerprint(reference_paths)
        media_ids = [int(x) for x in (payload.get('media_ids') or []) if str(x).strip()]
        dataset_id = int(payload['dataset_id']) if payload.get('dataset_id') else None
        folder = (payload.get('folder') or '').strip()
        candidates = self._candidate_media(media_ids, dataset_id, folder, bool(payload.get('recursive', True)))
        if not candidates:
            return {'processed': 0, 'detections': 0, 'message': 'No candidate media found.'}
        now = now_iso()
        with self.db._lock, self.db.connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO reference_runs(target_id, name, pipeline, threshold, dataset_id, folder, reference_fingerprint, status, params_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'running', ?, ?)
                """,
                (target_id, payload.get('run_name') or f'{target_name} {pipeline}', pipeline, threshold, dataset_id, folder, ref_fingerprint, json.dumps(payload), now),
            )
            run_id = int(cur.lastrowid)
        out_dir = self.exports_dir / f'run_{run_id:06d}'
        (out_dir / 'annotated').mkdir(parents=True, exist_ok=True)
        reference_embeddings = self._reference_embeddings(reference_paths, pipeline)
        detections = 0
        reused = 0
        processed = 0
        for idx, media in enumerate(candidates, start=1):
            if progress:
                progress((idx - 1) / max(len(candidates), 1), f'Reference search {idx}/{len(candidates)}')
            mem = None
            if payload.get('duplicate_policy', 'reuse_verified_or_cached') != 'force_reprocess':
                mem = self.db.query_one(
                    'SELECT * FROM reference_memory WHERE media_id=? AND target_id=? AND pipeline=? AND reference_fingerprint=?',
                    (media['id'], target_id, pipeline, ref_fingerprint),
                )
            if mem and (mem.get('verified_label') in {'correct', 'incorrect'} or payload.get('duplicate_policy') == 'reuse_exact_only'):
                reused += 1
                continue
            path = Path(media['path'])
            if not path.exists() or path.suffix.lower() not in IMAGE_EXTENSIONS:
                continue
            score = self._score_candidate(path, reference_embeddings, pipeline)
            decision = 'match' if score >= threshold else 'reject'
            bbox = _bbox_full(media)
            annotated = ''
            if decision == 'match' or payload.get('save_all_annotations'):
                annotated_path = out_dir / 'annotated' / f"{Path(media['path']).stem}_{media['id']}.jpg"
                _draw_annotation(path, bbox, score, annotated_path)
                annotated = str(annotated_path)
            det_id = self.db.execute(
                """
                INSERT INTO reference_detections(run_id, media_id, target_id, bbox_json, score_det, score_embed, score_final, decision, source, model_meta_json, annotated_path, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (run_id, media['id'], target_id, json.dumps(bbox), score, score, score, decision, pipeline, json.dumps({'pipeline': pipeline, 'whole_image': True}), annotated, now_iso()),
            )
            self._update_memory(media['id'], target_id, pipeline, ref_fingerprint, det_id, score, decision)
            detections += 1 if decision == 'match' else 0
            processed += 1
        self.db.execute('UPDATE reference_runs SET status=?, finished_at=?, message=? WHERE id=?', ('complete', now_iso(), f'processed={processed}, matches={detections}, reused={reused}', run_id))
        if progress:
            progress(1.0, 'Reference search complete')
        return {'run_id': run_id, 'processed': processed, 'matches': detections, 'reused': reused, 'output_dir': str(out_dir)}

    def _candidate_media(self, media_ids: list[int], dataset_id: int | None, folder: str, recursive: bool) -> list[dict[str, Any]]:
        if media_ids:
            placeholders = ','.join('?' for _ in media_ids)
            return self.db.query(f'SELECT * FROM media WHERE id IN ({placeholders}) AND active=1 ORDER BY id ASC', media_ids)
        if dataset_id:
            return self.db.query("SELECT * FROM media WHERE dataset_id=? AND active=1 AND media_type='image' ORDER BY id ASC", (dataset_id,))
        if folder:
            root = Path(folder).expanduser()
            if not root.exists():
                raise FileNotFoundError(str(root))
            ds_id = self.db.insert_dataset(f'Reference search: {root.name}', str(root), {'source': 'reference_search_folder'})
            paths = [p for p in root.rglob('*') if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS] if recursive else [p for p in root.glob('*') if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS]
            payloads = []
            for p in paths:
                meta = _image_meta(p)
                payloads.append({'dataset_id': ds_id, 'path': str(p), 'relative_path': str(p.relative_to(root)), 'media_type': 'image', 'ext': p.suffix.lower(), 'width': meta.get('width'), 'height': meta.get('height'), 'size_bytes': meta.get('size_bytes'), 'sha256': meta.get('sha256')})
            ids = self.db.bulk_upsert_media(payloads)
            if not ids:
                return []
            placeholders = ','.join('?' for _ in ids)
            return self.db.query(f'SELECT * FROM media WHERE id IN ({placeholders}) ORDER BY id ASC', ids)
        return []

    def _reference_embeddings(self, reference_paths: Sequence[str], pipeline: str) -> list[list[float]]:
        # The always-available backend is intentionally deterministic and dependency-light.
        # Optional model-backed pipelines can be added behind the same score call later.
        embeddings = []
        for rp in reference_paths:
            p = Path(rp).expanduser()
            if p.exists():
                embeddings.append(_histogram_embedding(p))
        if not embeddings:
            raise ValueError('No valid reference images were readable.')
        return embeddings

    def _score_candidate(self, image_path: Path, reference_embeddings: Sequence[Sequence[float]], pipeline: str) -> float:
        emb = _histogram_embedding(image_path)
        return max(_cosine(emb, ref) for ref in reference_embeddings)

    def _update_memory(self, media_id: int, target_id: int, pipeline: str, fingerprint: str, det_id: int, score: float, decision: str, verified_label: str = '') -> None:
        self.db.execute(
            """
            INSERT INTO reference_memory(media_id, target_id, pipeline, reference_fingerprint, best_detection_id, has_target, verified_label, best_score, last_decision, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(media_id, target_id, pipeline, reference_fingerprint)
            DO UPDATE SET best_detection_id=excluded.best_detection_id, has_target=excluded.has_target, best_score=excluded.best_score, last_decision=excluded.last_decision, updated_at=excluded.updated_at
            """,
            (media_id, target_id, pipeline, fingerprint, det_id, 1 if decision == 'match' else 0, verified_label, score, decision, now_iso()),
        )

    def list_runs(self, target_name: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        if target_name:
            target_id = self.get_target_id(target_name)
            return self.db.query('SELECT * FROM reference_runs WHERE target_id=? ORDER BY id DESC LIMIT ?', (target_id, int(limit)))
        return self.db.query('SELECT r.*, t.name AS target_name FROM reference_runs r LEFT JOIN reference_targets t ON t.id=r.target_id ORDER BY r.id DESC LIMIT ?', (int(limit),))

    def list_results(self, run_id: int | None = None, target_name: str | None = None, decision: str | None = None, limit: int = 200) -> list[dict[str, Any]]:
        where = []
        params: list[Any] = []
        if run_id:
            where.append('d.run_id=?'); params.append(int(run_id))
        if target_name:
            where.append('t.id=?'); params.append(self.get_target_id(target_name))
        if decision:
            where.append('d.decision=?'); params.append(decision)
        sql = """
            SELECT d.*, m.path, m.relative_path, m.width, m.height, t.name AS target_name,
                   COALESCE((SELECT user_label FROM reference_verifications v WHERE v.detection_id=d.id ORDER BY v.id DESC LIMIT 1), '') AS user_label
            FROM reference_detections d
            JOIN media m ON m.id=d.media_id
            LEFT JOIN reference_targets t ON t.id=d.target_id
        """
        if where:
            sql += ' WHERE ' + ' AND '.join(where)
        sql += ' ORDER BY d.score_final DESC, d.id DESC LIMIT ?'
        params.append(int(limit))
        rows = self.db.query(sql, params)
        for row in rows:
            row['bbox'] = _loads(row.get('bbox_json'), {})
            row['model_meta'] = _loads(row.get('model_meta_json'), {})
        return rows

    def verify(self, detection_id: int, label: str, notes: str = '') -> dict[str, Any]:
        label = (label or '').strip().lower()
        if label not in {'correct', 'incorrect', 'uncertain'}:
            raise ValueError('label must be correct, incorrect, or uncertain')
        det = self.db.query_one('SELECT * FROM reference_detections WHERE id=?', (int(detection_id),))
        if not det:
            raise ValueError(f'Unknown detection_id={detection_id}')
        vid = self.db.execute(
            'INSERT INTO reference_verifications(detection_id, media_id, target_id, user_label, notes, created_at) VALUES (?, ?, ?, ?, ?, ?)',
            (int(detection_id), int(det['media_id']), int(det['target_id']) if det.get('target_id') else None, label, notes or '', now_iso()),
        )
        has_target = 1 if label == 'correct' else 0
        self.db.execute(
            """
            UPDATE reference_memory SET verified_label=?, has_target=?, best_detection_id=?, best_score=?, last_decision=?, updated_at=?
            WHERE media_id=? AND target_id=? AND pipeline=(SELECT pipeline FROM reference_runs WHERE id=?)
            """,
            (label, has_target, int(detection_id), det.get('score_final'), det.get('decision'), now_iso(), int(det['media_id']), int(det['target_id']), int(det['run_id'])),
        )
        return {'verification_id': vid, 'detection_id': detection_id, 'label': label, 'updated': True}

    def known_sets(self, target_id: int) -> tuple[set[int], set[int]]:
        rows = self.db.query('SELECT media_id, user_label FROM reference_verifications WHERE target_id=? ORDER BY id ASC', (target_id,))
        pos: set[int] = set(); neg: set[int] = set()
        for row in rows:
            if row['user_label'] == 'correct':
                pos.add(int(row['media_id'])); neg.discard(int(row['media_id']))
            elif row['user_label'] == 'incorrect':
                neg.add(int(row['media_id'])); pos.discard(int(row['media_id']))
        return pos, neg

    def evaluate_query(self, target_name: str, query: str, baseline_query: str = '', dataset_id: int | None = None, scope: str = 'all_images', store: bool = True) -> dict[str, Any]:
        target_id = self.get_target_id(target_name)
        universe = self._query_universe(target_id, dataset_id, scope)
        result_ids = _evaluate_ast(_parse_query(query), self._tag_lookup(dataset_id), universe)
        known_pos, known_neg = self.known_sets(target_id)
        if dataset_id:
            known_pos &= universe; known_neg &= universe
        pos_returned = result_ids & known_pos
        neg_returned = result_ids & known_neg
        pos_dropped = known_pos - result_ids
        neg_avoided = known_neg - result_ids
        precision = _safe_div(len(pos_returned), len(pos_returned) + len(neg_returned))
        recall = _safe_div(len(pos_returned), len(known_pos))
        baseline_ids: set[int] = set()
        if baseline_query.strip():
            try:
                baseline_ids = _evaluate_ast(_parse_query(baseline_query), self._tag_lookup(dataset_id), universe)
            except Exception:
                baseline_ids = set()
        new_vs_baseline = result_ids - baseline_ids if baseline_ids else result_ids
        metrics = {
            'result_count': len(result_ids),
            'known_positive_total': len(known_pos),
            'known_negative_total': len(known_neg),
            'known_positive_returned': len(pos_returned),
            'known_negative_returned': len(neg_returned),
            'known_positive_dropped': len(pos_dropped),
            'known_negative_avoided': len(neg_avoided),
            'precision_known': precision,
            'recall_known': recall,
            'f1_known': _f1(precision, recall),
            'new_candidates': len(result_ids - known_pos - known_neg),
            'new_vs_baseline': len(new_vs_baseline),
            'new_valid_vs_baseline': len(new_vs_baseline & known_pos),
            'valid_dropped_vs_baseline': len((baseline_ids & known_pos) - result_ids) if baseline_ids else len(pos_dropped),
        }
        metrics['verdict'], metrics['notes'] = self._verdict(metrics)
        if store:
            self.db.execute(
                'INSERT INTO reference_query_trials(target_id, query, baseline_query, metrics_json, result_ids_json, created_at) VALUES (?, ?, ?, ?, ?, ?)',
                (target_id, query, baseline_query or '', json.dumps(metrics), json.dumps(sorted(result_ids)), now_iso()),
            )
        return {'target_id': target_id, 'query': query, 'result_ids': sorted(result_ids), 'metrics': metrics}

    def evaluate_many_queries(self, target_name: str, queries: Sequence[str], baseline_query: str = '', dataset_id: int | None = None, scope: str = 'all_images') -> dict[str, Any]:
        rows = []
        for query in queries:
            if not str(query).strip():
                continue
            try:
                rows.append(self.evaluate_query(target_name, str(query), baseline_query=baseline_query, dataset_id=dataset_id, scope=scope, store=True))
            except Exception as exc:
                rows.append({'query': query, 'error': str(exc)})
        ranked = sorted(rows, key=lambda r: r.get('metrics', {}).get('f1_known', -1), reverse=True)
        return {'results': ranked, 'count': len(ranked)}

    def suggest_queries(self, target_name: str, dataset_id: int | None = None, limit: int = 30) -> dict[str, Any]:
        target_id = self.get_target_id(target_name)
        pos, neg = self.known_sets(target_id)
        universe = self._query_universe(target_id, dataset_id, 'all_images')
        if dataset_id:
            pos &= universe; neg &= universe
        if not pos:
            return {'suggestions': [], 'message': 'Verify at least one correct detection before query suggestion.'}
        placeholders = ','.join('?' for _ in pos)
        tag_rows = self.db.query(f'SELECT tag, COUNT(*) AS n FROM tags WHERE media_id IN ({placeholders}) GROUP BY tag ORDER BY n DESC LIMIT 200', list(pos))
        suggestions: list[str] = []
        for row in tag_rows:
            tag = row['tag']
            if not tag:
                continue
            suggestions.append(f'[tag:{tag}]')
            if len(suggestions) >= limit:
                break
        return {'suggestions': suggestions, 'count': len(suggestions)}

    def _query_universe(self, target_id: int, dataset_id: int | None, scope: str) -> set[int]:
        if scope == 'character_seen_images':
            rows = self.db.query('SELECT DISTINCT media_id FROM reference_detections WHERE target_id=?', (target_id,))
        elif dataset_id:
            rows = self.db.query('SELECT id AS media_id FROM media WHERE dataset_id=? AND active=1', (dataset_id,))
        else:
            rows = self.db.query('SELECT id AS media_id FROM media WHERE active=1')
        return {int(r['media_id']) for r in rows}

    def _tag_lookup(self, dataset_id: int | None = None) -> Callable[[str], set[int]]:
        def lookup(tag: str) -> set[int]:
            norm = _normalize_query_tag(tag)
            if dataset_id:
                rows = self.db.query('SELECT t.media_id FROM tags t JOIN media m ON m.id=t.media_id WHERE m.dataset_id=? AND lower(t.tag)=?', (dataset_id, norm))
            else:
                rows = self.db.query('SELECT media_id FROM tags WHERE lower(tag)=?', (norm,))
            return {int(r['media_id']) for r in rows}
        return lookup

    def _verdict(self, m: dict[str, Any]) -> tuple[str, str]:
        if m['known_positive_total'] == 0 and m['known_negative_total'] == 0:
            return 'needs_feedback', 'No verified positives/negatives yet.'
        if m['precision_known'] >= 0.9 and m['recall_known'] >= 0.75:
            return 'strong', 'High precision and recall on verified memory.'
        if m['precision_known'] >= 0.9 and m['recall_known'] < 0.75:
            return 'precise_but_narrow', 'Good precision but misses known positives.'
        if m['recall_known'] >= 0.85 and m['known_negative_returned'] > 0:
            return 'high_recall_noisy', 'Finds positives but includes known negatives.'
        if m['valid_dropped_vs_baseline'] > 0 and m['new_valid_vs_baseline'] > 0:
            return 'combine_with_or', 'Useful but should be OR-combined with baseline.'
        if m['known_positive_dropped'] > 0 and m['known_positive_returned'] == 0:
            return 'harmful', 'Drops known positives.'
        return 'needs_review', 'Review unknown candidates and add feedback.'

    def _next_z_index(self, media_id: int) -> int:
        row = self.db.query_one('SELECT COALESCE(MAX(z_index), 0) AS n FROM annotations WHERE media_id=?', (int(media_id),)) or {'n': 0}
        return int(row.get('n') or 0) + 1

    @staticmethod
    def _decode_annotation_row(row: dict[str, Any] | None) -> dict[str, Any] | None:
        if not row:
            return None
        decoded = dict(row)
        decoded['bbox'] = _loads(decoded.get('bbox_json'), {})
        decoded['polygon'] = _loads(decoded.get('polygon_json'), [])
        decoded['metadata'] = _loads(decoded.get('metadata_json'), {})
        decoded['parent_ids'] = _loads(decoded.get('parent_ids_json'), [])
        decoded['visible'] = bool(decoded.get('visible', 1))
        decoded['locked'] = bool(decoded.get('locked', 0))
        decoded['opacity'] = float(decoded.get('opacity', 0.55) if decoded.get('opacity') is not None else 0.55)
        decoded['layer_order'] = int(decoded.get('z_index') or 0)
        return decoded

    def get_annotation(self, annotation_id: int) -> dict[str, Any] | None:
        row = self.db.query_one(
            'SELECT a.*, m.path, t.name AS target_name FROM annotations a JOIN media m ON m.id=a.media_id LEFT JOIN reference_targets t ON t.id=a.target_id WHERE a.id=?',
            (int(annotation_id),),
        )
        return self._decode_annotation_row(row)

    def _next_layer_z(self, media_id: int) -> int:
        row = self.db.query_one('SELECT COALESCE(MAX(z_index), 0) AS z FROM annotations WHERE media_id=?', (int(media_id),)) or {'z': 0}
        return int(row.get('z') or 0) + 1

    def add_annotation(self, media_id: int, label: str, annotation_type: str = 'bbox', bbox: dict[str, Any] | None = None, polygon: list[list[float]] | None = None,
                       mask_path: str = '', target_name: str = '', set_name: str = 'default', source: str = 'user', model_key: str = '', confidence: float | None = None, metadata: dict[str, Any] | None = None,
                       layer_name: str = '', layer_order: int | None = None, z_index: int | None = None, visible: bool = True, opacity: float = 0.55, locked: bool = False, blend_mode: str = 'normal', color: str = '', parent_ids: Sequence[int] | None = None) -> dict[str, Any]:
        media = self.media.get(int(media_id))
        if not media:
            raise ValueError(f'Unknown media_id={media_id}')
        target_id = self.get_target_id(target_name) if target_name else None
        bbox = bbox or {}
        polygon = polygon or []
        final_mask = mask_path or ''
        if not final_mask and annotation_type in {'polygon', 'mask'} and polygon:
            final_mask = self.rasterize_polygon_mask(media.path, polygon)
        if not final_mask and annotation_type in {'bbox_mask', 'mask'} and bbox:
            final_mask = self.rasterize_bbox_mask(media.path, bbox)
        now = now_iso()
        requested_order = layer_order if layer_order is not None else z_index
        layer_z = int(requested_order) if requested_order is not None else self._next_layer_z(int(media_id))
        layer_name = (layer_name or f"{label or target_name or annotation_type} #{layer_z}").strip()
        blend_mode = str(blend_mode or 'normal').lower()
        if blend_mode not in {'normal', 'multiply', 'screen', 'overlay', 'add', 'subtract', 'difference'}:
            blend_mode = 'normal'
        opacity = max(0.0, min(1.0, float(opacity)))
        ann_id = self.db.execute(
            """
            INSERT INTO annotations(media_id, target_id, label, annotation_type, set_name, bbox_json, polygon_json, mask_path, source, model_key, confidence, metadata_json, layer_name, z_index, visible, opacity, locked, blend_mode, color, parent_ids_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (int(media_id), target_id, label or target_name or 'object', annotation_type, set_name or 'default', json.dumps(bbox), json.dumps(polygon), final_mask, source, model_key, confidence, json.dumps(metadata or {}), layer_name, layer_z, 1 if visible else 0, opacity, 1 if locked else 0, blend_mode, color or '', json.dumps([int(x) for x in (parent_ids or [])]), now, now),
        )
        row = self.get_annotation(int(ann_id)) or {}
        return row | {'annotation_id': int(ann_id), 'layer_order': layer_z}

    def delete_annotation(self, annotation_id: int) -> dict[str, Any]:
        row = self.db.query_one('SELECT id, mask_path FROM annotations WHERE id=?', (int(annotation_id),))
        if not row:
            return {'deleted': 0, 'annotation_id': int(annotation_id)}
        revision_rows = self.db.query('SELECT snapshot_json FROM annotation_revisions WHERE annotation_id=?', (int(annotation_id),))
        revision_masks = [str(_loads(item.get('snapshot_json'), {}).get('mask_path') or '') for item in revision_rows]
        self.db.execute('DELETE FROM annotations WHERE id=?', (int(annotation_id),))
        self.db.execute('DELETE FROM annotation_revisions WHERE annotation_id=?', (int(annotation_id),))
        mask_path = row.get('mask_path') or ''
        deleted_mask = self._delete_unreferenced_annotation_mask(mask_path)
        deleted_revision_masks = sum(1 for value in revision_masks if self._delete_unreferenced_annotation_mask(value))
        return {'deleted': 1, 'annotation_id': int(annotation_id), 'mask_path': mask_path, 'deleted_mask_file': deleted_mask, 'deleted_revision_mask_files': deleted_revision_masks}

    def _delete_unreferenced_annotation_mask(self, mask_path: str) -> bool:
        if not mask_path:
            return False
        candidate = Path(str(mask_path)).expanduser()
        try:
            resolved = candidate.resolve()
            resolved.relative_to(self.annotations_dir.resolve())
        except Exception:
            return False
        if self.db.query_one('SELECT id FROM annotations WHERE mask_path IN (?, ?) LIMIT 1', (str(candidate), str(resolved))):
            return False
        try:
            resolved.unlink(missing_ok=True)
            return True
        except Exception:
            return False

    def clear_preview_masks(self, mask_paths: Sequence[str]) -> dict[str, Any]:
        deleted: list[str] = []
        preserved: list[str] = []
        for value in mask_paths or []:
            candidate = Path(str(value)).expanduser()
            try:
                resolved = candidate.resolve()
                allowed_roots = [(self.annotations_dir / 'model_masks').resolve(), (self.annotations_dir / 'preview_masks').resolve()]
                if not any(_path_is_within(resolved, root) for root in allowed_roots):
                    raise ValueError('outside preview roots')
            except Exception:
                preserved.append(str(value))
                continue
            if self.db.query_one('SELECT id FROM annotations WHERE mask_path IN (?, ?) LIMIT 1', (str(candidate), str(resolved))):
                preserved.append(str(resolved))
                continue
            try:
                resolved.unlink(missing_ok=True)
                deleted.append(str(resolved))
            except Exception:
                preserved.append(str(resolved))
        return {'deleted': len(deleted), 'deleted_paths': deleted, 'preserved_paths': preserved}

    def clear_generated_annotations(self, media_id: int, task: str, model_key: str = '') -> dict[str, Any]:
        task = str(task or '').lower()
        types = ('bbox', 'obb', 'rotated_bbox') if task == 'detection' else ('mask', 'polygon', 'bbox_mask', 'segmentation')
        placeholders = ','.join('?' for _ in types)
        params: list[Any] = [int(media_id), *types]
        sql = (
            f"SELECT id, mask_path FROM annotations WHERE media_id=? AND annotation_type IN ({placeholders}) "
            "AND source IN ('model','vlm','api','orchestration')"
        )
        if model_key:
            sql += ' AND model_key=?'
            params.append(model_key)
        rows = self.db.query(sql, params)
        deleted_masks = 0
        for row in rows:
            result = self.delete_annotation(int(row['id']))
            deleted_masks += int(bool(result.get('deleted_mask_file')))
        return {
            'media_id': int(media_id),
            'task': task,
            'model_key': model_key or None,
            'deleted_annotations': len(rows),
            'deleted_mask_files': deleted_masks,
        }

    def list_annotations(self, media_id: int | None = None, label: str | None = None, limit: int = 500) -> list[dict[str, Any]]:
        where = []
        params: list[Any] = []
        if media_id:
            where.append('a.media_id=?'); params.append(int(media_id))
        if label:
            where.append('a.label=?'); params.append(label)
        sql = 'SELECT a.*, m.path, t.name AS target_name FROM annotations a JOIN media m ON m.id=a.media_id LEFT JOIN reference_targets t ON t.id=a.target_id'
        if where:
            sql += ' WHERE ' + ' AND '.join(where)
        sql += ' ORDER BY a.z_index ASC, a.id ASC LIMIT ?'; params.append(int(limit))
        rows = self.db.query(sql, params)
        return [self._decode_annotation_row(row) for row in rows]

    def _snapshot_annotation(self, annotation_id: int, reason: str = 'edit') -> dict[str, Any]:
        row = self.get_annotation(int(annotation_id))
        if not row:
            raise ValueError(f'Unknown annotation_id={annotation_id}')
        snapshot = {
            key: row.get(key) for key in (
                'media_id', 'target_id', 'label', 'annotation_type', 'set_name', 'bbox', 'polygon',
                'mask_path', 'source', 'model_key', 'confidence', 'metadata', 'layer_name', 'z_index',
                'visible', 'opacity', 'locked', 'blend_mode', 'color', 'parent_ids', 'revision'
            )
        }
        mask_path = str(snapshot.get('mask_path') or '')
        if mask_path and Path(mask_path).exists():
            revisions_dir = self.annotations_dir / 'revision_masks'
            revisions_dir.mkdir(parents=True, exist_ok=True)
            copied = revisions_dir / f'ann_{annotation_id}_rev_{int(row.get("revision") or 1)}_{uuid.uuid4().hex[:8]}.png'
            try:
                shutil.copy2(mask_path, copied)
                snapshot['mask_path'] = str(copied.resolve())
            except Exception:
                pass
        revision = int(row.get('revision') or 1)
        self.db.execute(
            'INSERT INTO annotation_revisions(annotation_id, revision, snapshot_json, reason, created_at) VALUES (?, ?, ?, ?, ?)',
            (int(annotation_id), revision, json.dumps(snapshot), str(reason or 'edit'), now_iso()),
        )
        return snapshot

    def list_annotation_revisions(self, annotation_id: int, limit: int = 50) -> list[dict[str, Any]]:
        rows = self.db.query(
            'SELECT * FROM annotation_revisions WHERE annotation_id=? ORDER BY id DESC LIMIT ?',
            (int(annotation_id), max(1, min(int(limit or 50), 500))),
        )
        for row in rows:
            row['snapshot'] = _loads(row.get('snapshot_json'), {})
        return rows

    def update_annotation_layer(self, annotation_id: int, patch: dict[str, Any], reason: str = 'edit', force: bool = False) -> dict[str, Any]:
        row = self.get_annotation(int(annotation_id))
        if not row:
            raise ValueError(f'Unknown annotation_id={annotation_id}')
        patch = dict(patch or {})
        if 'layer_order' in patch and 'z_index' not in patch:
            patch['z_index'] = patch.pop('layer_order')
        geometry_keys = {'bbox', 'polygon', 'mask_path', 'annotation_type'}
        has_geometry_edit = any(key in patch for key in geometry_keys)
        if row.get('locked') and has_geometry_edit and not force and patch.get('locked') is not False:
            raise ValueError('This layer is locked. Unlock it before editing geometry or pixels.')
        # Once a user changes model/API geometry, preserve the originating model
        # in metadata but promote the layer to a user-edited source.  This keeps
        # manual refinements persistent when the user later clears raw model
        # outputs from the same image.
        if has_geometry_edit and str(row.get('source') or '').lower() in {'model', 'vlm', 'api', 'orchestration'} and 'source' not in patch:
            patch['source'] = 'user-edited'
            provenance = dict(patch.get('metadata') or {})
            provenance.setdefault('original_source', row.get('source') or '')
            provenance.setdefault('original_model_key', row.get('model_key') or '')
            provenance['manual_edit'] = True
            patch['metadata'] = provenance
        self._snapshot_annotation(int(annotation_id), reason)
        fields: list[str] = []
        values: list[Any] = []
        scalar_map = {
            'label': 'label', 'annotation_type': 'annotation_type', 'set_name': 'set_name',
            'mask_path': 'mask_path', 'source': 'source', 'model_key': 'model_key',
            'confidence': 'confidence', 'layer_name': 'layer_name', 'z_index': 'z_index',
            'blend_mode': 'blend_mode', 'color': 'color',
        }
        for key, column in scalar_map.items():
            if key in patch:
                value = patch[key]
                if key == 'blend_mode':
                    value = str(value or 'normal').lower()
                    if value not in {'normal', 'multiply', 'screen', 'overlay', 'add', 'subtract', 'difference'}:
                        raise ValueError(f'Unsupported layer blend mode: {value}')
                if key == 'z_index':
                    value = max(1, int(value))
                fields.append(f'{column}=?'); values.append(value)
        if 'target_name' in patch:
            target_name = str(patch.get('target_name') or '').strip()
            fields.append('target_id=?'); values.append(self.get_target_id(target_name) if target_name else None)
        if 'visible' in patch:
            fields.append('visible=?'); values.append(1 if patch['visible'] else 0)
        if 'locked' in patch:
            fields.append('locked=?'); values.append(1 if patch['locked'] else 0)
        if 'opacity' in patch:
            fields.append('opacity=?'); values.append(max(0.0, min(1.0, float(patch['opacity']))))
        if 'bbox' in patch:
            fields.append('bbox_json=?'); values.append(json.dumps(patch.get('bbox') or {}))
        if 'polygon' in patch:
            fields.append('polygon_json=?'); values.append(json.dumps(patch.get('polygon') or []))
        if 'metadata' in patch:
            # Layer edits augment provenance instead of erasing the originating
            # model/API metadata that the user may need later.
            merged_metadata = dict(row.get('metadata') or {})
            merged_metadata.update(patch.get('metadata') or {})
            fields.append('metadata_json=?'); values.append(json.dumps(merged_metadata))
        if 'parent_ids' in patch:
            fields.append('parent_ids_json=?'); values.append(json.dumps([int(x) for x in (patch.get('parent_ids') or [])]))
        if not fields:
            return row
        old_mask = str(row.get('mask_path') or '')
        fields.extend(['revision=revision+1', 'updated_at=?']); values.append(now_iso())
        values.append(int(annotation_id))
        self.db.execute(f'UPDATE annotations SET {", ".join(fields)} WHERE id=?', values)
        updated = self.get_annotation(int(annotation_id)) or {}
        new_mask = str(updated.get('mask_path') or '')
        if old_mask and new_mask != old_mask:
            self._delete_unreferenced_annotation_mask(old_mask)
        return updated

    def update_annotation(self, annotation_id: int, changes: dict[str, Any], *, force: bool = False, reason: str = 'edit') -> dict[str, Any]:
        """Public layer-update facade used by the spatial API.

        ``mask_data_url`` is intentionally accepted here so pixel edits and
        geometry/property edits share one annotation/layer contract.
        """
        patch = dict(changes or {})
        mask_data_url = patch.pop('mask_data_url', None)
        if mask_data_url:
            row = self.get_annotation(int(annotation_id))
            if not row:
                raise ValueError(f'Unknown annotation_id={annotation_id}')
            return self.save_raster_mask_layer(
                int(row['media_id']), str(mask_data_url), annotation_id=int(annotation_id),
                label=str(patch.pop('label', None) or row.get('label') or 'mask'),
                target_name=str(patch.pop('target_name', None) or row.get('target_name') or ''),
                layer_name=str(patch.pop('layer_name', None) or row.get('layer_name') or ''),
                source=str(patch.pop('source', None) or row.get('source') or 'user'),
                model_key=str(patch.pop('model_key', None) or row.get('model_key') or ''),
                opacity=float(patch.pop('opacity', row.get('opacity', 0.55))),
                color=str(patch.pop('color', None) or row.get('color') or '#22c55e'),
                metadata=dict(patch.pop('metadata', {}) or {}), force=force,
            )
        return self.update_annotation_layer(int(annotation_id), patch, reason=reason, force=force)

    def duplicate_annotation(self, annotation_id: int, layer_name: str = '') -> dict[str, Any]:
        return self.duplicate_annotation_layer(int(annotation_id), layer_name=layer_name)

    def save_mask_layer(
        self,
        media_id: int,
        mask_data_url: str,
        *,
        annotation_id: int | None = None,
        label: str = 'mask',
        target_name: str = '',
        source: str = 'user',
        model_key: str = '',
        metadata: dict[str, Any] | None = None,
        layer_name: str = '',
        opacity: float = 0.55,
        color: str = '#22c55e',
        force: bool = False,
    ) -> dict[str, Any]:
        return self.save_raster_mask_layer(
            int(media_id), str(mask_data_url), annotation_id=annotation_id, label=label,
            target_name=target_name, source=source, model_key=model_key,
            metadata=metadata, layer_name=layer_name, opacity=opacity, color=color,
            force=force,
        )

    def restore_annotation_revision(self, annotation_id: int, revision_id: int) -> dict[str, Any]:
        revision = self.db.query_one(
            'SELECT * FROM annotation_revisions WHERE id=? AND annotation_id=?',
            (int(revision_id), int(annotation_id)),
        )
        if not revision:
            raise ValueError('The requested annotation revision was not found.')
        snapshot = _loads(revision.get('snapshot_json'), {})
        restored_mask = str(snapshot.get('mask_path') or '')
        if restored_mask and Path(restored_mask).exists():
            media = self.media.get(int(snapshot['media_id']))
            if not media:
                raise ValueError('The source media for this revision no longer exists.')
            with Image.open(media.path) as source_image:
                restored_array = annotation_to_mask({'mask_path': restored_mask}, source_image.size)
            restored_mask = str(Path(save_mask(restored_array, self.annotations_dir / 'layers', f'ann_{annotation_id}_restored')).resolve())
        patch = {
            'label': snapshot.get('label') or 'object',
            'annotation_type': snapshot.get('annotation_type') or 'bbox',
            'bbox': snapshot.get('bbox') or {},
            'polygon': snapshot.get('polygon') or [],
            'mask_path': restored_mask,
            'source': snapshot.get('source') or 'user',
            'model_key': snapshot.get('model_key') or '',
            'confidence': snapshot.get('confidence'),
            'metadata': (snapshot.get('metadata') or {}) | {'restored_from_revision_id': int(revision_id)},
            'layer_name': snapshot.get('layer_name') or '',
            'visible': snapshot.get('visible', True),
            'opacity': snapshot.get('opacity', 0.55),
            'locked': snapshot.get('locked', False),
            'blend_mode': snapshot.get('blend_mode') or 'normal',
            'color': snapshot.get('color') or '',
            'parent_ids': snapshot.get('parent_ids') or [],
        }
        return self.update_annotation(int(annotation_id), patch, force=True, reason=f'restore_revision_{revision_id}')

    def reorder_annotation_layers(self, media_id: int, annotation_ids: Sequence[int], task: str = '') -> dict[str, Any]:
        ids = [int(value) for value in annotation_ids]
        if not ids:
            return {'media_id': int(media_id), 'task': task or None, 'ordered_ids': []}
        if len(ids) != len(set(ids)):
            raise ValueError('Layer order cannot contain duplicate annotation IDs.')
        placeholders = ','.join('?' for _ in ids)
        found = self.db.query(
            f'SELECT id, annotation_type FROM annotations WHERE media_id=? AND id IN ({placeholders})',
            [int(media_id), *ids],
        )
        found_ids = {int(row['id']) for row in found}
        if found_ids != set(ids):
            raise ValueError('One or more layers do not belong to this media item.')
        task_value = str(task or '').lower()
        if task_value:
            allowed = {'bbox', 'obb', 'rotated_bbox'} if task_value == 'detection' else {'mask', 'polygon', 'bbox_mask', 'segmentation'}
            if any(str(row.get('annotation_type') or '').lower() not in allowed for row in found):
                raise ValueError(f'Layer order contains an annotation that is not compatible with {task_value}.')
        now = now_iso()
        with self.db._lock, self.db.connect() as conn:
            for z_index, annotation_id in enumerate(ids, start=1):
                conn.execute('UPDATE annotations SET z_index=?, updated_at=? WHERE id=?', (z_index, now, annotation_id))
        return {'media_id': int(media_id), 'task': task_value or None, 'ordered_ids': ids}

    def duplicate_annotation_layer(self, annotation_id: int, layer_name: str = '') -> dict[str, Any]:
        row = self.get_annotation(int(annotation_id))
        if not row:
            raise ValueError(f'Unknown annotation_id={annotation_id}')
        copied_mask = str(row.get('mask_path') or '')
        if copied_mask and Path(copied_mask).exists():
            with Image.open(copied_mask) as mask:
                copied_mask = save_mask(np.asarray(mask.convert('L'), dtype=np.uint8), self.annotations_dir / 'layers', f'ann_{annotation_id}_copy')
        return self.add_annotation(
            media_id=int(row['media_id']), label=row.get('label') or 'object', annotation_type=row.get('annotation_type') or 'bbox',
            bbox=row.get('bbox') or {}, polygon=row.get('polygon') or [], mask_path=copied_mask,
            set_name=row.get('set_name') or 'default', source='derived', model_key=row.get('model_key') or '',
            confidence=row.get('confidence'), metadata=(row.get('metadata') or {}) | {'duplicated_from': int(annotation_id)},
            layer_name=layer_name or f"{row.get('layer_name') or row.get('label') or 'layer'} copy",
            visible=row.get('visible', True), opacity=row.get('opacity', 0.55), locked=False,
            blend_mode=row.get('blend_mode') or 'normal', color=row.get('color') or '', parent_ids=[int(annotation_id)],
        )

    @staticmethod
    def _decode_mask_data(mask_data: str) -> Image.Image:
        value = str(mask_data or '')
        if ',' in value and value.lstrip().startswith('data:'):
            value = value.split(',', 1)[1]
        raw = base64.b64decode(value, validate=False)
        if len(raw) > 128 * 1024 * 1024:
            raise ValueError('Mask payload is too large.')
        image = Image.open(io.BytesIO(raw))
        if image.mode == 'RGBA':
            alpha = image.getchannel('A')
            if alpha.getextrema() != (255, 255):
                return alpha
        return image.convert('L')

    def save_raster_mask_layer(
        self,
        media_id: int,
        mask_data: str,
        *,
        annotation_id: int | None = None,
        label: str = 'mask',
        target_name: str = '',
        layer_name: str = '',
        source: str = 'user',
        model_key: str = '',
        opacity: float = 0.55,
        color: str = '#22c55e',
        metadata: dict[str, Any] | None = None,
        force: bool = False,
    ) -> dict[str, Any]:
        media = self.media.get(int(media_id))
        if not media:
            raise ValueError(f'Unknown media_id={media_id}')
        mask = self._decode_mask_data(mask_data)
        with Image.open(media.path) as image:
            expected = image.size
        if mask.size != expected:
            raise ValueError(f'Mask dimensions {mask.size} do not match image dimensions {expected}.')
        array = np.asarray(mask, dtype=np.uint8)
        if not bool((array > 0).any()):
            raise ValueError('The edited mask is empty. Draw or select pixels before saving.')
        output = save_mask(array, self.annotations_dir / 'layers', f'{Path(media.path).stem}_edited_mask')
        bbox = mask_bbox(array)
        meta = dict(metadata or {}) | {'spatial_task': 'segmentation', 'user_pixel_edit': True}
        if annotation_id is not None:
            row = self.get_annotation(int(annotation_id))
            if not row or int(row['media_id']) != int(media_id):
                raise ValueError('The selected mask layer does not belong to this image.')
            original_source = str(row.get('source') or 'user')
            effective_source = str(source or original_source)
            if original_source.lower() in {'model', 'vlm', 'api', 'orchestration'} and effective_source.lower() == original_source.lower():
                effective_source = 'user-edited'
                meta.setdefault('original_source', original_source)
                meta.setdefault('original_model_key', row.get('model_key') or '')
            meta['manual_edit'] = True
            updated = self.update_annotation(
                int(annotation_id),
                {'mask_path': output, 'bbox': bbox, 'polygon': [], 'annotation_type': 'mask',
                 'label': label or row.get('label') or 'mask', 'target_name': target_name or row.get('target_name') or '',
                 'layer_name': layer_name or row.get('layer_name') or '', 'opacity': opacity, 'color': color,
                 'source': effective_source, 'model_key': model_key or row.get('model_key') or '',
                 'metadata': meta},
                reason='pixel_edit', force=force,
            )
            return updated | {'updated': True, 'annotation': updated, 'id': int(annotation_id), 'annotation_id': int(annotation_id), 'mask_path': output, 'bbox': bbox}
        result = self.add_annotation(
            media_id=int(media_id), label=label or 'mask', annotation_type='mask', bbox=bbox, polygon=[], mask_path=output,
            target_name=target_name, source=source or 'user', model_key=model_key or '', confidence=None, metadata=meta,
            layer_name=layer_name or label or 'edited mask', opacity=opacity, color=color,
        )
        result_id = int(result.get('id') or result.get('annotation_id'))
        return result | {'updated': False, 'annotation': result, 'id': result_id, 'annotation_id': result_id, 'mask_path': output, 'bbox': bbox}

    def create_blank_mask_layer(self, media_id: int, label: str = 'blank_mask', layer_name: str = '') -> dict[str, Any]:
        media = self.media.get(int(media_id))
        if not media:
            raise ValueError(f'Unknown media_id={media_id}')
        with Image.open(media.path) as image:
            blank = np.zeros((image.height, image.width), dtype=np.uint8)
        path = save_mask(blank, self.annotations_dir / 'layers', f'{Path(media.path).stem}_blank')
        return self.add_annotation(
            media_id=int(media_id), label=label or 'blank_mask', annotation_type='mask', mask_path=path,
            source='user', metadata={'spatial_task': 'segmentation', 'blank_layer': True},
            layer_name=layer_name or label or 'blank mask', opacity=0.55, color='#22c55e',
        )

    def _selected_annotations(self, media_id: int, annotation_ids: Sequence[int], allowed_types: set[str]) -> list[dict[str, Any]]:
        ids = [int(value) for value in annotation_ids]
        if not ids:
            raise ValueError('Select at least one layer.')
        if len(ids) != len(set(ids)):
            raise ValueError('A layer can only appear once in a composition.')
        placeholders = ','.join('?' for _ in ids)
        rows = self.db.query(
            f'SELECT * FROM annotations WHERE media_id=? AND id IN ({placeholders})',
            [int(media_id), *ids],
        )
        by_id = {int(row['id']): self._decode_annotation_row(row) for row in rows}
        if set(by_id) != set(ids):
            raise ValueError('One or more selected layers were not found on this media item.')
        # Preserve caller order. This is significant for subtract/difference:
        # the first selected/base mask is reduced by all following masks.
        decoded = [by_id[value] for value in ids]
        invalid = [row for row in decoded if str(row.get('annotation_type') or '').lower() not in allowed_types]
        if invalid:
            raise ValueError('The selected layer set contains incompatible annotation types.')
        return decoded

    def merge_bbox_layers(
        self,
        media_id: int,
        annotation_ids: Sequence[int],
        operation: str = 'union',
        *,
        label: str = 'combined_box',
        layer_name: str = '',
        delete_sources: bool = False,
    ) -> dict[str, Any]:
        rows = self._selected_annotations(int(media_id), annotation_ids, {'bbox', 'obb', 'rotated_bbox'})
        if len(rows) < 2:
            raise ValueError('Select at least two bounding-box layers to combine.')
        media = self.media.get(int(media_id))
        merged = merge_bboxes(
            [row.get('bbox') or {} for row in rows], operation,
            [row.get('confidence') for row in rows], width=media.width or None, height=media.height or None,
        )
        confidences = [float(row['confidence']) for row in rows if row.get('confidence') is not None]
        confidence = max(confidences) if operation in {'union', 'envelope', 'enclosing'} and confidences else (sum(confidences) / len(confidences) if confidences else None)
        result = self.add_annotation(
            media_id=int(media_id), label=label or 'combined_box', annotation_type='bbox', bbox=merged,
            source='composite', model_key='layer-compositor', confidence=confidence,
            metadata={'spatial_task': 'detection', 'operation': operation, 'parent_ids': [int(row['id']) for row in rows]},
            layer_name=layer_name or f'{label or "combined box"} ({operation})', parent_ids=[int(row['id']) for row in rows],
            color='#a855f7', opacity=0.75,
        )
        if delete_sources:
            for row in rows:
                self.delete_annotation(int(row['id']))
        return {'operation': operation, 'sources': [int(row['id']) for row in rows], 'annotation': result}

    def merge_mask_layers(
        self,
        media_id: int,
        annotation_ids: Sequence[int],
        operation: str = 'union',
        *,
        label: str = 'combined_mask',
        layer_name: str = '',
        delete_sources: bool = False,
        threshold: int = 1,
        feather: int = 0,
        grow: int = 0,
    ) -> dict[str, Any]:
        rows = self._selected_annotations(int(media_id), annotation_ids, {'mask', 'polygon', 'bbox_mask', 'segmentation'})
        if len(rows) < 2:
            raise ValueError('Select at least two mask layers to combine.')
        media = self.media.get(int(media_id))
        if not media:
            raise ValueError(f'Unknown media_id={media_id}')
        with Image.open(media.path) as image:
            size = image.size
        arrays = [annotation_to_mask(row, size) for row in rows]
        merged = combine_masks(arrays, operation, threshold=threshold)
        merged = postprocess_mask(merged, feather=feather, grow=grow)
        if not bool((merged > 0).any()):
            raise ValueError(f'The {operation} operation produced an empty mask; no layer was saved.')
        output = save_mask(merged, self.annotations_dir / 'composite_masks', f'{Path(media.path).stem}_{operation}')
        bbox = mask_bbox(merged)
        result = self.add_annotation(
            media_id=int(media_id), label=label or 'combined_mask', annotation_type='mask', bbox=bbox,
            polygon=[], mask_path=output, source='composite', model_key='layer-compositor', confidence=None,
            metadata={'spatial_task': 'segmentation', 'operation': operation, 'threshold': int(threshold), 'feather': int(feather), 'grow': int(grow), 'parent_ids': [int(row['id']) for row in rows]},
            layer_name=layer_name or f'{label or "combined mask"} ({operation})', parent_ids=[int(row['id']) for row in rows],
            color='#a855f7', opacity=0.55,
        )
        if delete_sources:
            for row in rows:
                self.delete_annotation(int(row['id']))
        return {'operation': operation, 'sources': [int(row['id']) for row in rows], 'annotation': result}

    def magic_select(
        self,
        media_id: int,
        x: float,
        y: float,
        *,
        method: str = 'flood_fill',
        tolerance: int = 24,
        connectivity: int = 8,
        bbox: dict[str, Any] | None = None,
        iterations: int = 5,
        radius_ratio: float = 0.22,
        feather: int = 0,
        grow: int = 0,
        invert: bool = False,
    ) -> dict[str, Any]:
        media = self.media.get(int(media_id))
        if not media:
            raise ValueError(f'Unknown media_id={media_id}')
        mask = magic_select_mask(
            media.path, x, y, method=method, tolerance=tolerance, connectivity=connectivity,
            bbox=bbox, iterations=iterations, radius_ratio=radius_ratio, feather=feather,
        )
        mask = postprocess_mask(mask, grow=grow)
        if invert:
            mask = (255 - np.asarray(mask, dtype=np.uint8)).astype(np.uint8)
        if not bool((mask > 0).any()):
            raise ValueError('Magic Select did not find a non-empty region at the clicked point.')
        path = save_mask(mask, self.annotations_dir / 'preview_masks', f'{Path(media.path).stem}_{method}_preview')
        return {
            'media_id': int(media_id), 'method': method, 'mask_path': path, 'bbox': mask_bbox(mask),
            'pixel_count': int((mask > 0).sum()), 'width': int(mask.shape[1]), 'height': int(mask.shape[0]),
        }

    def persist_spatial_proposals(self, media_id: int, task: str, proposals: Sequence[dict[str, Any]], label: str = '') -> list[dict[str, Any]]:
        saved: list[dict[str, Any]] = []
        for index, proposal in enumerate(proposals or []):
            ann_type = str(proposal.get('annotation_type') or ('bbox' if task == 'detection' else 'mask')).lower()
            if task == 'detection' and ann_type not in {'bbox', 'obb', 'rotated_bbox'}:
                ann_type = 'bbox'
            if task == 'segmentation' and ann_type not in {'mask', 'polygon', 'bbox_mask', 'segmentation'}:
                ann_type = 'mask' if proposal.get('mask_path') else 'polygon'
            saved.append(self.add_annotation(
                media_id=int(media_id), label=label or proposal.get('label') or f'{task}_{index + 1}',
                annotation_type=ann_type, bbox=proposal.get('bbox') or {}, polygon=proposal.get('polygon') or [],
                mask_path=str(proposal.get('mask_path') or ''), source=proposal.get('source') or 'model',
                model_key=proposal.get('model_key') or '', confidence=proposal.get('confidence'),
                metadata=(proposal.get('metadata') or {}) | {'spatial_task': task, 'persisted_from_preview': True},
                layer_name=proposal.get('layer_name') or f"{proposal.get('label') or task} preview {index + 1}",
                color='#f97316', opacity=0.6,
            ))
        return saved

    def rasterize_bbox_mask(self, image_path: str, bbox: dict[str, Any]) -> str:
        media_path = Path(image_path)
        out_path = self.annotations_dir / f'{media_path.stem}_bbox_mask_{uuid.uuid4().hex[:12]}.png'
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with Image.open(media_path) as im:
            w, h = im.size
        x1, y1, x2, y2 = _bbox_to_xyxy(bbox)
        mask = Image.new('L', (w, h), 0)
        ImageDraw.Draw(mask).rectangle([x1, y1, x2, y2], fill=255)
        mask.save(out_path)
        return str(out_path)

    def rasterize_polygon_mask(self, image_path: str, polygon: Sequence[Sequence[float]]) -> str:
        media_path = Path(image_path)
        out_path = self.annotations_dir / f'{media_path.stem}_polygon_mask_{uuid.uuid4().hex[:12]}.png'
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with Image.open(media_path) as im:
            w, h = im.size
        mask = Image.new('L', (w, h), 0)
        ImageDraw.Draw(mask).polygon([(float(x), float(y)) for x, y in polygon], fill=255)
        mask.save(out_path)
        return str(out_path)


    def annotation_model_catalog(self) -> list[dict[str, Any]]:
        """Return first-class annotation-capable model records with runtime status."""
        if not self.models:
            return []
        wanted = {"detect", "bbox", "segment", "mask", "video_mask", "pose", "pose2d", "pose3d", "keypoints", "annotation", "open_vocabulary", "custom_pt_compatible"}
        rows = []
        for row in self.models.list_models():
            caps = set(row.get("capabilities") or [])
            if row.get("name") == "dataset-assistant" or "no-model-download" in caps or "tag_suggestions" in caps or "caption_suggestions" in caps:
                continue
            if caps & wanted or row.get("kind") in {"detection", "segmentation", "pose2d", "pose3d", "custom"}:
                rows.append(row | {"annotation_status": self.annotation_model_status(row.get("name"), {})})
        return rows

    def annotation_model_classes(
        self,
        model_key: str,
        options: dict[str, Any] | None = None,
        *,
        query: str = "",
        limit: int = 500,
    ) -> dict[str, Any]:
        """Return fixed classes or prompt semantics for an annotation model.

        Closed-set models expose their real class IDs/names. SAM-family models
        explicitly report that text does not condition geometry, preventing the
        old misleading behavior where every typed token produced identical masks.
        """
        options = dict(options or {})
        if not self.models:
            return {"model_key": model_key, "mode": "unknown", "classes": [], "class_count": 0, "message": "Model service is not attached."}
        try:
            rec = self.models.registry.get_record(model_key)
        except Exception as exc:
            return {"model_key": model_key, "mode": "unknown", "classes": [], "class_count": 0, "error": str(exc)}
        checkpoint = self._resolve_annotation_checkpoint(model_key, options)
        mtime = None
        if checkpoint:
            try:
                path = Path(str(checkpoint)).expanduser()
                if path.exists():
                    mtime = path.stat().st_mtime_ns
            except Exception:
                pass
        cache_key = json.dumps({
            "model_key": model_key,
            "checkpoint": str(checkpoint or ""),
            "mtime": mtime,
            "custom_model_type": options.get("custom_model_type") or "auto",
        }, sort_keys=True)
        info = self._annotation_class_cache.get(cache_key)
        if info is None:
            info = inspect_model_classes(
                checkpoint,
                model_key=model_key,
                provider=str(getattr(rec, "provider", "") or ""),
                capabilities=getattr(rec, "capabilities", []) or [],
                custom_model_type=str(options.get("custom_model_type") or "auto"),
                allow_runtime_load=True,
            )
            self._annotation_class_cache[cache_key] = info
        all_classes = list(info.get("classes") or [])
        filtered = all_classes
        if query.strip():
            needle = re.sub(r"\s+", " ", query.strip().lower().replace("_", " ").replace("-", " "))
            filtered = [row for row in all_classes if needle in str(row.get("name") or "").lower().replace("_", " ").replace("-", " ")]
        safe_limit = max(0, min(int(limit or 500), 10000))
        visible = filtered[:safe_limit] if safe_limit else []
        return {
            "model_key": model_key,
            **{key: value for key, value in info.items() if key != "classes"},
            "class_count": len(all_classes) if info.get("class_count") is not None else info.get("class_count"),
            "matched_count": len(filtered),
            "returned_count": len(visible),
            "classes": visible,
            "checkpoint": str(checkpoint or ""),
        }

    def annotation_model_status(self, model_key: str | None, options: dict[str, Any] | None = None) -> dict[str, Any]:
        options = dict(options or {})
        if not model_key:
            return {"model_key": model_key, "exists": False, "message": "No model selected."}
        if model_key in {"demo_center_bbox", "", "none", "__none__"}:
            return {
                "model_key": model_key,
                "exists": False,
                "available": False,
                "downloaded": False,
                "loaded": False,
                "backend": "none",
                "message": "No annotation model selected. Draw manually or choose/download/load a real detection/segmentation/pose model.",
            }
        local = options.get("local_model_path") or options.get("custom_local_path") or ""
        if local:
            p = Path(local).expanduser()
            return {"model_key": model_key, "exists": p.exists(), "available": p.exists(), "downloaded": p.exists(), "local_path": str(p), "backend": options.get("custom_model_type") or "custom", "message": "Custom local model path."}
        if not self.models:
            return {"model_key": model_key, "exists": False, "available": False, "message": "Model service is not attached."}
        try:
            rec = self.models.registry.get_record(model_key)
        except Exception as exc:
            return {"model_key": model_key, "exists": False, "available": False, "error": str(exc)}
        local_dir = rec.local_dir(self.paths.models) if hasattr(rec, "local_dir") else None
        files = []
        if local_dir and local_dir.exists():
            files = [str(p) for p in local_dir.rglob("*") if p.is_file()][:25]
        deps: dict[str, bool] = {}
        dep_imports = {
            "segment-anything": "segment_anything",
            "segment-anything-hq": "segment_anything_hq",
            "SAM-HQ": "segment_anything_hq",
            "opencv-python": "cv2",
            "pycocotools": "pycocotools",
            "sam2": "sam2",
            "mediapipe": "mediapipe",
            "mmpose": "mmpose",
            "mmengine": "mmengine",
            "mmcv": "mmcv",
            "mmdet": "mmdet",
        }
        for dep in getattr(rec, "requirements", []) or []:
            base = dep.split("=")[0].split(">")[0].split("<")[0].split("[")[0]
            name = dep_imports.get(base, base)
            try:
                __import__(name)
                deps[dep] = True
            except Exception:
                deps[dep] = False
        expected = getattr(rec, "filename", None)
        downloaded = False
        if local_dir and local_dir.exists():
            if expected:
                downloaded = (local_dir / str(expected)).exists()
            else:
                downloaded = any(p.is_file() and not p.name.endswith(".part") for p in local_dir.rglob("*"))
        runtime_only_provider = rec.provider in {"ultralytics", "local", "mmpose", "openai", "openrouter", "anthropic", "builtin"}
        available = downloaded or runtime_only_provider
        if deps and not all(deps.values()):
            available = False
        return {"model_key": model_key, "label": rec.label, "provider": rec.provider, "kind": rec.kind, "backend": rec.recommended_backend, "downloaded": downloaded, "available": available, "loaded": model_key in self._annotation_model_cache, "local_dir": str(local_dir) if local_dir else None, "files": files, "requirements": deps, "message": "ready" if available else "Download checkpoint and/or install optional annotation model dependencies."}

    def load_annotation_model(self, model_key: str, device: str = "auto", options: dict[str, Any] | None = None) -> dict[str, Any]:
        """Validate/cache lightweight model state for annotation workflows."""
        status = self.annotation_model_status(model_key, options)
        if not status.get("available"):
            raise RuntimeError(status.get("message") or status.get("error") or "Annotation model is not available.")
        # Heavy model objects are loaded lazily by propose_annotation to avoid keeping
        # multiple large checkpoints in VRAM.  This cache records that validation passed.
        self._annotation_model_cache[model_key] = {"validated": True, "device": device, "options": dict(options or {}), "status": status, "loaded_at": now_iso()}
        status["loaded"] = True
        return status

    def _resolve_annotation_checkpoint(self, model_key: str, options: dict[str, Any]) -> str | None:
        """Resolve only real local checkpoint files for spatial annotation models.

        Returning the model key itself for SAM-like records caused errors such as
        "SAM checkpoint was not found: dataset-assistant" when the frontend
        accidentally selected a generic assistant row. YOLO remains the only
        adapter that may intentionally fall back to its public .pt id because
        Ultralytics can lazy-resolve those names.
        """
        for key in ("local_model_path", "custom_local_path", "checkpoint_path"):
            value = (options or {}).get(key)
            if value:
                p = Path(str(value)).expanduser()
                return str(p)
        if not self.models:
            return None
        rec = self.models.registry.get_record(model_key)
        local_dir = rec.local_dir(self.paths.models)
        if local_dir and local_dir.exists():
            preferred = [getattr(rec, "filename", None)] if getattr(rec, "filename", None) else []
            for name in preferred:
                candidate = local_dir / str(name)
                if candidate.exists():
                    return str(candidate)
            for suffix in ("*.pt", "*.pth", "*.onnx", "*.safetensors", "*.task"):
                hits = [p for p in local_dir.rglob(suffix) if p.is_file() and not p.name.endswith(".part")]
                if hits:
                    return str(hits[0])
        if getattr(rec, "provider", "") == "ultralytics":
            return getattr(rec, "api_model_id", None) or getattr(rec, "repo_id", None) or model_key
        return None

    def _propose_with_vlm(self, media: Any, label: str, target_name: str, prompt: str, model_key: str, threshold: float, annotation_type: str, device: str, options: dict[str, Any]) -> list[dict[str, Any]]:
        if not self.models:
            return []
        system_prompt = (
            "Return ONLY JSON. Propose annotations for the image. Use this schema: "
            "{\"proposals\":[{\"label\":string,\"annotation_type\":\"bbox|mask|polygon|pose2d|pose3d\","
            "\"bbox\":{\"x1\":number,\"y1\":number,\"x2\":number,\"y2\":number},\"polygon\":[[x,y]],"
            "\"keypoints_2d\":[{\"name\":string,\"x\":number,\"y\":number}],\"keypoints_3d\":[{\"name\":string,\"x\":number,\"y\":number,\"z\":number}],\"confidence\":number}]}"
        )
        req = type("ChatReq", (), {})()
        req.model_name = model_key
        req.prompt = f"{system_prompt}\nTask: {prompt or label or target_name}. Label: {label}. Annotation type: {annotation_type}. Confidence threshold: {threshold}."
        req.dataset_id = None; req.media_ids = [int(media.id)]; req.external_paths = []; req.history = []
        req.use_selected_media = True; req.apply_suggested_tags = False; req.apply_suggested_caption = False
        req.device = device; req.options = options
        # Reuse the real ModelService chat path when the selected model is a VLM/API route.
        response = self.models.chat(req)
        return parse_json_proposals(response.get("response", ""), label=label, model_key=model_key, annotation_type=annotation_type)

    def _run_detection_guide(
        self,
        media_id: int,
        *,
        model_key: str,
        class_query: str,
        threshold: float,
        device: str,
        options: dict[str, Any],
    ) -> dict[str, Any]:
        guide_options = dict(options.get('guide_detection_options') or {})
        guide_options.update({
            'class_query': class_query,
            'strict_class_filter': True,
            'annotation_label': '',
            'max_proposals': int(options.get('guide_max_proposals') or options.get('max_proposals') or 32),
            'run_id': f"{options.get('run_id') or uuid.uuid4().hex[:12]}_guide",
        })
        result = self.propose_annotation(
            media_id=int(media_id),
            label=class_query or 'object',
            target_name='',
            prompt=class_query,
            model_key=model_key,
            threshold=float(options.get('guide_threshold') if options.get('guide_threshold') is not None else threshold),
            annotation_type='bbox',
            save=False,
            create_mask=False,
            source='model',
            device=device,
            options=guide_options,
        )
        if not result.get('ok'):
            raise RuntimeError(f"Detector-guided segmentation failed: {result.get('error') or 'guide detector returned no boxes'}")
        boxes = [proposal.get('bbox') for proposal in result.get('proposals') or [] if proposal.get('bbox')]
        if not boxes:
            raise RuntimeError(f"Guide detector {model_key} returned no bounding boxes for class {class_query!r}.")
        return {'boxes': boxes, 'result': result}

    def propose_annotation(self, media_id: int, label: str = 'object', target_name: str = '', prompt: str = '', model_key: str = 'demo_center_bbox', threshold: float = 0.25, annotation_type: str = 'bbox', save: bool = False, create_mask: bool = False, source: str = 'model', device: str = 'auto', options: dict[str, Any] | None = None) -> dict[str, Any]:
        """Create or preview bbox/mask/pose proposals for one media item."""
        media = self.media.get(int(media_id))
        if not media:
            raise ValueError(f'Unknown media_id={media_id}')
        label = label or target_name or 'object'
        prompt = (prompt or label or 'object').strip()
        options = dict(options or {})
        options.setdefault('run_id', uuid.uuid4().hex[:12])
        if create_mask and annotation_type == 'bbox':
            annotation_type = 'bbox_mask'
        proposals: list[dict[str, Any]] = []
        adapter_error = None
        warnings: list[str] = []
        conditioning: dict[str, Any] = {}
        out_dir = self.annotations_dir / 'model_masks'
        model_status = self.annotation_model_status(model_key, options)
        if model_key in {'demo_center_bbox', '', 'none', '__none__'}:
            return {
                'ok': False,
                'media_id': int(media_id),
                'proposals': [],
                'saved': [],
                'count': 0,
                'error': model_status.get('message') or 'No annotation model selected.',
                'model_status': model_status,
            }
        try:
            rec = self.models.registry.get_record(model_key) if self.models else None
            caps = set(getattr(rec, 'capabilities', []) or []) if rec else set()
            kind = getattr(rec, 'kind', '') if rec else ''
            provider = getattr(rec, 'provider', '') if rec else ''
            spatial_caps = {'detect', 'bbox', 'segment', 'mask', 'video_mask', 'pose', 'pose2d', 'pose3d', 'keypoints', 'annotation', 'open_vocabulary', 'custom_pt_compatible'}
            if model_key == 'dataset-assistant' or ('no-model-download' in caps and not (caps & spatial_caps)):
                raise RuntimeError('The built-in dataset assistant is not a spatial annotation model. Select SAM, SAM-HQ, SAM2, YOLO, a custom local checkpoint, or an API/VLM adapter that explicitly supports annotation proposals.')
            checkpoint = self._resolve_annotation_checkpoint(model_key, options)
            backend = str(getattr(rec, 'recommended_backend', '') or '').lower()
            custom_type = str(options.get('custom_model_type') or '').lower()
            has_custom_path = bool(options.get('local_model_path') or options.get('custom_local_path') or options.get('checkpoint_path'))
            is_mediapipe_pose = backend == 'mediapipe_tasks' or model_key.startswith('mediapipe-pose-') or (has_custom_path and custom_type == 'mediapipe')
            is_mmpose = provider == 'mmpose' or backend == 'mmpose_inferencer' or model_key.startswith('mmpose-') or (has_custom_path and custom_type == 'mmpose')
            is_yolo = provider == 'ultralytics' or 'yolo' in caps or (has_custom_path and str(checkpoint or '').lower().endswith('.pt') and custom_type in {'auto', 'yolo'})
            is_sam2 = 'sam2' in caps or backend == 'sam2' or model_key.startswith('sam2') or (has_custom_path and custom_type == 'sam2')
            is_hq_sam = 'hq_sam' in caps or model_key.startswith('sam-hq-') or (has_custom_path and custom_type == 'sam_hq')
            is_sam = (not is_yolo) and (not is_sam2) and ('sam' in caps or 'segment_anything' in backend or model_key.startswith(('sam-', 'sam-hq-', 'custom-sam')) or (has_custom_path and custom_type in {'sam', 'sam_hq'}))
            class_info = self.annotation_model_classes(model_key, options, limit=0)
            class_query = str(options.get('class_query') or '').strip()
            semantic_class_query = class_query.lower() not in {'', '*', 'all', 'any', 'object', 'objects', 'everything'}
            conditioning = {
                'mode': class_info.get('mode'),
                'prompt_affects_geometry': class_info.get('prompt_affects_geometry'),
                'class_query': class_query,
                'class_source': class_info.get('source'),
            }
            if is_mediapipe_pose:
                if not checkpoint:
                    raise RuntimeError(f'MediaPipe Pose Landmarker task bundle was not found for {model_key}. Use Download Weights first or provide a local .task path.')
                proposals = propose_with_mediapipe(
                    media.path, checkpoint, model_key=model_key, label=label,
                    threshold=threshold, annotation_type=annotation_type, options=options,
                )
                conditioning.update({'mode': 'pose_landmarks', 'skeleton_template': 'blazepose33', 'prompt_affects_geometry': False})
            elif is_mmpose:
                proposals = propose_with_mmpose(
                    media.path, model_key=model_key, label=label, threshold=threshold,
                    annotation_type=annotation_type, device=device, options=options,
                )
                conditioning.update({'mode': 'pose_inference', 'prompt_affects_geometry': False})
            elif is_yolo:
                options.setdefault('strict_class_filter', True)
                proposals = propose_with_yolo(media.path, checkpoint or model_key, model_key=model_key, label=label, threshold=threshold, annotation_type=annotation_type, device=device, output_dir=out_dir, options=options)
            elif is_sam2:
                if not checkpoint:
                    raise RuntimeError(f'SAM2 checkpoint was not found for {model_key}. Download weights or provide a local SAM2 checkpoint path.')
                bbox_prompt = options.get('bbox_prompt') or options.get('prompt_bbox')
                has_points = bool(options.get('point_prompts') or options.get('positive_points') or options.get('negative_points'))
                guide_key = str(options.get('guide_detection_model_key') or '').strip()
                if not bbox_prompt and not options.get('bbox_prompts') and not has_points and guide_key:
                    if not class_query:
                        raise RuntimeError('Detector-guided segmentation requires a class/token to find.')
                    guide = self._run_detection_guide(int(media_id), model_key=guide_key, class_query=class_query, threshold=threshold, device=device, options=options)
                    options['bbox_prompts'] = guide['boxes']
                    conditioning.update({'mode': 'detector_guided_bbox_prompts', 'guide_model_key': guide_key, 'guide_box_count': len(guide['boxes']), 'prompt_affects_geometry': True})
                elif has_points:
                    conditioning.update({'mode': 'positive_negative_point_prompts', 'point_count': len(options.get('point_prompts') or []) + len(options.get('positive_points') or []) + len(options.get('negative_points') or []), 'prompt_affects_geometry': True})
                elif semantic_class_query and not bbox_prompt and not options.get('bbox_prompts'):
                    raise RuntimeError('SAM2 is class-agnostic and cannot use a class/name token to locate an object by itself. Clear the class token to generate class-agnostic automatic masks, draw/copy a bbox prompt, add positive/negative point prompts, or enable detector-guided segmentation so a detector first finds that class.')
                proposals = propose_with_sam2(media.path, checkpoint, model_key=model_key, label=label, threshold=threshold, annotation_type=annotation_type, bbox_prompt=options.get('bbox_prompt') or options.get('prompt_bbox'), device=device, output_dir=out_dir, options=options)
            elif is_sam:
                if not checkpoint:
                    raise RuntimeError(f'SAM checkpoint was not found for {model_key}. Download weights or provide a local SAM/SAM-HQ checkpoint path.')
                model_type = options.get('sam_model_type') or {'sam-vit-b': 'vit_b', 'sam-vit-l': 'vit_l', 'sam-vit-h': 'vit_h', 'sam-hq-vit-b': 'vit_b', 'sam-hq-vit-l': 'vit_l', 'sam-hq-vit-h': 'vit_h'}.get(model_key, 'vit_b')
                sam_options = dict(options)
                if is_hq_sam:
                    sam_options['hq_sam'] = True
                bbox_prompt = options.get('bbox_prompt') or options.get('prompt_bbox')
                has_points = bool(sam_options.get('point_prompts') or sam_options.get('positive_points') or sam_options.get('negative_points'))
                guide_key = str(options.get('guide_detection_model_key') or '').strip()
                if not bbox_prompt and not sam_options.get('bbox_prompts') and not has_points and guide_key:
                    if not class_query:
                        raise RuntimeError('Detector-guided segmentation requires a class/token to find.')
                    guide = self._run_detection_guide(int(media_id), model_key=guide_key, class_query=class_query, threshold=threshold, device=device, options=options)
                    sam_options['bbox_prompts'] = guide['boxes']
                    conditioning.update({'mode': 'detector_guided_bbox_prompts', 'guide_model_key': guide_key, 'guide_box_count': len(guide['boxes']), 'prompt_affects_geometry': True})
                elif has_points:
                    conditioning.update({'mode': 'positive_negative_point_prompts', 'point_count': len(sam_options.get('point_prompts') or []) + len(sam_options.get('positive_points') or []) + len(sam_options.get('negative_points') or []), 'prompt_affects_geometry': True})
                elif semantic_class_query and not bbox_prompt and not sam_options.get('bbox_prompts'):
                    raise RuntimeError('SAM/SAM-HQ is class-agnostic and cannot use a class/name token to locate an object by itself. Clear the class token to generate class-agnostic automatic masks, draw/copy a bbox prompt, add positive/negative point prompts, or enable detector-guided segmentation so a detector first finds that class.')
                proposals = propose_with_sam(media.path, checkpoint, model_key=model_key, model_type=model_type, label=label, threshold=threshold, annotation_type=annotation_type, bbox_prompt=options.get('bbox_prompt') or options.get('prompt_bbox'), device=device, output_dir=out_dir, options=sam_options)
            elif kind in {'pose3d'} or 'pose3d' in caps:
                # Contract rows can only save user-supplied pose metadata. They do not
                # generate synthetic poses without a real trained adapter/API route.
                if options.get('keypoints_3d') or options.get('frames'):
                    proposals = [{
                        'label': label, 'target_name': target_name or label, 'annotation_type': 'pose3d',
                        'bbox': {}, 'polygon': [], 'confidence': 1.0, 'model_key': model_key, 'source': 'user_contract',
                        'metadata': {'keypoints_3d': options.get('keypoints_3d') or [], 'edges': options.get('edges') or [], 'frames': options.get('frames') or []}
                    }]
                else:
                    raise RuntimeError('This pose3d catalog row is a dataset/adapter contract, not a runnable model. Add keypoints manually or select a real pose model/API adapter.')
            elif ('annotation' in caps or 'open_vocabulary' in caps or provider in {'openai', 'openrouter', 'anthropic'}):
                proposals = self._propose_with_vlm(media, label, target_name, prompt, model_key, threshold, annotation_type, device, options)
            else:
                raise RuntimeError(f'No annotation adapter is implemented for model {model_key!r}.')
        except Exception as exc:
            adapter_error = str(exc)
            return {
                'ok': False,
                'media_id': int(media_id),
                'proposals': [],
                'saved': [],
                'count': 0,
                'error': adapter_error,
                'model_status': self.annotation_model_status(model_key, options),
                'conditioning': conditioning,
                'warnings': warnings,
            }
        if not proposals:
            return {
                'ok': False,
                'media_id': int(media_id),
                'proposals': [],
                'saved': [],
                'count': 0,
                'error': f'Model {model_key} ran but returned no annotation proposals at threshold {threshold}. Lower the threshold, adjust the prompt/bbox prompt, or choose a different model.',
                'model_status': self.annotation_model_status(model_key, options),
                'conditioning': conditioning,
                'warnings': warnings,
            }
        # Fill target/source fields consistently.
        for prop in proposals:
            prop.setdefault('target_name', target_name or prop.get('label') or label)
            prop.setdefault('source', source or prop.get('source') or 'model')
            prop.setdefault('model_key', model_key)
            prop.setdefault('prompt', prompt)
            prop.setdefault('device', device)
            if 'mask' in annotation_type and prop.get('annotation_type') == 'bbox':
                prop['annotation_type'] = 'bbox_mask'
        saved: list[dict[str, Any]] = []
        if save:
            for prop in proposals:
                saved.append(self.add_annotation(
                    media_id=int(media_id),
                    label=prop.get('label') or label,
                    annotation_type=prop.get('annotation_type') or ('bbox_mask' if create_mask else annotation_type),
                    bbox=prop.get('bbox') or {},
                    polygon=prop.get('polygon') or [],
                    mask_path=prop.get('mask_path') or '',
                    target_name=prop.get('target_name') or target_name,
                    source=prop.get('source') or source,
                    model_key=prop.get('model_key') or model_key,
                    confidence=prop.get('confidence'),
                    metadata=prop.get('metadata') or {},
                ))
        confidence_values = [float(prop.get('confidence')) for prop in proposals if prop.get('confidence') is not None]
        diagnostics = {
            'proposal_count': len(proposals),
            'confidence_min': min(confidence_values) if confidence_values else None,
            'confidence_max': max(confidence_values) if confidence_values else None,
            'class_labels': sorted({str(prop.get('label') or '') for prop in proposals if prop.get('label')}),
            'run_id': options.get('run_id'),
            'max_proposals': options.get('max_proposals'),
        }
        return {
            'ok': True,
            'media_id': int(media_id),
            'proposals': proposals,
            'saved': saved,
            'count': len(proposals),
            'model_status': self.annotation_model_status(model_key, options),
            'conditioning': conditioning,
            'warnings': warnings,
            'diagnostics': diagnostics,
        }

    def create_training_set(self, name: str, query: str = '', dataset_id: int | None = None, train_ratio: float = 0.9, seed: int = 42, description: str = '') -> dict[str, Any]:
        universe = self._query_universe(0, dataset_id, 'all_images')
        ids = sorted(_evaluate_ast(_parse_query(query), self._tag_lookup(dataset_id), universe)) if query.strip() else sorted(universe)
        rng = random.Random(int(seed)); rng.shuffle(ids)
        split_at = int(len(ids) * float(train_ratio)) if ids else 0
        train = set(ids[:split_at])
        root = self.training_dir / _safe_name(name)
        root.mkdir(parents=True, exist_ok=True)
        now = now_iso()
        with self.db._lock, self.db.connect() as conn:
            cur = conn.execute('INSERT INTO training_sets(name, dataset_id, query, description, root_path, export_format, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)', (name, dataset_id, query, description, str(root), 'working_set', now))
            set_id = int(cur.lastrowid)
            conn.executemany('INSERT INTO training_set_items(training_set_id, media_id, split, include_reason, created_at) VALUES (?, ?, ?, ?, ?)', [(set_id, mid, 'train' if mid in train else 'val', f'query:{query or "<all>"}', now) for mid in ids])
        return {'training_set_id': set_id, 'name': name, 'count': len(ids), 'train': len(train), 'val': len(ids) - len(train), 'root_path': str(root)}

    def export_yolo(self, training_set_id: int, output_dir: str | None = None, task: str = 'detection', label_filter: str = '') -> dict[str, Any]:
        ts = self.db.query_one('SELECT * FROM training_sets WHERE id=?', (int(training_set_id),))
        if not ts:
            raise ValueError(f'Unknown training_set_id={training_set_id}')
        out = Path(output_dir or ts.get('root_path') or (self.training_dir / f'set_{training_set_id}')).expanduser()
        label_to_id: dict[str, int] = {}
        exported_images = exported_labels = 0
        rows = self.db.query(
            """
            SELECT tsi.media_id, tsi.split, m.path, m.width, m.height FROM training_set_items tsi
            JOIN media m ON m.id=tsi.media_id WHERE tsi.training_set_id=? ORDER BY tsi.media_id
            """,
            (int(training_set_id),),
        )
        for row in rows:
            src = Path(row['path'])
            if not src.exists():
                continue
            img_dst = out / 'images' / row['split'] / src.name
            img_dst.parent.mkdir(parents=True, exist_ok=True)
            if src.resolve() != img_dst.resolve() and not img_dst.exists():
                shutil.copy2(src, img_dst)
            anns = self.list_annotations(media_id=int(row['media_id']), label=label_filter or None, limit=5000)
            lines: list[str] = []
            w, h = int(row.get('width') or 0), int(row.get('height') or 0)
            if not w or not h:
                with Image.open(src) as im:
                    w, h = im.size
            for ann in anns:
                label = ann.get('label') or 'object'
                if label not in label_to_id:
                    label_to_id[label] = len(label_to_id)
                cid = label_to_id[label]
                if task == 'segmentation' and ann.get('polygon'):
                    vals = [str(cid)]
                    for x, y in ann['polygon']:
                        vals.append(f'{float(x)/max(w,1):.6f}'); vals.append(f'{float(y)/max(h,1):.6f}')
                    lines.append(' '.join(vals))
                elif ann.get('bbox'):
                    x1, y1, x2, y2 = _bbox_to_xyxy(ann['bbox'])
                    xc, yc = ((x1 + x2) / 2.0) / max(w, 1), ((y1 + y2) / 2.0) / max(h, 1)
                    bw, bh = abs(x2 - x1) / max(w, 1), abs(y2 - y1) / max(h, 1)
                    lines.append(f'{cid} {xc:.6f} {yc:.6f} {bw:.6f} {bh:.6f}')
            label_dst = out / 'labels' / row['split'] / f'{src.stem}.txt'
            label_dst.parent.mkdir(parents=True, exist_ok=True)
            label_dst.write_text('\n'.join(lines), encoding='utf-8')
            exported_images += 1; exported_labels += len(lines)
        names = {idx: label for label, idx in label_to_id.items()}
        data_yaml = out / 'data.yaml'
        data_yaml.write_text('\n'.join([f'path: {out.as_posix()}', 'train: images/train', 'val: images/val', f'nc: {len(names)}', 'names:', *[f'  {idx}: {label}' for idx, label in names.items()]]), encoding='utf-8')
        return {'output_dir': str(out), 'data_yaml': str(data_yaml), 'task': task, 'images': exported_images, 'labels': exported_labels, 'classes': names}

    def export_caption_jsonl(self, training_set_id: int, output_dir: str | None = None) -> dict[str, Any]:
        ts = self.db.query_one('SELECT * FROM training_sets WHERE id=?', (int(training_set_id),))
        if not ts:
            raise ValueError(f'Unknown training_set_id={training_set_id}')
        out = Path(output_dir or ts.get('root_path') or (self.training_dir / f'set_{training_set_id}')).expanduser()
        out.mkdir(parents=True, exist_ok=True)
        rows = self.db.query(
            """
            SELECT tsi.media_id, tsi.split, m.path, c.caption FROM training_set_items tsi
            JOIN media m ON m.id=tsi.media_id LEFT JOIN captions c ON c.media_id=m.id
            WHERE tsi.training_set_id=? AND c.caption IS NOT NULL ORDER BY tsi.media_id
            """,
            (int(training_set_id),),
        )
        jsonl = out / 'captions.jsonl'
        with jsonl.open('w', encoding='utf-8') as f:
            for row in rows:
                f.write(json.dumps({'image': row['path'], 'caption': row['caption'], 'split': row['split'], 'media_id': row['media_id']}, ensure_ascii=False) + '\n')
        return {'output_dir': str(out), 'jsonl': str(jsonl), 'rows': len(rows)}

    def create_training_job(self, name: str, task: str, model_key: str = '', training_set_id: int | None = None, config: dict[str, Any] | None = None) -> dict[str, Any]:
        out = self.training_dir / _safe_name(name)
        out.mkdir(parents=True, exist_ok=True)
        now = now_iso()
        job_id = self.db.execute(
            'INSERT INTO training_jobs(name, task, model_key, training_set_id, output_dir, config_json, status, message, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (name, task, model_key or '', training_set_id, str(out), json.dumps(config or {}), 'created', 'Training script scaffold created.', now, now),
        )
        script = self.generate_training_script(job_id)
        return {'training_job_id': job_id, 'output_dir': str(out), 'script': script}

    def generate_training_script(self, training_job_id: int) -> str:
        job = self.db.query_one('SELECT * FROM training_jobs WHERE id=?', (int(training_job_id),))
        if not job:
            raise ValueError(f'Unknown training_job_id={training_job_id}')
        cfg = _loads(job.get('config_json'), {})
        out = Path(job.get('output_dir') or self.training_dir / f'job_{training_job_id}')
        out.mkdir(parents=True, exist_ok=True)
        script = out / ('train_job.bat' if _is_windowsish() else 'train_job.sh')
        if job['task'] in {'detection', 'segmentation', 'yoloe_detection', 'yoloe_segmentation'}:
            yolo_task = 'segment' if 'seg' in job['task'] else 'detect'
            command = f'yolo {yolo_task} train model="{cfg.get("model", job.get("model_key") or "yolo11n.pt")}" data="{cfg.get("data_yaml", "data.yaml")}" epochs={int(cfg.get("epochs", 50))} imgsz={int(cfg.get("imgsz", 640))} batch={cfg.get("batch", "auto")} device={cfg.get("device", "0")} project="{out}" name="weights"'
        elif job['task'] in {'captioning', 'vlm_caption_finetune'}:
            command = 'echo Caption/VLM fine-tuning scaffold. Insert your selected trainer command here.'
        else:
            command = 'echo Training job scaffold. Edit with the chosen trainer command.'
        if script.suffix == '.bat':
            script.write_text('@echo off\ncd /d %~dp0\n' + command + '\n', encoding='utf-8')
        else:
            script.write_text('#!/usr/bin/env bash\ncd "$(dirname "$0")"\n' + command + '\n', encoding='utf-8')
            script.chmod(0o755)
        return str(script)


def _loads(text: str | None, default: Any) -> Any:
    if not text:
        return default
    try:
        return json.loads(text)
    except Exception:
        return default


def _bbox_to_xyxy(bbox: dict[str, Any]) -> tuple[float, float, float, float]:
    if {'x1', 'y1', 'x2', 'y2'}.issubset(bbox):
        return float(bbox['x1']), float(bbox['y1']), float(bbox['x2']), float(bbox['y2'])
    if {'x', 'y', 'w', 'h'}.issubset(bbox):
        x, y, w, h = float(bbox['x']), float(bbox['y']), float(bbox['w']), float(bbox['h'])
        return x, y, x + w, y + h
    if isinstance(bbox, list) and len(bbox) == 4:
        return float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])
    return 0.0, 0.0, 0.0, 0.0


def _path_is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except Exception:
        return False


def _is_windowsish() -> bool:
    import platform
    return platform.system().lower().startswith('win')

# v5.28 spatial-layer geometry/mask helpers.  These are deliberately model-agnostic:
# they only transform geometry or user/model-produced mask pixels already present.
def merge_bboxes(
    boxes: Sequence[dict[str, Any]],
    operation: str = 'union',
    confidences: Sequence[float | None] | None = None,
    *,
    width: int | float | None = None,
    height: int | float | None = None,
) -> dict[str, float]:
    parsed = [_bbox_to_xyxy(dict(box or {})) for box in boxes]
    parsed = [(x1, y1, x2, y2) for x1, y1, x2, y2 in parsed if x2 > x1 and y2 > y1]
    if not parsed:
        raise ValueError('No valid bounding boxes were selected.')
    op = str(operation or 'union').lower()
    if op in {'union', 'envelope', 'enclosing'}:
        x1 = min(row[0] for row in parsed); y1 = min(row[1] for row in parsed)
        x2 = max(row[2] for row in parsed); y2 = max(row[3] for row in parsed)
    elif op in {'intersection', 'overlap'}:
        x1 = max(row[0] for row in parsed); y1 = max(row[1] for row in parsed)
        x2 = min(row[2] for row in parsed); y2 = min(row[3] for row in parsed)
        if x2 <= x1 or y2 <= y1:
            raise ValueError('The selected boxes do not share a non-empty intersection.')
    elif op in {'weighted_average', 'confidence_weighted', 'average', 'consensus'}:
        values = list(confidences or [])
        weights = ([1.0 for _ in parsed] if op in {'average', 'consensus'} else [max(0.000001, float(values[i])) if i < len(values) and values[i] is not None else 1.0 for i in range(len(parsed))])
        total = sum(weights) or float(len(parsed))
        x1 = sum(row[0] * weights[i] for i, row in enumerate(parsed)) / total
        y1 = sum(row[1] * weights[i] for i, row in enumerate(parsed)) / total
        x2 = sum(row[2] * weights[i] for i, row in enumerate(parsed)) / total
        y2 = sum(row[3] * weights[i] for i, row in enumerate(parsed)) / total
    elif op == 'largest':
        x1, y1, x2, y2 = max(parsed, key=lambda row: (row[2] - row[0]) * (row[3] - row[1]))
    else:
        raise ValueError(f'Unsupported bbox merge operation: {operation}')
    if width is not None:
        x1 = max(0.0, min(float(width), x1)); x2 = max(0.0, min(float(width), x2))
    if height is not None:
        y1 = max(0.0, min(float(height), y1)); y2 = max(0.0, min(float(height), y2))
    if x2 <= x1 or y2 <= y1:
        raise ValueError('The merged bounding box is empty after clipping.')
    return {'x1': float(x1), 'y1': float(y1), 'x2': float(x2), 'y2': float(y2)}


def annotation_to_mask(row: dict[str, Any], size: tuple[int, int]):
    import numpy as np
    width, height = int(size[0]), int(size[1])
    mask_path = str(row.get('mask_path') or '')
    if mask_path and Path(mask_path).exists():
        with Image.open(mask_path) as image:
            mask = image.convert('L')
            if mask.size != (width, height):
                mask = mask.resize((width, height), Image.Resampling.NEAREST)
            return np.asarray(mask, dtype=np.uint8)
    canvas = Image.new('L', (width, height), 0)
    polygon = row.get('polygon') or _loads(row.get('polygon_json'), [])
    bbox = row.get('bbox') or _loads(row.get('bbox_json'), {})
    draw = ImageDraw.Draw(canvas)
    if polygon and len(polygon) >= 3:
        draw.polygon([(float(p[0] if isinstance(p, (list, tuple)) else p.get('x', 0)), float(p[1] if isinstance(p, (list, tuple)) else p.get('y', 0))) for p in polygon], fill=255)
    elif bbox:
        draw.rectangle(_bbox_to_xyxy(bbox), fill=255)
    return np.asarray(canvas, dtype=np.uint8)


def combine_masks(masks: Sequence[Any], operation: str = 'union', *, threshold: int = 1):
    """Composite grayscale/alpha masks while preserving soft edges.

    Values below ``threshold`` are cleared, but surviving pixel strengths remain
    intact. This keeps brush opacity, feathering, imported alpha masks, and
    model-produced soft masks useful after compositing.
    """
    arrays = [np.asarray(mask, dtype=np.uint8) for mask in masks]
    if not arrays:
        raise ValueError('Select at least one mask layer.')
    shape = arrays[0].shape
    if any(array.shape != shape for array in arrays):
        raise ValueError('All mask layers must have matching image dimensions.')
    cutoff = max(0, min(255, int(threshold)))
    prepared = [np.where(array >= cutoff, array, 0).astype(np.uint8) if cutoff > 0 else array.copy() for array in arrays]
    op = str(operation or 'union').lower()
    result = prepared[0].copy()
    if op in {'union', 'add', 'maximum'}:
        for array in prepared[1:]:
            result = np.maximum(result, array)
    elif op in {'intersection', 'minimum'}:
        for array in prepared[1:]:
            result = np.minimum(result, array)
    elif op in {'subtract', 'difference'}:
        for array in prepared[1:]:
            result = np.clip(result.astype(np.int16) - array.astype(np.int16), 0, 255).astype(np.uint8)
    elif op in {'xor', 'exclusive_or'}:
        for array in prepared[1:]:
            result = np.abs(result.astype(np.int16) - array.astype(np.int16)).astype(np.uint8)
    elif op == 'replace':
        result = prepared[-1]
    else:
        raise ValueError(f'Unsupported mask merge operation: {operation}')
    return result.astype(np.uint8)


def postprocess_mask(mask: Any, *, feather: int = 0, grow: int = 0) -> np.ndarray:
    array = np.asarray(mask, dtype=np.uint8)
    image = Image.fromarray(array, mode='L')
    grow_value = int(grow or 0)
    if grow_value > 0:
        size = max(3, grow_value * 2 + 1)
        if size % 2 == 0:
            size += 1
        image = image.filter(ImageFilter.MaxFilter(size=size))
    elif grow_value < 0:
        size = max(3, abs(grow_value) * 2 + 1)
        if size % 2 == 0:
            size += 1
        image = image.filter(ImageFilter.MinFilter(size=size))
    if int(feather or 0) > 0:
        image = image.filter(ImageFilter.GaussianBlur(radius=float(feather)))
    return np.asarray(image, dtype=np.uint8)


def mask_bbox(mask: Any) -> dict[str, float]:
    import numpy as np
    array = np.asarray(mask)
    ys, xs = np.nonzero(array > 0)
    if not len(xs):
        return {}
    # x2/y2 are exclusive bounds, matching common detector conventions.
    return {'x1': float(xs.min()), 'y1': float(ys.min()), 'x2': float(xs.max() + 1), 'y2': float(ys.max() + 1)}


def save_mask(mask: Any, output_dir: Path, stem: str) -> str:
    import numpy as np
    output_dir.mkdir(parents=True, exist_ok=True)
    safe = _safe_name(stem)
    path = output_dir / f'{safe}_{uuid.uuid4().hex[:12]}.png'
    array = np.asarray(mask, dtype=np.uint8)
    Image.fromarray(array, mode='L').save(path, format='PNG', optimize=False)
    return str(path.resolve())


def magic_select_mask(
    image_path: str,
    x: float,
    y: float,
    *,
    method: str = 'flood_fill',
    tolerance: int = 24,
    connectivity: int = 8,
    bbox: dict[str, Any] | None = None,
    iterations: int = 5,
    radius_ratio: float = 0.22,
    feather: int = 0,
):
    with Image.open(image_path) as source:
        rgb = source.convert('RGB')
    image_rgb = np.asarray(rgb, dtype=np.uint8)
    height, width = image_rgb.shape[:2]
    seed_x = max(0, min(width - 1, int(round(x))))
    seed_y = max(0, min(height - 1, int(round(y))))
    tolerance = max(0, min(255, int(tolerance)))
    method = str(method or 'flood_fill').lower()
    try:
        import cv2  # optional acceleration / GrabCut runtime
    except Exception:
        cv2 = None

    if method in {'flood_fill', 'magic_wand', 'contiguous'}:
        if cv2 is not None:
            bgr = image_rgb[:, :, ::-1].copy()
            flood_mask = np.zeros((height + 2, width + 2), dtype=np.uint8)
            flags = (8 if int(connectivity) == 8 else 4) | cv2.FLOODFILL_MASK_ONLY | cv2.FLOODFILL_FIXED_RANGE | (255 << 8)
            cv2.floodFill(bgr, flood_mask, (seed_x, seed_y), (0, 0, 0), (tolerance,) * 3, (tolerance,) * 3, flags)
            mask = flood_mask[1:-1, 1:-1]
        else:
            # Pillow's floodfill gives a dependency-free contiguous magic-wand
            # approximation and uses a per-channel threshold through thresh.
            fill = Image.new('L', (width, height), 0)
            seed_color = tuple(int(v) for v in image_rgb[seed_y, seed_x])
            color_distance = np.max(np.abs(image_rgb.astype(np.int16) - np.asarray(seed_color, dtype=np.int16)), axis=2)
            allowed = Image.fromarray((color_distance <= tolerance).astype(np.uint8) * 255, mode='L')
            # Connected component from the clicked point using a small explicit stack.
            allowed_array = np.asarray(allowed, dtype=np.uint8) > 0
            visited = np.zeros((height, width), dtype=bool)
            stack = [(seed_x, seed_y)]
            neighbours = ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)) if int(connectivity) == 8 else ((1,0),(-1,0),(0,1),(0,-1))
            while stack:
                px, py = stack.pop()
                if px < 0 or py < 0 or px >= width or py >= height or visited[py, px] or not allowed_array[py, px]:
                    continue
                visited[py, px] = True
                stack.extend((px + dx, py + dy) for dx, dy in neighbours)
            mask = visited.astype(np.uint8) * 255
    elif method in {'color_range', 'color_similarity', 'noncontiguous'}:
        seed = image_rgb[seed_y, seed_x].astype(np.int32)
        delta = image_rgb.astype(np.int32) - seed
        distance = np.sqrt(np.sum(delta * delta, axis=2))
        mask = (distance <= max(1.0, tolerance * math.sqrt(3.0))).astype(np.uint8) * 255
    elif method in {'grabcut', 'object'}:
        if cv2 is None:
            raise ValueError('GrabCut Magic Select requires opencv-python. Choose Flood Fill or Color Similarity, or install OpenCV.')
        bgr = image_rgb[:, :, ::-1].copy()
        gc_mask = np.zeros((height, width), dtype=np.uint8)
        if bbox:
            x1, y1, x2, y2 = _bbox_to_xyxy(bbox)
            left = max(0, min(width - 1, int(x1))); top = max(0, min(height - 1, int(y1)))
            right = max(left + 1, min(width, int(x2))); bottom = max(top + 1, min(height, int(y2)))
            rect = (left, top, max(1, right-left), max(1, bottom-top))
        else:
            radius_x = max(8, int(width * float(radius_ratio)))
            radius_y = max(8, int(height * float(radius_ratio)))
            left = max(0, seed_x-radius_x); top = max(0, seed_y-radius_y)
            right = min(width, seed_x+radius_x); bottom = min(height, seed_y+radius_y)
            rect = (left, top, max(1, right-left), max(1, bottom-top))
        bgd = np.zeros((1,65), np.float64); fgd = np.zeros((1,65), np.float64)
        cv2.grabCut(bgr, gc_mask, rect, bgd, fgd, max(1,int(iterations)), cv2.GC_INIT_WITH_RECT)
        mask = np.where((gc_mask == cv2.GC_FGD) | (gc_mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
    elif method == 'ellipse':
        mask_image = Image.new('L', (width, height), 0)
        rx = max(3, int(width * float(radius_ratio))); ry = max(3, int(height * float(radius_ratio)))
        ImageDraw.Draw(mask_image).ellipse((seed_x-rx, seed_y-ry, seed_x+rx, seed_y+ry), fill=255)
        mask = np.asarray(mask_image, dtype=np.uint8)
    else:
        raise ValueError(f'Unsupported Magic Select method: {method}')
    return postprocess_mask(mask, feather=feather)

