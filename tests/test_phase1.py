"""Phase 1 の動作確認テスト。

ハードコードした IR（:mod:`core.ir`）から AviUtl .exo ファイルと
YMM4 向け台本ファイル（JSON/CSV）が正しく出力されることを検証する。

出力ファイルは ``tests/output/`` に生成される。
"""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path

from core.ir import (
    DialogueLine,
    DialogueScript,
    EditedVideoTrack,
    PlaceholderObject,
    PlaceholderTrack,
    Project,
    VideoClip,
)
from core.time_utils import (
    format_timecode,
    frames_to_seconds,
    parse_timecode,
    seconds_to_frames,
)
from exporter.exo_exporter import build_exo_text, export_exo
from exporter.ymm4_script_exporter import export_ymm4_csv, export_ymm4_json

# テスト出力先ディレクトリ
OUTPUT_DIR = Path(__file__).resolve().parent / "output"

FPS = 30.0


def _build_sample_project() -> Project:
    """ハードコードされた仮データから Project を構築する。"""
    video_track = EditedVideoTrack(
        name="video",
        clips=[
            VideoClip(
                source_path="video1.mp4",
                source_start="12:00",
                source_end="14:30",
                timeline_start=0,
                timeline_end=seconds_to_frames(3.5, FPS),
            ),
            VideoClip(
                source_path="video2.mp4",
                source_start="00:05",
                source_end="00:08",
                timeline_start=seconds_to_frames(3.5, FPS),
                timeline_end=seconds_to_frames(5.5, FPS),
            ),
        ],
    )
    placeholder_track = PlaceholderTrack(
        name="placeholder",
        objects=[
            PlaceholderObject(
                text="AE2の自動クラフト設定ができたのだ！",
                start_frame=0,
                end_frame=seconds_to_frames(3.5, FPS),
                layer=1,
            ),
            PlaceholderObject(
                text="次は鉱石の自動精錬だ！",
                start_frame=seconds_to_frames(3.5, FPS),
                end_frame=seconds_to_frames(5.5, FPS),
                layer=1,
            ),
        ],
    )
    script = DialogueScript(
        title="テスト台本",
        lines=[
            DialogueLine(
                character="ずんだもん",
                text="AE2の自動クラフト設定ができたのだ！",
                estimated_duration_sec=3.5,
                source_video_path="video1.mp4",
                highlight_start="12:00",
                highlight_end="14:30",
            ),
            DialogueLine(
                character="ずんだもん",
                text="次は鉱石の自動精錬だ！",
                estimated_duration_sec=2.0,
                source_video_path="video2.mp4",
                highlight_start="00:05",
                highlight_end="00:08",
            ),
        ],
    )
    return Project(
        name="テストプロジェクト",
        fps=FPS,
        width=1920,
        height=1080,
        video_track=video_track,
        placeholder_track=placeholder_track,
        script=script,
    )


# ---------------------------------------------------------------------------
# core/time_utils.py のテスト
# ---------------------------------------------------------------------------


def test_parse_timecode() -> None:
    """タイムコードのパースを検証する。"""
    assert parse_timecode("12:00") == 720.0
    assert parse_timecode("01:30.5") == 90.5
    assert parse_timecode("1:02:03") == 3723.0
    assert parse_timecode(3.5) == 3.5
    assert parse_timecode(10) == 10.0


def test_seconds_frames_conversion() -> None:
    """秒数/フレーム数の相互変換を検証する。"""
    assert seconds_to_frames(3.5, FPS) == 105
    assert seconds_to_frames(0.0, FPS) == 0
    assert frames_to_seconds(105, FPS) == 3.5
    assert frames_to_seconds(0, FPS) == 0.0


def test_format_timecode() -> None:
    """秒数からタイムコード文字列への変換を検証する。"""
    assert format_timecode(90.0) == "01:30"
    assert format_timecode(0.0) == "00:00"
    assert format_timecode(720.0) == "12:00"


# ---------------------------------------------------------------------------
# core/ir.py のテスト
# ---------------------------------------------------------------------------


def test_ir_properties() -> None:
    """IR のプロパティ（秒換算・フレーム長）を検証する。"""
    project = _build_sample_project()
    clip = project.video_track.clips[0]
    assert clip.source_start_sec == 720.0
    assert clip.source_end_sec == 870.0
    assert clip.duration_frames == 105

    obj = project.placeholder_track.objects[0]
    assert obj.duration_frames == 105


# ---------------------------------------------------------------------------
# exporter/exo_exporter.py のテスト
# ---------------------------------------------------------------------------


def test_build_exo_text() -> None:
    """.exo テキストの構造を検証する。"""
    project = _build_sample_project()
    text = build_exo_text(project)

    # [exedit] セクション
    assert "[exedit]" in text
    assert "width=1920" in text
    assert "height=1080" in text
    assert "rate=30" in text
    assert "length=165" in text  # 5.5 秒 * 30fps

    # 映像オブジェクト [0] / [0.0]
    assert "[0]" in text
    assert "start=0" in text
    assert "end=105" in text
    assert "name=動画" in text
    assert "[0.0]" in text
    assert "再生位置=720000" in text  # 12:00 = 720 秒 = 720000 ms
    assert "ファイル名=video1.mp4" in text

    # 映像オブジェクト [1] / [1.0]
    assert "[1]" in text
    assert "start=105" in text
    assert "end=165" in text
    assert "再生位置=5000" in text  # 00:05 = 5 秒 = 5000 ms
    assert "ファイル名=video2.mp4" in text

    # テキストオブジェクト [2] / [2.0]
    assert "[2]" in text
    assert "layer=1" in text
    assert "name=テキスト" in text
    assert "[2.0]" in text
    assert "テキスト=AE2の自動クラフト設定ができたのだ！" in text
    assert "テキスト=次は鉱石の自動精錬だ！" in text


def test_export_exo(tmp_path: Path) -> None:
    """.exo ファイルが出力され、内容が検証できることを確認する。"""
    project = _build_sample_project()
    output_path = str(tmp_path / "sample.exo")
    result = export_exo(project, output_path)

    assert result == output_path
    assert os.path.exists(output_path)
    with open(output_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert content.startswith("[exedit]")
    assert "ファイル名=video1.mp4" in content


# ---------------------------------------------------------------------------
# exporter/ymm4_script_exporter.py のテスト
# ---------------------------------------------------------------------------


def test_export_ymm4_json(tmp_path: Path) -> None:
    """YMM4 向け JSON 台本が正しく出力されることを確認する。"""
    project = _build_sample_project()
    output_path = str(tmp_path / "script.json")
    result = export_ymm4_json(project, output_path)

    assert result == output_path
    with open(output_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["title"] == "テスト台本"
    assert data["fps"] == FPS
    assert len(data["lines"]) == 2
    first = data["lines"][0]
    assert first["character"] == "ずんだもん"
    assert first["text"] == "AE2の自動クラフト設定ができたのだ！"
    assert first["estimatedDurationSec"] == 3.5
    assert first["sourceVideoPath"] == "video1.mp4"
    assert first["highlightStart"] == "12:00"
    assert first["highlightEnd"] == "14:30"


def test_export_ymm4_csv(tmp_path: Path) -> None:
    """YMM4 向け CSV 台本が正しく出力されることを確認する。"""
    project = _build_sample_project()
    output_path = str(tmp_path / "script.csv")
    result = export_ymm4_csv(project, output_path)

    assert result == output_path
    with open(output_path, "r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    assert len(rows) == 2
    assert rows[0]["character"] == "ずんだもん"
    assert rows[0]["text"] == "AE2の自動クラフト設定ができたのだ！"
    assert rows[0]["estimated_duration_sec"] == "3.5"
    assert rows[0]["source_video_path"] == "video1.mp4"
    assert rows[0]["highlight_start"] == "12:00"
    assert rows[0]["highlight_end"] == "14:30"


# ---------------------------------------------------------------------------
# 成果物の実出力（tests/output/ に生成）
# ---------------------------------------------------------------------------


def test_generate_sample_outputs() -> None:
    """ハードコードした IR から実ファイルを tests/output/ に生成する。"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    project = _build_sample_project()

    exo_path = export_exo(project, str(OUTPUT_DIR / "sample.exo"))
    json_path = export_ymm4_json(project, str(OUTPUT_DIR / "script.json"))
    csv_path = export_ymm4_csv(project, str(OUTPUT_DIR / "script.csv"))

    assert os.path.exists(exo_path)
    assert os.path.exists(json_path)
    assert os.path.exists(csv_path)


if __name__ == "__main__":
    # pytest を使わず直接実行した場合も成果物を生成できるようにする
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    project = _build_sample_project()
    print("EXO :", export_exo(project, str(OUTPUT_DIR / "sample.exo")))
    print("JSON:", export_ymm4_json(project, str(OUTPUT_DIR / "script.json")))
    print("CSV :", export_ymm4_csv(project, str(OUTPUT_DIR / "script.csv")))