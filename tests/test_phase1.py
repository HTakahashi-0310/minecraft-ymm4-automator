"""Phase 1 の動作確認テスト（YMM4 .ymmp 直接生成版）。

ハードコードした IR（:mod:`core.ir`）から YMM4 プロジェクト（.ymmp）と
台本ファイル（JSON/CSV）が正しく出力されることを検証する。

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
    Project,
    VideoItem,
    VoiceItem,
)
from core.time_utils import (
    format_timecode,
    format_ymm4_timecode,
    frames_to_seconds,
    parse_timecode,
    parse_ymm4_timecode,
    seconds_to_frames,
)
from exporter.ymm4_exporter import build_ymm4_dict, export_ymm4
from exporter.ymm4_script_exporter import export_ymm4_csv, export_ymm4_json

# テスト出力先ディレクトリ
OUTPUT_DIR = Path(__file__).resolve().parent / "output"

FPS = 30.0


def _build_sample_project() -> Project:
    """ハードコードされた仮データから Project を構築する。"""
    video_items = [
        VideoItem(
            file_path="video1.mp4",
            frame=0,
            length=seconds_to_frames(3.5, FPS),
            layer=0,
            content_offset=format_ymm4_timecode(720.0),  # 12:00
        ),
        VideoItem(
            file_path="video2.mp4",
            frame=seconds_to_frames(3.5, FPS),
            length=seconds_to_frames(2.0, FPS),
            layer=0,
            content_offset=format_ymm4_timecode(5.0),  # 00:05
        ),
    ]
    voice_items = [
        VoiceItem(
            character_name="ずんだもん",
            serif="AE2の自動クラフト設定ができたのだ！",
            frame=0,
            length=seconds_to_frames(3.5, FPS),
            layer=2,
            voice_length=format_ymm4_timecode(3.5),
        ),
        VoiceItem(
            character_name="ずんだもん",
            serif="次は鉱石の自動精錬だ！",
            frame=seconds_to_frames(3.5, FPS),
            length=seconds_to_frames(2.0, FPS),
            layer=2,
            voice_length=format_ymm4_timecode(2.0),
        ),
    ]
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
        audio_hz=48000,
        timeline_name="メイン",
        video_items=video_items,
        voice_items=voice_items,
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


def test_ymm4_timecode() -> None:
    """YMM4 の ContentOffset 形式（HH:MM:SS.fffffff）の変換を検証する。"""
    assert format_ymm4_timecode(3.5) == "00:00:03.5000000"
    assert format_ymm4_timecode(720.0) == "00:12:00.0000000"
    assert parse_ymm4_timecode("00:00:03.5000000") == 3.5
    assert parse_ymm4_timecode("00:12:00.0000000") == 720.0


# ---------------------------------------------------------------------------
# core/ir.py のテスト
# ---------------------------------------------------------------------------


def test_ir_items() -> None:
    """IR の VideoItem / VoiceItem の内容を検証する。"""
    project = _build_sample_project()
    assert len(project.video_items) == 2
    assert len(project.voice_items) == 2
    assert project.video_items[0].length == 105
    assert project.voice_items[0].length == 105
    assert project.voice_items[0].character_name == "ずんだもん"
    assert project.voice_items[0].serif == "AE2の自動クラフト設定ができたのだ！"


# ---------------------------------------------------------------------------
# exporter/ymm4_exporter.py のテスト
# ---------------------------------------------------------------------------


def test_build_ymm4_dict_structure() -> None:
    """.ymmp 辞書の構造（トップレベルキー・タイムライン・アイテム）を検証する。"""
    project = _build_sample_project()
    data = build_ymm4_dict(project, "sample.ymmp")

    # トップレベルキー（sample の .ymmp と一致）
    assert set(data.keys()) == {
        "FilePath",
        "SelectedTimelineIndex",
        "Timelines",
        "Characters",
        "CollapsedGroups",
        "LayoutXml",
        "ToolStates",
    }
    assert data["FilePath"] == "sample.ymmp"
    assert data["SelectedTimelineIndex"] == 0

    # タイムライン
    timeline = data["Timelines"][0]
    assert timeline["Name"] == "メイン"
    assert timeline["VideoInfo"] == {
        "FPS": 30,
        "Hz": 48000,
        "Width": 1920,
        "Height": 1080,
    }
    assert timeline["Length"] == 165  # 5.5 秒 * 30fps
    assert timeline["MaxLayer"] == 2
    assert timeline["LayerSettings"] == {"Items": []}

    # アイテム（Frame 昇順で 4 個）
    items = timeline["Items"]
    assert len(items) == 4
    video_items = [it for it in items if "VideoItem" in it["$type"]]
    voice_items = [it for it in items if "VoiceItem" in it["$type"]]
    assert len(video_items) == 2
    assert len(voice_items) == 2

    # VideoItem のキー検証
    first_video = video_items[0]
    assert first_video["FilePath"] == "video1.mp4"
    assert first_video["Frame"] == 0
    assert first_video["Length"] == 105
    assert first_video["ContentOffset"] == "00:12:00.0000000"
    assert first_video["Layer"] == 0
    assert first_video["PlaybackRate"] == 100.0

    # VoiceItem のキー検証
    first_voice = voice_items[0]
    assert first_voice["CharacterName"] == "ずんだもん"
    assert first_voice["Serif"] == "AE2の自動クラフト設定ができたのだ！"
    assert first_voice["Frame"] == 0
    assert first_voice["Length"] == 105
    assert first_voice["VoiceLength"] == "00:00:03.5000000"
    assert first_voice["Layer"] == 2
    assert first_voice["JimakuVisibility"] == "UseCharacterSetting"

    # Characters
    characters = data["Characters"]
    assert len(characters) == 1
    assert characters[0]["Name"] == "ずんだもん"
    assert characters[0]["GroupName"] == "VOICEVOX"


def test_export_ymm4(tmp_path: Path) -> None:
    """.ymmp ファイルが出力され、JSON としてパース可能（構文エラーなし）であることを確認する。"""
    project = _build_sample_project()
    output_path = str(tmp_path / "sample.ymmp")
    result = export_ymm4(project, output_path)

    assert result == output_path
    assert os.path.exists(output_path)
    with open(output_path, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    assert data["Timelines"][0]["Length"] == 165
    assert len(data["Timelines"][0]["Items"]) == 4


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

    ymm4_path = export_ymm4(project, str(OUTPUT_DIR / "sample.ymmp"))
    json_path = export_ymm4_json(project, str(OUTPUT_DIR / "script.json"))
    csv_path = export_ymm4_csv(project, str(OUTPUT_DIR / "script.csv"))

    assert os.path.exists(ymm4_path)
    assert os.path.exists(json_path)
    assert os.path.exists(csv_path)


if __name__ == "__main__":
    # pytest を使わず直接実行した場合も成果物を生成できるようにする
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    project = _build_sample_project()
    print("YMMP:", export_ymm4(project, str(OUTPUT_DIR / "sample.ymmp")))
    print("JSON:", export_ymm4_json(project, str(OUTPUT_DIR / "script.json")))
    print("CSV :", export_ymm4_csv(project, str(OUTPUT_DIR / "script.csv")))