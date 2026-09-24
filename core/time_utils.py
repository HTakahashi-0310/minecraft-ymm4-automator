"""タイムコード・秒数・フレーム数換算ヘルパー。

IR 内のタイムコードは「秒数 (int/float)」または「MM:SS 形式の文字列」を
明示的にサポートし、fps 基準でフレーム数へ変換するためのユーティリティを提供する。

対応形式:
- 秒数: ``int`` / ``float``
- タイムコード: ``"MM:SS"`` / ``"MM:SS.mmm"`` / ``"HH:MM:SS"``
- YMM4 の ContentOffset 形式: ``"HH:MM:SS.fffffff"``（:func:`format_ymm4_timecode` / :func:`parse_ymm4_timecode`）
"""

from __future__ import annotations

import re
from typing import Union

# タイムコードの正規表現: "MM:SS" / "MM:SS.mmm" / "HH:MM:SS" 形式
_TIME_CODE_RE = re.compile(
    r"^(?:(?P<hours>\d+):)?(?P<minutes>\d{1,2}):(?P<seconds>\d{1,2}(?:\.\d+)?)$"
)

# IR 内でタイムコードとして許容する型（秒数 or "MM:SS" 文字列）
TimeCode = Union[int, float, str]


def parse_timecode(value: TimeCode) -> float:
    """タイムコードを秒数 (float) に変換する。

    Args:
        value: 秒数 (int/float) または ``"MM:SS"`` / ``"HH:MM:SS"`` 形式の文字列。

    Returns:
        秒数 (float)。

    Raises:
        ValueError: パースできない形式の場合。
    """
    if isinstance(value, (int, float)):
        return float(value)
    if not isinstance(value, str):
        raise ValueError(f"Unsupported timecode type: {type(value)!r}")

    text = value.strip()
    match = _TIME_CODE_RE.match(text)
    if not match:
        raise ValueError(
            f"Invalid timecode format: {value!r} (expected 'MM:SS' or seconds)"
        )

    hours = int(match.group("hours") or 0)
    minutes = int(match.group("minutes"))
    seconds = float(match.group("seconds"))
    return hours * 3600.0 + minutes * 60.0 + seconds


def seconds_to_frames(seconds: float, fps: float) -> int:
    """秒数をフレーム数に変換する（四捨五入）。

    Args:
        seconds: 秒数。
        fps: フレームレート（例: 30.0）。

    Returns:
        フレーム数 (int)。

    Raises:
        ValueError: fps が 0 以下の場合。
    """
    if fps <= 0:
        raise ValueError(f"fps must be positive, got {fps}")
    return int(round(seconds * fps))


def frames_to_seconds(frames: int, fps: float) -> float:
    """フレーム数を秒数に変換する。

    Args:
        frames: フレーム数。
        fps: フレームレート（例: 30.0）。

    Returns:
        秒数 (float)。

    Raises:
        ValueError: fps が 0 以下の場合。
    """
    if fps <= 0:
        raise ValueError(f"fps must be positive, got {fps}")
    return frames / fps


def format_timecode(seconds: float) -> str:
    """秒数を ``"MM:SS"`` 形式のタイムコード文字列に変換する。

    Args:
        seconds: 秒数。

    Returns:
        ``"MM:SS"`` 形式の文字列（例: ``"01:30"``）。
    """
    total = int(round(seconds))
    minutes, secs = divmod(total, 60)
    return f"{minutes:02d}:{secs:02d}"


def format_ymm4_timecode(seconds: float) -> str:
    """秒数を YMM4 の ContentOffset 形式 ``"HH:MM:SS.fffffff"`` に変換する。

    YMM4 の VideoItem / VoiceItem が保持する ``ContentOffset`` / ``VoiceLength``
    は ``"HH:MM:SS.fffffff"``（時:分:秒.小数部7桁）形式である。
    小数部は秒の小数を7桁で表す（例: 0.5 秒 → ``"5000000"``）。

    Args:
        seconds: 秒数。

    Returns:
        ``"HH:MM:SS.fffffff"`` 形式の文字列（例: ``"00:00:03.5000000"``）。
    """
    total_seconds = int(seconds)
    fraction = int(round((seconds - total_seconds) * 10_000_000))
    # 丸め誤差で小数部が 1.0 相当になった場合の補正
    if fraction >= 10_000_000:
        total_seconds += 1
        fraction -= 10_000_000
    hours, rem = divmod(total_seconds, 3600)
    minutes, secs = divmod(rem, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{fraction:07d}"


def parse_ymm4_timecode(value: str) -> float:
    """YMM4 の ContentOffset 形式 ``"HH:MM:SS.fffffff"`` を秒数に変換する。

    Args:
        value: ``"HH:MM:SS.fffffff"`` 形式の文字列。

    Returns:
        秒数 (float)。

    Raises:
        ValueError: パースできない形式の場合。
    """
    match = _TIME_CODE_RE.match(value.strip())
    if not match:
        raise ValueError(f"Invalid YMM4 timecode format: {value!r}")
    hours = int(match.group("hours") or 0)
    minutes = int(match.group("minutes"))
    seconds = float(match.group("seconds"))
    return hours * 3600.0 + minutes * 60.0 + seconds