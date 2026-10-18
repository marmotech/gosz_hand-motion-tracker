# gosz_hand-motion-tracker

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
