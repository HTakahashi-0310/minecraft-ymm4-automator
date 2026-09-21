"""中間データモデル層 (IR: Intermediate Representation)。

Minecraft実況動画編集ツールの中間データモデルを定義する。
動画フレーム（AviUtl換算）と台本を抽象化し、エクスポート層が
AviUtl .exo や YMM4 台本ファイルへ変換する際の共通データ構造となる。

タイムコードは「秒数 (int/float)」または「MM:SS 形式の文字列」を
明示的にサポートする（:mod:`core.time_utils` の ``TimeCode`` 型）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from core.time_utils import TimeCode, parse_timecode


@dataclass
class VideoClip:
    """編集済み映像クリップ1つ分の情報。

    Attributes:
        source_path: 元動画ファイルのパス。
        source_start: ソース上の開始位置（秒数 or ``"MM:SS"``）。
        source_end: ソース上の終了位置（秒数 or ``"MM:SS"``）。
        timeline_start: タイムライン上の開始フレーム。
        timeline_end: タイムライン上の終了フレーム。
    """

    source_path: str
    source_start: TimeCode
    source_end: TimeCode
    timeline_start: int
    timeline_end: int

    @property
    def source_start_sec(self) -> float:
        """ソース開始位置（秒）。"""
        return parse_timecode(self.source_start)

    @property
    def source_end_sec(self) -> float:
        """ソース終了位置（秒）。"""
        return parse_timecode(self.source_end)

    @property
    def duration_frames(self) -> int:
        """タイムライン上のクリップ長（フレーム）。"""
        return self.timeline_end - self.timeline_start


@dataclass
class EditedVideoTrack:
    """セリフ長/ハイライトに基づきカット・トリミング配置された映像クリップ群。

    Attributes:
        name: トラック名。
        clips: 映像クリップのリスト。
    """

    name: str = "video"
    clips: List[VideoClip] = field(default_factory=list)


@dataclass
class PlaceholderObject:
    """セリフ区間に対応する仮オブジェクト（字幕/プレースホルダ）。

    長さ（フレーム数）は対応するセリフ長に一致させる。

    Attributes:
        text: 表示テキスト（セリフ）。
        start_frame: タイムライン上の開始フレーム。
        end_frame: タイムライン上の終了フレーム。
        layer: 配置レイヤー番号。
    """

    text: str
    start_frame: int
    end_frame: int
    layer: int = 1

    @property
    def duration_frames(self) -> int:
        """オブジェクト長（フレーム）。"""
        return self.end_frame - self.start_frame


@dataclass
class PlaceholderTrack:
    """セリフ別・区間別の仮オブジェクト群。

    Attributes:
        name: トラック名。
        objects: 仮オブジェクトのリスト。
    """

    name: str = "placeholder"
    objects: List[PlaceholderObject] = field(default_factory=list)


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
    """全体コンテナ。

    Attributes:
        name: プロジェクト名。
        fps: フレームレート（例: 30.0）。
        width: 出力解像度の幅。
        height: 出力解像度の高さ。
        video_track: 編集済み映像トラック。
        placeholder_track: 仮オブジェクトトラック。
        script: 台本データ。
    """

    name: str
    fps: float = 30.0
    width: int = 1920
    height: int = 1080
    video_track: EditedVideoTrack = field(default_factory=EditedVideoTrack)
    placeholder_track: PlaceholderTrack = field(default_factory=PlaceholderTrack)
    script: DialogueScript = field(default_factory=DialogueScript)