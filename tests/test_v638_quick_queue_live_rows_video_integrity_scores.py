from pathlib import Path

import data_curation_tool

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_version_bumped_to_v5844():
    assert data_curation_tool.__version__ == "5.8.48"
    assert 'version = "5.8.48"' in read("pyproject.toml")
    assert "v5.8.48 Update" in read("README.md")


def test_quick_tag_queue_preserves_all_selected_rows_and_live_placeholders():
    app = read("data_curation_tool/static/app.js")
    assert "queuePlaceholderJob" in app
    assert "pendingTemps" in app and "state.jobs = [...pendingTemps, ...serverJobs]" in app
    assert "Submit queue requests in parallel" in app or "submit queue requests in parallel" in app
    assert "const placeholders = new Map()" in app
    assert "for (const body of runBodies)" in app
    assert "upsertJobRow(optimistic, placeholders.get(row.model_name))" in app
    assert "modelQueueRecentEnough" in app
    assert "includeRecent: scope === 'quick'" in app


def test_hover_prediction_scores_are_patched_from_job_results():
    app = read("data_curation_tool/static/app.js")
    assert "function patchTagScoresFromModelJob" in app
    assert "candidate_scores_by_media" in app
    assert "patchTagScoresFromModelJob(job)" in app
    assert "state.tagScores" in app


def test_backend_recovers_scores_for_normalized_string_tags_before_thresholding():
    svc = read("data_curation_tool/services/model_service.py")
    assert "score_lookup" in svc
    assert "_collect_scores(pred.raw)" in svc
    assert "score_lookup.get(_score_key(item), 1.0)" in svc
    assert "if score >= effective_threshold" in svc


def test_integrity_classifier_supports_video_sampling_options():
    svc = read("data_curation_tool/services/integrity_classifier_service.py")
    assert "VIDEO_EXTS" in svc
    assert "def _video_options" in svc
    assert "def _sample_video_frames_cv2" in svc
    assert "def _sample_video_frames_ffmpeg" in svc
    assert "def predict_media" in svc
    assert "max_score_with_mean" in svc
    app = read("data_curation_tool/static/app.js")
    assert "video_sampling" in app
    assert "highest_quality" in app
    assert "sampling_rate_fps" in app
    assert "compression_percent" in app


def test_thumbnail_path_has_opencv_cpu_gpu_fast_path():
    svc = read("data_curation_tool/services/media_service.py")
    assert "DCT_THUMB_WEBP_QUALITY" in svc
    assert "cv2.cuda" in svc
    assert "cv2.resize" in svc
    assert "INTER_AREA" in svc


def test_docs_added():
    assert "Quick Queue Live Rows" in read("docs/V5_8_44_QUICK_QUEUE_LIVE_ROWS_VIDEO_INTEGRITY_SCORES.md")
    assert "74-Quick-Queue-Live-Rows-Video-Integrity-Scores.md" in read("docs/wiki/_Sidebar.md")
