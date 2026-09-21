"""AviUtl拡張編集 .exo 形式のテキスト生成・出力。

IR（:mod:`core.ir`）のタイムライン情報から、AviUtl拡張編集が読み込める
INI風の .exo テキストを構築する。

出力構造:
- ``[exedit]``: プロジェクト全体設定（解像度・fps・長さ等）
- ``[0]`` / ``[0.0]``: 映像オブジェクト（カット・トリミング済みクリップ）
- ``[1]`` / ``[1.0]``: テキストオブジェクト（セリフ長に一致する仮オブジェクト）
"""

from __future__ import annotations

from typing import List

from core.ir import PlaceholderObject, Project, VideoClip


def _format_exedit_section(project: Project, total_frames: int) -> List[str]:
    """``[exedit]`` セクションを生成する。"""
    return [
        "[exedit]",
        f"width={project.width}",
        f"height={project.height}",
        f"rate={int(round(project.fps))}",
        "scale=1",
        f"length={total_frames}",
        "audio_rate=44100",
        "audio_ch=2",
    ]


def _format_video_clip(clip: VideoClip, index: int) -> List[str]:
    """映像クリップ1つ分の ``[N]`` / ``[N.0]`` セクションを生成する。

    AviUtl拡張編集の映像オブジェクトは「再生位置」をミリ秒単位で保持するため、
    ソース開始位置（秒）をミリ秒へ換算して出力する。
    """
    source_start_ms = int(round(clip.source_start_sec * 1000))
    return [
        f"[{index}]",
        f"start={clip.timeline_start}",
        f"end={clip.timeline_end}",
        "layer=0",
        "overlay=0",
        "camera=0",
        "color=0",
        "clip=0",
        "mix=0",
        "name=動画",
        f"[{index}.0]",
        f"再生位置={source_start_ms}",
        "再生速度=100.0",
        "ループ再生=0",
        "アルファブレンド=0",
        f"ファイル名={clip.source_path}",
    ]


def _format_placeholder_object(obj: PlaceholderObject, index: int) -> List[str]:
    """仮オブジェクト（テキスト）1つ分の ``[N]`` / ``[N.0]`` セクションを生成する。"""
    return [
        f"[{index}]",
        f"start={obj.start_frame}",
        f"end={obj.end_frame}",
        f"layer={obj.layer}",
        "overlay=0",
        "camera=0",
        "color=0",
        "clip=0",
        "mix=0",
        "name=テキスト",
        f"[{index}.0]",
        "サイズ=32",
        "表示位置=1",
        "文字色=FFFFFF",
        "縁取り色=000000",
        "縁取りサイズ=0",
        "影色=000000",
        "影サイズ=0",
        "影位置X=0",
        "影位置Y=0",
        "影透明度=0",
        "ボールド=0",
        "斜体=0",
        "下線=0",
        "打ち消し線=0",
        "標準=1",
        "文字間隔=0",
        "行間隔=0",
        "縦書き=0",
        "ルビ=0",
        "ルビサイズ=0",
        "ルビ位置=0",
        "ルビ文字間隔=0",
        "ルビ行間隔=0",
        f"テキスト={obj.text}",
    ]


def _compute_total_frames(project: Project) -> int:
    """タイムライン全体の長さ（フレーム）を計算する。

    映像クリップ・仮オブジェクトの終了フレームの最大値を返す。
    要素が無い場合は 0 を返す。
    """
    end_frames: List[int] = []
    end_frames.extend(clip.timeline_end for clip in project.video_track.clips)
    end_frames.extend(obj.end_frame for obj in project.placeholder_track.objects)
    return max(end_frames) if end_frames else 0


def build_exo_text(project: Project) -> str:
    """Project から .exo テキスト全体を構築する。

    Args:
        project: 出力対象の Project。

    Returns:
        .exo 形式のテキスト（末尾改行付き）。
    """
    total_frames = _compute_total_frames(project)
    lines: List[str] = _format_exedit_section(project, total_frames)
    lines.append("")

    index = 0
    for clip in project.video_track.clips:
        lines.extend(_format_video_clip(clip, index))
        lines.append("")
        index += 1

    for obj in project.placeholder_track.objects:
        lines.extend(_format_placeholder_object(obj, index))
        lines.append("")
        index += 1

    return "\n".join(lines) + "\n"


def export_exo(project: Project, output_path: str) -> str:
    """Project を AviUtl拡張編集 .exo ファイルとして出力する。

    Args:
        project: 出力対象の Project。
        output_path: 出力先ファイルパス。

    Returns:
        出力先ファイルパス。
    """
    content = build_exo_text(project)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    return output_path