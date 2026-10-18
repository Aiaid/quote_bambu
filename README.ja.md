# Quote Bambu

[English](README.en.md) | [简体中文](README.md) | 日本語

Bambu Lab プリンターの稼働状況を Quote/0 電子ペーパーディスプレイに表示します。
Quote Bambu はローカル LAN の MQTT テレメトリーを読み取り、必要に応じて
カメラ画像を取得する、単一の Docker コンテナーで動作するサービスです。

> **非公式のコミュニティープロジェクトです。** Quote Bambu は Bambu Lab および
> MindReset/Dot とは関係がなく、両社の公認・推奨を受けたものではありません。

![Canvas モードのプレビュー](canvas_camera_x3.png)

<sub>既定の Canvas モードのカメラレイアウト。Image モードのプレビューは
後述します。</sub>

## 実機での表示例

![Bambu Lab プリンターと造形物を背景に、プリンターの状態を表示した Quote/0 を手に持っている様子](docs/media/quote-bambu-live-original.jpg)

元の写真に対して、形式変換、リサイズ、メタデータの削除のみを行っています。
AI によるレタッチは行っていません。写真は撮影時点のレイアウトを示しており、
日付表示オプションなど、現在のヘッダー設定とは異なる場合があります。
すべての対応対象機種で実機検証済みであることを示すものではありません。

## 対応機種

対応対象は P2S（主な開発基準機）、P1P / P1S、A1 / A1 mini、
X1 / X1C / X1E、H2D / H2DPro です。

通常 P2S / X1 / H2 系で使われる RTSPS と、通常 P1 / A1 系で使われる
ポート 6000 の JPEG ストリームを自動判別できます。Bambu の LAN 接続、カメラ、
開発者モードの動作は、機種、ファームウェア、セキュリティーモードによって変わる
可能性があります。すべての機種とファームウェアの組み合わせを検証したものではなく、
互換性を保証するものでもありません。機種名、ファームウェアのバージョン、
機密情報を伏せたログを添えた動作報告を歓迎します。

## 機能

- ローカルのプリンター MQTT テレメトリーを購読し、接続後に `pushall` による
  ステータスの一括取得を 1 回要求します。プリンターの制御コマンドは送信しません。
- RTSPS または JPEG のカメラ画像を取得し、16:9 に切り抜いたうえで、
  Floyd-Steinberg ディザリングを使って本プロジェクトの 1 ビット出力に変換します。
- プリンターの状態、進捗、日付と時刻、ノズル・ベッド・チャンバー温度、AMS の
  湿度と温度、4 つのフィラメントトレイ、完了予定時刻、レイヤー数、ジョブ名を表示します。
- HMS アラートは既定で非表示です。`SHOW_HMS=true` にすると全画面アラートを有効に
  できます。有効時は起動時に英語の HMS 説明文をダウンロードし、取得できない場合は
  一時的なローカルキャッシュを利用します。
- カメラが無効、または画像を取得できない場合は、データのみのレイアウトに切り替わります。
- Quote/0 Canvas API と Image API による出力に対応しています。

## Canvas モードと Image モード

`PUSH_MODE` で、同じプリンターデータをどのように描画するかを選択します。

| モード | Quote/0 API | 描画方法 |
|---|---|---|
| `canvas`（既定） | `/device/<id>/canvas` | `div` / `span` / CSS による宣言的レイアウトを送信します。テキストには Quote/0 のピクセルフォントクラスを使い、埋め込み画像はカメラとフィラメントの色見本にのみ使用します。 |
| `image` | `/device/<id>/image` | Pillow を使い、画面全体をローカルで 1 ビット PNG に描画します。 |

Canvas、Image、データのみの表示は、それぞれ独立したコンテンツブロックです。
表示するには、選択した API のコンテンツブロックを Dot. App のデバイスの
Loop タスクに追加してください。

![Image モードのプレビュー](preview_camera_x3.png)

## 必要な情報

Bambu プリンターから取得するもの：

- LAN IP アドレス
- プリンターのシリアル番号
- 8 桁の LAN アクセスコード

Quote/0 から取得するもの：

- API キー（`dot_app_...`）
- デバイスのシリアル番号

LAN 接続や開発者モードの要件は、コミュニティーによるプロトコル情報と限られた
動作確認に基づくものであり、安定した Bambu 公式連携ではありません。プリンターと
ファームウェアによっては、ローカル MQTT やカメラへのアクセスに LAN 専用モードと
開発者モードが必要になる場合があります。ファームウェア更新後は設定を再確認してください。

## Docker でのクイックスタート

```bash
git clone https://github.com/Aiaid/quote_bambu.git
cd quote_bambu
cp .env.example .env
# .env を編集し、必要な認証情報とデバイス ID を設定します。
docker compose up -d
docker compose logs -f
```

Docker Compose は amd64 と arm64 に対応したビルド済みマルチアーキテクチャー
イメージ `ghcr.io/aiaid/quote_bambu:latest` を取得します。
ローカルのソースコードで開発する場合は、次を実行してください。

```bash
docker compose --profile dev up bambu_cc_dev
```

## 設定

| 変数 | 説明 | 既定値 |
|---|---|---|
| `PRINTER_IP` | プリンターの LAN アドレス | 必須 |
| `PRINTER_SN` | プリンターのシリアル番号 | 必須 |
| `PRINTER_ACCESS` | 8 桁の LAN アクセスコード | 必須 |
| `PRINTER_LABEL` | ヘッダーに表示する機種名・名前（例：`X1C`、`A1 mini`） | `Bambu` |
| `QUOTE0_API_KEY` | Quote/0 API キー | 必須 |
| `QUOTE0_DEVICE_ID` | Quote/0 デバイスのシリアル番号 | 必須 |
| `INTERVAL_SECONDS` | 表示の更新間隔（秒） | `60` |
| `SHOW_CAMERA` | カメラ画像の取得を有効にする（`true` / `false`） | `true` |
| `SHOW_HMS` | HMS アラートを全画面表示する。`false` では通常のステータス画面を維持 | `false` |
| `SHOW_DATE` | ヘッダーに月日を表示する。`false` では時刻のみ表示 | `true` |
| `PUSH_MODE` | `canvas` または `image` | `canvas` |
| `CAMERA_PROTO` | `auto`、`rtsps`、`jpeg` | `auto` |
| `HMS_IGNORE` | 画面を切り替えない HMS ecode。16 桁の 16 進数をカンマ区切りで指定 | 空 |
| `TZ` | ヘッダーの時計と HMS タイムスタンプに使用する IANA タイムゾーン | `Asia/Shanghai` |

起動時に、必須項目、対応モード、更新間隔が正の値であることを検証します。
設定が不正な場合は終了ステータス 2 で終了します。

### 継続的に表示される HMS 通知を無視する

`SHOW_HMS=false` では、プリンターから HMS 項目が報告されても通常のステータス
画面を維持します。全画面の `ALERT` 表示を有効にするには、`.env` で
`SHOW_HMS=true` を設定してください。有効時は `HMS_IGNORE` で個別の継続的な
通知を非表示にできます。

`SHOW_DATE=true` ではヘッダーに `10-18 14:30` のように表示し、
`SHOW_DATE=false` では `14:30` のみを表示します。これは描画時点の時刻で、
`INTERVAL_SECONDS` ごとに更新され、サービスまたはコンテナーの `TZ` を使用します。
`.env` を編集した後は、`docker compose up -d --force-recreate` を実行して
設定を反映してください。ローカルのソースコード変更を反映するには、イメージの
再ビルド、または開発用コンテナーが必要です。

複数の ecode は半角カンマで区切ってください。`HMS_` 接頭辞やグループ間の
区切り文字は含めません。

```ini
SHOW_HMS=true
HMS_IGNORE=0500030000020019,0700420000020025
```

この設定が変更するのは Quote Bambu の表示ロジックだけです。プリンターの HMS 警告を
確認済みにしたり、解除・無効化したりするものではなく、プリンターの安全保護機能にも
影響しません。原因となる不具合を解消した後は、該当する ecode をリストから削除してください。

## プライバシーとデータの流れ

- プリンターのテレメトリーと、任意のカメラ画像をローカルネットワークから読み取ります。
- 表示を更新するため、描画したステータスを Quote/0 サービスに POST します。
  送信内容には印刷ジョブ名や、カメラを有効にしている場合は取得した画像が含まれることが
  あります。Canvas モードも宣言的レイアウトと埋め込み画像をアップロードするため、
  完全にローカルで完結する表示方式ではありません。
- `SHOW_HMS=true` の場合、起動時に Bambu の公開 HMS エンドポイントに接続して
  エラーの説明文を取得します。失敗した場合は一時キャッシュを使うか、コードをそのまま表示します。
- プリンターの LAN アクセスコードを Quote/0 に送る設計にはしていません。ただし、
  コンテナープロセスはプリンターのアクセスコードと Quote/0 API キーの両方を読み取るため、
  `.env`、ログ、ホストを適切に保護してください。

## セキュリティー上の境界

現在、プリンター固有のローカル証明書との互換性のため、MQTT 接続では TLS 証明書の
検証を省略しています。このため、LAN 内の中間者攻撃のリスクがあります。
RTSPS に使用する ffmpeg ビルドも、通常はプリンターの証明書を検証しません。

現在、RTSPS のアクセスコードは ffmpeg の入力 URL に含める必要があります。
Quote Bambu は ffmpeg の診断出力から機密情報を伏せますが、画像の取得中は
ホストの特権ユーザーにプロセス引数からコードを見られる可能性があります。

Quote Bambu は信頼できるホストと LAN でのみ実行してください。プリンターの
MQTT、RTSPS、JPEG のポートをインターネットに公開しないでください。
脆弱性の報告方法と運用上の注意事項は [SECURITY.md](SECURITY.md) を参照してください。

## 既知の制限

- RTSPS の画像取得には約 5～10 秒かかる場合があります。P1/A1 の JPEG ストリームは
  一般にそれより高速です。更新間隔を画像の取得時間より短くしないでください。
- 出力は 1 ビットのため、フィラメントの色見本はフルカラーではなく明るさを表します。
- 1 つのコンテナーで管理できるプリンターは 1 台です。複数台を使う場合は、
  コンテナーのインスタンスと設定をそれぞれ用意してください。
- H2D のデュアルノズルレイアウトは温度表示に 2 行使うため、フィラメントの表示行が
  1 行少なくなります。
- Bambu の HMS エンドポイントでレート制限やサーバーエラーが発生することがありますが、
  サービス全体の動作を停止するものではありません。
- 60 秒の更新間隔は外部給電での使用に適しています。電子ペーパーの頻繁な更新と
  ネットワーク通信はバッテリー駆動時間を短くする可能性があるため、バッテリー使用時は
  `INTERVAL_SECONDS` を長くしてください。
- ファームウェアやプロトコルの変更により、LAN 接続や開発者モードでの互換性が
  失われる場合があります。

## ローカルプレビューとテスト

Quote Bambu は Python 3.10 以降に対応しています。

```bash
uv run --with-requirements requirements-dev.lock pytest
uv run --with-requirements requirements-dev.lock python preview.py
uv run --with-requirements requirements-dev.lock python preview_canvas.py
```

プレビュースクリプトは、プリンターや Quote/0 に接続せず、代表的なレイアウトを描画します。
開発用の近似的なプレビューであり、すべての実機での動作を証明するものとして
扱わないでください。

## コントリビューション

不具合報告、ファームウェア・機種ごとの動作報告、ドキュメント改善、変更範囲を絞った
プルリクエストを歓迎します。貢献の前に [CONTRIBUTING.md](CONTRIBUTING.md) を
お読みください。脆弱性は [SECURITY.md](SECURITY.md) の手順に従い、非公開で報告してください。

## ライセンス

Quote Bambu のアプリケーションソースは [MIT License](LICENSE) で公開しています。
コンテナーには、GPLv3 コンポーネントを有効にしてビルドした独立した FFmpeg 7.1
実行ファイルも含まれます。FFmpeg と静的リンクされたライブラリーにはそれぞれの
ライセンスが引き続き適用され、MIT によって再ライセンスされるものではありません。
正確なバージョン、ビルド元、対応するソースコードへのリンク、ライセンス全文は
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) を参照してください。

## 参考資料

- [Quote/0 開発者プラットフォーム](https://dot.mindreset.tech/docs/service/open)
- [Quote/0 Canvas API](https://dot.mindreset.tech/docs/service/open/canvas_api)
- [Bambu Lab：アップデートとサードパーティー連携](https://blog.bambulab.com/updates-and-third-party-integration-with-bambu-connect/)
- [OpenBambuAPI](https://github.com/Doridian/OpenBambuAPI)
