# gosz_hand-motion-tracker

MediaPipeでピアノ演奏中の手・指の動きを解析するためのプロジェクト。
現在は、開発環境の構築とHand Landmarkerの初期化・終了を確認するための基盤を用意している。

## 使用するバージョン

- Python: 3.12.15（`.python-version` で指定）
- MediaPipe: 1.0.1（`pyproject.toml` で指定）
- uv: 0.13.0で動作確認済み

動作確認環境はWindows x86-64。

## uvの導入

uvは、Pythonの取得、プロジェクトごとの仮想環境、依存パッケージを管理するツール。
PCに一度インストールすると、複数のプロジェクトで利用できる。

Windowsでは、PowerShellで次を実行する。

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

macOS・Linuxでは、次を実行する。

```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
```

インストール後はターミナルを開き直し、次のコマンドで利用できることを確認する。

```console
uv --version
```

その他の導入方法は[uv公式のインストール手順](https://docs.astral.sh/uv/getting-started/installation/)を参照する。

## 開発環境の構築

リポジトリをまだ取得していない場合は、次を実行する。

```console
git clone https://github.com/marmotech/gosz_hand-motion-tracker.git
cd gosz_hand-motion-tracker
```

取得済みの場合は、そのリポジトリのルート（`pyproject.toml` のあるディレクトリ）に移動する。
続いて、次のコマンドでPythonを取得し、依存パッケージをインストールする。初回はインターネット接続が必要。

```console
uv python install 3.12.15
uv sync --locked
```

このディレクトリに仮想環境 `.venv/` が作成され、`uv.lock` に記録されたバージョンの依存パッケージが入る。
以降のスクリプトは `uv run --locked` で実行するため、仮想環境を手動で有効化する必要はない。

新しくworktreeを作った場合も、そのworktreeのルートで同じ2つのコマンドを実行する。
`.venv/` はworktreeごとに作成され、Gitには追跡されない。

## Hand Landmarkerモデルの取得

開発環境を構築した後、リポジトリのルートで次を実行する。

```console
uv run --locked python scripts/download_hand_landmarker.py
```

モデルは `models/hand_landmarker.task` に保存される。取得時にはインターネット接続が必要。
保存済みのファイルがチェックサムと一致する場合、ダウンロードを省略する。
再取得する場合は、上のコマンドに `--force` を付ける。

使用するモデルは、[公式Hand Landmarkerガイド](https://developers.google.com/edge/mediapipe/solutions/vision/hand_landmarker#models)で案内されているモデルのfloat16・バージョン1。
再現性のため、`latest` ではなくバージョン指定のURLを使用し、取得したファイルのSHA-256を検証する。

- 取得元: https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task
- SHA-256: `fbc2a30080c3c557093b5ddfc334698132eb341044ccee322ccf8bcf3607cde1`

モデルファイルはGitの追跡対象外とし、新しいチェックアウトやworktreeでは上記の手順で取得する。

## Hand Landmarkerの動作確認

モデルの取得後、リポジトリのルートで次を実行する。

```console
uv run --locked python scripts/check_hand_landmarker.py
```

`models/hand_landmarker.task` を読み込み、CPUでHand Landmarkerを初期化して終了する。
画像や動画の読み込み、カメラの起動、手の検出は行わない。

成功時には次の2行が表示される。MediaPipe自身のログが併せて表示される場合もある。

```text
Hand Landmarker initialized.
Hand Landmarker closed.
```

モデルがない場合は、モデルの保存先と取得コマンドを表示して終了する。
