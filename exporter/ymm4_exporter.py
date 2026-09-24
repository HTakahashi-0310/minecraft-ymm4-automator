"""YMM4 プロジェクト（.ymmp）直接生成エクスポーター。

IR（:mod:`core.ir`）のタイムライン情報（VideoItem / VoiceItem）から、
YMM4 が読み込める .ymmp（JSON）を直接生成する。

出力方針:
- タイムラインには「編集のベースとなる動画アイテム」と
  「キャラクター設定に従って生成された音声＋字幕アイテム」のみを配置する。
- YMM4 は省略されたプロパティに対してデフォルト値を自動適用するため、
  装飾・アニメーション系のプロパティ（座標アニメーション、Bezier、
  DisplayDirection、HideDirection、Font 関連等）は出力しない。
"""

from __future__ import annotations

import json
import uuid
from typing import Dict, List

from core.ir import Project, VideoItem, VoiceItem

# YMM4 のアイテム型識別子
_TYPE_VIDEO_ITEM = "YukkuriMovieMaker.Project.Items.VideoItem, YukkuriMovieMaker"
_TYPE_VOICE_ITEM = "YukkuriMovieMaker.Project.Items.VoiceItem, YukkuriMovieMaker"
_TYPE_VERTICAL_BPM_LINE = (
    "YukkuriMovieMaker.Project.VerticalBPMLine, YukkuriMovieMaker.Plugin"
)


def _build_video_item(item: VideoItem) -> Dict[str, object]:
    """VideoItem を .ymmp のアイテム辞書に変換する。

    配置と再生に必要な最低限のプロパティのみを出力する。
    """
    return {
        "$type": _TYPE_VIDEO_ITEM,
        "FilePath": item.file_path,
        "Layer": item.layer,
        "Frame": item.frame,
        "Length": item.length,
        "ContentOffset": item.content_offset,
    }


def _build_voice_item(item: VoiceItem) -> Dict[str, object]:
    """VoiceItem を .ymmp のアイテム辞書に変換する。

    配置と再生に必要な最低限のプロパティのみを出力する。
    """
    return {
        "$type": _TYPE_VOICE_ITEM,
        "CharacterName": item.character_name,
        "Serif": item.serif,
        "VoiceLength": item.voice_length,
        "Layer": item.layer,
        "Frame": item.frame,
        "Length": item.length,
    }


def _character_color(name: str) -> str:
    """キャラクター名から字幕色（``#AARRGGBB``）を決定的に生成する。"""
    rgb = sum(ord(c) for c in name) % 0xFFFFFF
    return f"#FF{rgb:06X}"


def _build_characters(project: Project) -> List[Dict[str, object]]:
    """VoiceItem のキャラクター名から Characters 配列を生成する。

    キャラクター設定（音声合成 API 等）に必要な最低限のプロパティのみを出力する。
    """
    characters: List[Dict[str, object]] = []
    seen: set[str] = set()
    for item in project.voice_items:
        if item.character_name in seen:
            continue
        seen.add(item.character_name)
        characters.append(
            {
                "Name": item.character_name,
                "GroupName": "VOICEVOX",
                "Color": _character_color(item.character_name),
                "Layer": item.layer,
                "Voice": {"API": "voicevox", "Arg": ""},
            }
        )
    return characters


def _compute_total_length(project: Project) -> int:
    """タイムライン全体の長さ（フレーム）を計算する。"""
    end_frames: List[int] = []
    end_frames.extend(item.frame + item.length for item in project.video_items)
    end_frames.extend(item.frame + item.length for item in project.voice_items)
    return max(end_frames) if end_frames else 0


def _compute_max_layer(project: Project) -> int:
    """タイムライン上の最大レイヤー番号を計算する。"""
    layers: List[int] = []
    layers.extend(item.layer for item in project.video_items)
    layers.extend(item.layer for item in project.voice_items)
    return max(layers) if layers else 0


def build_ymm4_dict(project: Project, file_path: str) -> Dict[str, object]:
    """Project から .ymmp の辞書構造を構築する。

    Args:
        project: 出力対象の Project。
        file_path: プロジェクトファイルパス（``FilePath`` に記録）。

    Returns:
        .ymmp の辞書構造。
    """
    # タイムライン上の配置順（Frame 昇順）でアイテムを並べる
    items: List[Dict[str, object]] = []
    items.extend(_build_video_item(item) for item in project.video_items)
    items.extend(_build_voice_item(item) for item in project.voice_items)
    items.sort(key=lambda it: int(it["Frame"]))

    timeline: Dict[str, object] = {
        "ID": str(uuid.uuid4()),
        "Name": project.timeline_name,
        "VideoInfo": {
            "FPS": int(round(project.fps)),
            "Hz": project.audio_hz,
            "Width": project.width,
            "Height": project.height,
        },
        "VerticalLine": {
            "IsEnabled": False,
            "StartFrame": 0,
            "LineType": "BPM",
            "Line": {"$type": _TYPE_VERTICAL_BPM_LINE, "BPM": 100.0},
            "Group": 4,
        },
        "Items": items,
        "LayerSettings": {"Items": []},
        "CurrentFrame": 0,
        "Length": _compute_total_length(project),
        "MaxLayer": _compute_max_layer(project),
    }

    return {
        "FilePath": file_path,
        "SelectedTimelineIndex": 0,
        "Timelines": [timeline],
        "Characters": _build_characters(project),
        "CollapsedGroups": [],
        "LayoutXml": "",
        "ToolStates": {},
    }


def export_ymm4(project: Project, output_path: str) -> str:
    """Project を YMM4 プロジェクト（.ymmp）ファイルとして出力する。

    YMM4 の実ファイルと同様に UTF-8 BOM 付きで書き出す。

    Args:
        project: 出力対象の Project。
        output_path: 出力先ファイルパス。

    Returns:
        出力先ファイルパス。
    """
    data = build_ymm4_dict(project, output_path)
    with open(output_path, "w", encoding="utf-8-sig") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return output_path