# gosz_hand-motion-tracker

MediaPipeでピアノ演奏中の手・指の動きを解析するためのプロジェクト。

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

## アプリの起動

開発環境を構築した後、リポジトリのルートで次を実行する。

```console
uv run --locked python src/main.py
```

アプリの入口である `src/main.py` から `src/camera.py` の `CameraCapture` を呼び出し、
カメラ映像をウィンドウに表示する。画像取得と表示は同じスレッドで順番に実行する。
映像の左上には取得時刻（`Capture timestamp`、整数ns）と、前フレームからの取得間隔
（`Frame interval`、ms）を表示する。最初のフレームの取得間隔は `N/A` とする。
取得時刻は `time.monotonic_ns()` による読み取り成功直後の時刻であり、日時やカメラの撮影時刻ではない。
現段階のアプリはカメラ映像の表示までに対応している。検出・運動計算モジュールは単独で実装済みで、カメラ表示への組み込みは #8 で行う。
モデルの取得は、現在のアプリの起動には不要。

映像ウィンドウでQまたはEscキーを押すか、ウィンドウを閉じると終了する。
ターミナルのCtrl+Cでも終了できる。終了時はカメラを解放する。

別のカメラを使う場合は、カメラ番号を指定する。

```console
uv run --locked python src/main.py --camera 1
```

カメラを開けない場合や画像取得に失敗した場合は、エラーを表示して終了コード1で終了する。
カメラを開けない場合は、他のカメラ使用アプリ、OSのカメラアクセス許可、カメラ番号を確認する。

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

## 画像からの手の検出確認

モデルの取得後、未反転のテスト画像を用意して次を実行する。

```console
uv run --locked python scripts/check_hand_detection.py data/example.jpg
```

`src/hand_detector.py` の `HandDetector` を使い、最大2つの手をCPUで検出する。
IMAGEモードで画像ごとに同期実行し、画像やカメラ映像の描画は行わない。
左右の手について、21点の座標をMediaPipe順の配列としてJSONで出力する。
座標は入力画像の左上原点、右向き+x、下向き+yの小数pxで、未検出の側は `null` になる。
MediaPipe自身のログが併せて表示される場合もある。

この確認スクリプトの `timestamp_ns` は画像読み込み直後の時刻で、写真の撮影時刻ではない。
カメラ画像を処理する際は、入力の `CapturedFrame.timestamp_ns` がそのまま結果に引き継がれる。
検出終了時は、例外が起きた場合もHand Landmarkerを解放する。

## 運動計算の動作確認

開発環境を構築した後、リポジトリのルートで実行する。カメラ・画像・モデルは不要。

```console
uv run --locked python scripts/check_motion_calculation.py
```

サンプルの全21点の座標と取得時刻を、本体の `MotionCalculator` に順番に渡す。
表には時刻（ms）、左右、入力位置（px）、速度（px/s）、加速度（px/s²）を表示する。
各ベクトルは `(x, y)`。初期表示は手首（`WRIST`）で、計算対象は全21点。
時刻・座標は動作確認用に用意した値で、実際のカメラから取得した値ではない。

既定の保持時間100msでは、左手の結果を次のように確認できる。

| 時刻（ms） | 入力位置 | 速度 | 加速度 | 確認内容 |
|---|---|---|---|---|
| 0 | `(0, 0)` | `None` | `None` | 初回 |
| 20 | `(1, -2)` | `(50, -100)` | `None` | 速度の計算開始 |
| 70 | `(6, -12)` | `(100, -200)` | `(1000, -2000)` | 異なる時間間隔での計算 |
| 90 | `None` | `None` | `None` | 未検出中の値は補完しない |
| 120 | `(11, -22)` | `(100, -200)` | `(0, 0)` | 短い欠落をまたいで再開 |
| 240 | `(23, -46)` | `None` | `None` | 最後の検出から120ms経過し、初回扱いに戻る |

右手は検出し続ける入力なので、左手の欠落中も計算が継続する。
表示する点と保持時間は変更できる。例えば、人差し指の第2関節を表示し、保持時間を200msにすると、240msの左手も計算が継続する。

```console
uv run --locked python scripts/check_motion_calculation.py --landmark INDEX_FINGER_PIP --retention-ms 200
```

利用可能な点の名前は `--help` で確認できる。
計算処理の構成は[設計書の運動計算](docs/design.md#運動計算issue-7)を参照する。
