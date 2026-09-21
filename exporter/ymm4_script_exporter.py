"""YMM4インポート用台本ファイルの出力。

IR（:mod:`core.ir`）の台本データ（:class:`~core.ir.DialogueScript`）を、
YMM4側で取り込みやすい以下の形式で出力する。

- JSON: 構造化データとしてそのまま利用可能（``export_ymm4_json``）
- CSV: 表計算ソフト等で編集しやすい形式（``export_ymm4_csv``）
"""

from __future__ import annotations

import csv
import json
from typing import Dict, List

from core.ir import DialogueLine, DialogueScript, Project

# CSV の列定義（YMM4側で参照しやすいよう設計書の JSON キーと対応させる）
_CSV_FIELDNAMES: List[str] = [
    "character",
    "text",
    "estimated_duration_sec",
    "source_video_path",
    "highlight_start",
    "highlight_end",
]


def _line_to_dict(line: DialogueLine) -> Dict[str, object]:
    """DialogueLine を YMM4 向け JSON 辞書に変換する。"""
    return {
        "character": line.character,
        "text": line.text,
        "estimatedDurationSec": line.estimated_duration_sec,
        "sourceVideoPath": line.source_video_path,
        "highlightStart": line.highlight_start,
        "highlightEnd": line.highlight_end,
    }


def to_json_dict(script: DialogueScript, fps: float) -> Dict[str, object]:
    """DialogueScript を YMM4 向け JSON 辞書に変換する。

    Args:
        script: 変換対象の台本。
        fps: プロジェクトのフレームレート（メタ情報として付与）。

    Returns:
        YMM4 向け JSON 辞書。
    """
    return {
        "title": script.title,
        "fps": fps,
        "lines": [_line_to_dict(line) for line in script.lines],
    }


def export_ymm4_json(project: Project, output_path: str) -> str:
    """Project の台本を YMM4 向け JSON ファイルとして出力する。

    Args:
        project: 出力対象の Project。
        output_path: 出力先ファイルパス。

    Returns:
        出力先ファイルパス。
    """
    data = to_json_dict(project.script, project.fps)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return output_path


def export_ymm4_csv(project: Project, output_path: str) -> str:
    """Project の台本を YMM4 向け CSV ファイルとして出力する。

    Excel 等での文字化けを防ぐため UTF-8 BOM 付きで書き出す。

    Args:
        project: 出力対象の Project。
        output_path: 出力先ファイルパス。

    Returns:
        出力先ファイルパス。
    """
    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=_CSV_FIELDNAMES)
        writer.writeheader()
        for line in project.script.lines:
            writer.writerow(
                {
                    "character": line.character,
                    "text": line.text,
                    "estimated_duration_sec": line.estimated_duration_sec,
                    "source_video_path": line.source_video_path or "",
                    "highlight_start": line.highlight_start or "",
                    "highlight_end": line.highlight_end or "",
                }
            )
    return output_path