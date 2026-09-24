"""YMM4 プロジェクト（.ymmp）直接生成エクスポーター。

IR（:mod:`core.ir`）のタイムライン情報（VideoItem / VoiceItem）から、
YMM4 が読み込める .ymmp（JSON）を直接生成する。

``samples/`` の参考 .ymmp 構造（トップレベルキー・タイムライン・
VideoItem / VoiceItem / Characters のキー構成）に準拠する。
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


def _animation(value: float) -> Dict[str, object]:
    """YMM4 のアニメーション構造（Values/Span/AnimationType/Bezier）を生成する。"""
    return {
        "Values": [{"Value": value}],
        "Span": 0.0,
        "AnimationType": "なし",
        "Bezier": {
            "Points": [
                {
                    "Point": {"X": 0.0, "Y": 0.0},
                    "ControlPoint1": {"X": -0.3, "Y": -0.3},
                    "ControlPoint2": {"X": 0.3, "Y": 0.3},
                },
                {
                    "Point": {"X": 1.0, "Y": 1.0},
                    "ControlPoint1": {"X": -0.3, "Y": -0.3},
                    "ControlPoint2": {"X": 0.3, "Y": 0.3},
                },
            ],
            "IsQuadratic": False,
        },
    }


def _key_frames() -> Dict[str, object]:
    """空のキーフレーム構造を生成する。"""
    return {"Frames": [], "Count": 0}


def _build_video_item(item: VideoItem) -> Dict[str, object]:
    """VideoItem を .ymmp のアイテム辞書に変換する。"""
    return {
        "$type": _TYPE_VIDEO_ITEM,
        "IsWaveformEnabled": False,
        "FilePath": item.file_path,
        "AudioTrackIndex": item.audio_track_index,
        "Volume": _animation(item.volume),
        "Pan": _animation(0.0),
        "PlaybackRate": item.playback_rate,
        "ContentOffset": item.content_offset,
        "IsLooped": item.is_looped,
        "EchoIsEnabled": False,
        "EchoInterval": 0.0,
        "EchoAttenuation": 0.0,
        "AudioEffects": [],
        "X": _animation(0.0),
        "Y": _animation(0.0),
        "Z": _animation(0.0),
        "Opacity": _animation(100.0),
        "Zoom": _animation(100.0),
        "Rotation": _animation(0.0),
        "FadeIn": 0.0,
        "FadeOut": 0.0,
        "Blend": "Normal",
        "IsInverted": False,
        "IsClippingWithObjectAbove": False,
        "IsAlwaysOnTop": False,
        "IsZOrderEnabled": False,
        "VideoEffects": [],
        "Group": 0,
        "Frame": item.frame,
        "Layer": item.layer,
        "KeyFrames": _key_frames(),
        "Length": item.length,
        "Remark": "",
        "IsLocked": False,
        "IsHidden": False,
    }


def _build_voice_item(item: VoiceItem) -> Dict[str, object]:
    """VoiceItem を .ymmp のアイテム辞書に変換する。"""
    return {
        "$type": _TYPE_VOICE_ITEM,
        "IsWaveformEnabled": False,
        "CharacterName": item.character_name,
        "Serif": item.serif,
        "Decorations": [],
        "Hatsuon": "",
        "Pronounce": None,
        "VoiceLength": item.voice_length,
        "VoiceCache": None,
        "Volume": _animation(item.volume),
        "Pan": _animation(0.0),
        "PlaybackRate": item.playback_rate,
        "VoiceParameter": None,
        "ContentOffset": item.content_offset,
        "VoiceFadeIn": 0.0,
        "VoiceFadeOut": 0.0,
        "EchoIsEnabled": False,
        "EchoInterval": 0.0,
        "EchoAttenuation": 0.0,
        "AudioEffects": [],
        "JimakuVisibility": item.jimaku_visibility,
        "Y": _animation(0.0),
        "X": _animation(0.0),
        "Z": _animation(0.0),
        "Opacity": _animation(100.0),
        "Zoom": _animation(100.0),
        "Rotation": _animation(0.0),
        "JimakuFadeIn": 0.0,
        "JimakuFadeOut": 0.0,
        "Blend": "Normal",
        "IsInverted": False,
        "IsClippingWithObjectAbove": False,
        "IsAlwaysOnTop": False,
        "IsZOrderEnabled": False,
        "Font": item.font,
        "FontSize": _animation(item.font_size),
        "LineHeight2": 0.0,
        "LetterSpacing2": 0.0,
        "MaxWidth": 0.0,
        "BasePoint": item.base_point,
        "FontColor": item.font_color,
        "Style": "Normal",
        "StyleColor": "#FF000000",
        "Bold": False,
        "Italic": False,
        "IsTrimEndSpace": True,
        "IsDevidedPerCharacter": False,
        "DisplayInterval": 0.0,
        "DisplayDirection": "LeftToRight",
        "HideInterval": 0.0,
        "HideDirection": "LeftToRight",
        "JimakuVideoEffects": [],
        "TachieFaceParameter": None,
        "TachieFaceEffects": [],
        "Group": 0,
        "Frame": item.frame,
        "Layer": item.layer,
        "KeyFrames": _key_frames(),
        "Length": item.length,
        "Remark": "",
        "IsLocked": False,
        "IsHidden": False,
    }


def _character_color(name: str) -> str:
    """キャラクター名から字幕色（``#AARRGGBB``）を決定的に生成する。"""
    rgb = sum(ord(c) for c in name) % 0xFFFFFF
    return f"#FF{rgb:06X}"


def _build_characters(project: Project) -> List[Dict[str, object]]:
    """VoiceItem のキャラクター名から Characters 配列を生成する。"""
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
                "KeyGesture": {"Key": 0, "Modifiers": 2},
                "Voice": {"API": "voicevox", "Arg": ""},
                "Volume": _animation(item.volume),
                "Pan": _animation(0.0),
                "PlaybackRate": item.playback_rate,
                "VoiceParameter": None,
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