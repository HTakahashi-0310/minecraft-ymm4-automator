"""中間データモデル層 (IR: Intermediate Representation)。

Minecraft実況動画編集ツールの中間データモデルを定義する。
YMM4 のプロジェクト（.ymmp）へ直接変換するための共通データ構造として、
映像アイテム（VideoItem）・音声アイテム（VoiceItem）・台本（DialogueScript）を
抽象化する。

タイムコードは「秒数 (int/float)」または「MM:SS 形式の文字列」を
明示的にサポートする（:mod:`core.time_utils` の ``TimeCode`` 型）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from core.time_utils import TimeCode


@dataclass
class VideoItem:
    """YMM4 の映像アイテム（VideoItem）1つ分の情報。

    配置と再生に必要な最低限のプロパティのみを保持する。
    装飾・アニメーション系のプロパティは YMM4 がデフォルト値を適用するため
    データモデルに含めない。

    Attributes:
        file_path: 元動画ファイルのパス。
        frame: タイムライン上の開始フレーム。
        length: アイテム長（フレーム）。
        layer: 配置レイヤー番号。
        content_offset: 動画内の再生開始位置（``"HH:MM:SS.fffffff"`` 形式）。
    """

    file_path: str
    frame: int
    length: int
    layer: int = 0
    content_offset: str = "00:00:00"


@dataclass
class VoiceItem:
    """YMM4 の音声アイテム（VoiceItem）1つ分の情報。

    セリフ長（``length``）は対応する音声の長さに一致させる。
    配置と再生に必要な最低限のプロパティのみを保持する。

    Attributes:
        character_name: キャラクター名。
        serif: セリフ本文。
        frame: タイムライン上の開始フレーム。
        length: アイテム長（フレーム）。
        layer: 配置レイヤー番号。
        voice_length: 音声の長さ（``"HH:MM:SS.fffffff"`` 形式）。
    """

    character_name: str
    serif: str
    frame: int
    length: int
    layer: int = 2
    voice_length: str = "00:00:00"


@dataclass
class DialogueLine:
    """台本の1行（セリフ）。

    Attributes:
        character: キャラクター名。
        text: セリフ本文。
        estimated_duration_sec: 推定セリフ長（秒）。
        source_video_path: 対応する元動画パス（任意）。
        highlight_start: 対応するハイライト開始位置（任意）。
        highlight_end: 対応するハイライト終了位置（任意）。
    """

    character: str
    text: str
    estimated_duration_sec: float
    source_video_path: Optional[str] = None
    highlight_start: Optional[TimeCode] = None
    highlight_end: Optional[TimeCode] = None


@dataclass
class DialogueScript:
    """YMM4インポート用に対話・キャラクター・尺をまとめた構造体。

    Attributes:
        title: 台本タイトル。
        lines: セリフ行のリスト。
    """

    title: str
    lines: List[DialogueLine] = field(default_factory=list)


@dataclass
class Project:
    """全体コンテナ（YMM4 プロジェクト相当）。

    Attributes:
        name: プロジェクト名。
        fps: フレームレート（例: 30.0）。
        width: 出力解像度の幅。
        height: 出力解像度の高さ。
        audio_hz: 音声サンプリングレート（Hz）。
        timeline_name: タイムライン名。
        video_items: 映像アイテムのリスト。
        voice_items: 音声アイテムのリスト。
        script: 台本データ。
    """

    name: str
    fps: float = 30.0
    width: int = 1920
    height: int = 1080
    audio_hz: int = 48000
    timeline_name: str = "メイン"
    video_items: List[VideoItem] = field(default_factory=list)
    voice_items: List[VoiceItem] = field(default_factory=list)
    script: DialogueScript = field(default_factory=DialogueScript)