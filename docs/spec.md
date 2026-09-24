# Minecraft実況動画編集 自動化ツール 設計書

## 1. システム概要
本システムは、Minecraftのプレイ動画（複数可）と見どころのメモを入力とし、LLMによるセリフ自動生成を経て、以下の成果物を出力するツールである。

1. **YMM4用プロジェクトファイル（.ymmp）**: セリフ長に合わせてカット・トリミング配置された映像アイテム（VideoItem）と、セリフごとにセリフ長に合わせた長さを持つ音声アイテム（VoiceItem）を配置した、YMM4が直接読み込めるプロジェクトファイル。
2. **YMM4用台本ファイル**: YMM4のプロジェクトや音声・字幕インポートに利用可能な構造化台本データ（JSON/CSV）。

> 旧仕様では AviUtl 拡張編集（.exo）を出力対象としていたが、仕様変更により **YMM4（.ymmp）直接生成** へ移行した。

将来的な拡張性を見据え、中間に抽象化されたタイムライン・セリフデータモデル（IR）を挟むアーキテクチャとする。

## 2. アプリケーションアーキテクチャ

### 2.1. UI・設定層 (Streamlit)
* **設定管理**:
  * 利用するLLMプロバイダ（OpenRouter / Gemini等）の選択とAPIキー設定（環境変数またはセキュアなローカル保存）。
  * 編集フレームレート設定（例: 30fps または 60fps）。
  * 音声・セリフ長計算の目安文字数/秒数設定。
* **入力フォーム**:
  * キャラクターの性格付け・セリフ生成用プロンプト。
  * 動画ごとの入力ブロックを動的に追加できるUI。
  * 各動画ブロック内で「動画ファイルの指定」と、**構造化されたハイライト入力（`st.data_editor` 利用、「開始時間」「終了時間」「出来事」の列を持つ表形式）** を提供する。

### 2.2. LLM解析・生成層
* 構造化された入力メモとプロンプトをもとにLLM APIを呼び出し、セリフデータおよび時間アラインメント用メタデータを生成。
* 出力JSON仕様:
  ```json
  {
    "scenes": [
      {
        "sourceVideoPath": "video1.mp4",
        "highlightStart": "12:00",
        "highlightEnd": "14:30",
        "script": [
          { "character": "ずんだもん", "text": "AE2の自動クラフト設定ができたのだ！", "estimatedDurationSec": 3.5 }
        ]
      }
    ]
  }
  ```

### 2.3. 中間データモデル層 (IR: Intermediate Representation)
* 動画フレーム（YMM4換算）および台本を抽象化したデータ構造。
* Project: 全体コンテナ（fps、解像度、音声Hz、タイムライン名等保持）。
* VideoItem: YMM4 の映像アイテム（ファイルパス、開始フレーム、長さ、レイヤー、ContentOffset 等）。
* VoiceItem: YMM4 の音声アイテム（キャラクター名、セリフ、開始フレーム、長さ、レイヤー、字幕設定等）。
* DialogueScript: YMM4インポート用に対話・キャラクター・尺をまとめた構造体。

### 2.4. エクスポート層 (Export Layer)
* ymm4_exporter.py:
  * IR（VideoItem / VoiceItem）から YMM4 プロジェクト（.ymmp）の JSON 構造を直接構築・出力。
  * `samples/` の参考 .ymmp 構造（トップレベルキー、Timelines、VideoItem / VoiceItem / Characters のキー構成）に準拠。
  * タイムライン上の配置順（Frame 昇順）でアイテムをソートし、`Length` / `MaxLayer` を自動計算。

* ymm4_script_exporter.py:
  * YMM4側でインポート・参照可能なJSON/CSV形式の台本ファイルを出力。

## 3. YMM4 .ymmp 出力仕様

### 3.1. トップレベル構造
```json
{
  "FilePath": "出力先 .ymmp の絶対パス",
  "SelectedTimelineIndex": 0,
  "Timelines": [ { "ID": "GUID", "Name": "メイン", "VideoInfo": {...}, "VerticalLine": {...}, "Items": [...], "LayerSettings": {"Items": []}, "CurrentFrame": 0, "Length": 165, "MaxLayer": 2 } ],
  "Characters": [ { "Name": "ずんだもん", "GroupName": "VOICEVOX", "Color": "#FF00A103", "Layer": 2, "KeyGesture": {...}, "Voice": {"API": "voicevox", "Arg": ""}, "Volume": {...}, "Pan": {...}, "PlaybackRate": 100.0, "VoiceParameter": null } ],
  "CollapsedGroups": [],
  "LayoutXml": "",
  "ToolStates": {}
}
```

### 3.2. VideoInfo
```json
{ "FPS": 30, "Hz": 48000, "Width": 1920, "Height": 1080 }
```

### 3.3. VideoItem（映像アイテム）
主要キー:
- `$type`: `"YukkuriMovieMaker.Project.Items.VideoItem, YukkuriMovieMaker"`
- `FilePath`: 元動画ファイルのパス
- `Frame`: タイムライン上の開始フレーム
- `Length`: アイテム長（フレーム）
- `Layer`: 配置レイヤー番号
- `ContentOffset`: 動画内の再生開始位置（`"HH:MM:SS.fffffff"` 形式）
- `Volume` / `Pan` / `PlaybackRate`: 音量・定位・再生速度
- `IsLooped`: ループ再生フラグ
- `AudioTrackIndex`: 使用音声トラック番号

### 3.4. VoiceItem（音声アイテム）
主要キー:
- `$type`: `"YukkuriMovieMaker.Project.Items.VoiceItem, YukkuriMovieMaker"`
- `CharacterName`: キャラクター名
- `Serif`: セリフ本文
- `Frame`: タイムライン上の開始フレーム
- `Length`: アイテム長（フレーム、セリフ長に一致）
- `Layer`: 配置レイヤー番号
- `VoiceLength`: 音声の長さ（`"HH:MM:SS.fffffff"` 形式）
- `ContentOffset`: 音声内の再生開始位置
- `Volume` / `Pan` / `PlaybackRate`: 音量・定位・再生速度
- `JimakuVisibility`: 字幕表示設定（例: `"UseCharacterSetting"`）
- `Font` / `FontSize` / `FontColor` / `BasePoint`: 字幕のフォント・色・基準点

### 3.5. アニメーション構造（Volume / Pan / FontSize 等）
```json
{
  "Values": [ { "Value": 100.0 } ],
  "Span": 0.0,
  "AnimationType": "なし",
  "Bezier": {
    "Points": [
      { "Point": {"X": 0.0, "Y": 0.0}, "ControlPoint1": {"X": -0.3, "Y": -0.3}, "ControlPoint2": {"X": 0.3, "Y": 0.3} },
      { "Point": {"X": 1.0, "Y": 1.0}, "ControlPoint1": {"X": -0.3, "Y": -0.3}, "ControlPoint2": {"X": 0.3, "Y": 0.3} }
    ],
    "IsQuadratic": false
  }
}
```

### 3.6. タイムコード形式
- IR 内: 秒数（int/float）または `"MM:SS"` 形式
- .ymmp 内: `"HH:MM:SS.fffffff"` 形式（`core/time_utils.py` の `format_ymm4_timecode` / `parse_ymm4_timecode` で相互変換）

## 4. 開発フェーズ
* Phase 1: IRモデルの定義、ハードコードされた仮データから「カット済み動画＋セリフ音声」の .ymmp を直接出力するコア、およびYMM4向け台本ファイル出力コアの実装。
* Phase 2: StreamlitによるUI構築（構造化データ入力フォーム含む）とLLM API連携の実装。
* Phase 3: 複数ファイル対応のIR構築・タイムライン/尺計算ロジックの完成と、全体パイプラインの結合。

## 5. 技術スタック
* 言語: Python 3.10+
* UIフレームワーク: Streamlit
* LLM API: openai / google-generativeai 等
* 映像/データ処理: 標準ライブラリ ＋ 必要に応じ数学・フレーム換算ユーティリティ