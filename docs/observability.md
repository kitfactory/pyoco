# Pyoco Observability Guide

Pyoco v0.5 では、Prometheus/Grafana/Webhook と連携するための最小構成を備えています。このドキュメントでは実運用に向けた設定手順と、トラブルシューティングのヒントをまとめます。

## 1. Prometheus 設定

### 1.1 /metrics エンドポイント

- Kanban Server（`pyoco server start`）は `http://<host>:<port>/metrics` に Prometheus 互換のテキストメトリクスを公開します。
- 主要メトリクス
  | 名前 | 種類 | 説明 |
  | --- | --- | --- |
  | `pyoco_runs_total{status}` | Counter | Run 状態遷移の累計。RUNNING/COMPLETED/FAILED が基本。 |
  | `pyoco_runs_in_progress` | Gauge | 現在 RUNNING 中の Run 数。 |
  | `pyoco_task_duration_seconds{task}` | Histogram | タスクごとの処理時間（秒）。 |
  | `pyoco_run_duration_seconds{flow}` | Histogram | フロー単位の完了時間（秒）。 |

### 1.2 Prometheus scrape 設定例

`prometheus.yml` に以下を追加します:

```yaml
scrape_configs:
  - job_name: "pyoco"
    scrape_interval: 15s
    static_configs:
      - targets: ["pyoco-kanban.internal:8000"]  # server start --host/--port に合わせて変更
```

> Tips: BasicAuth や TLS が必要な場合は usual Prometheus オプションを併用してください。

### 1.3 クエリ例

- 実行中 Run 数: `pyoco_runs_in_progress`
- 直近 5 分の完了数: `sum by (status) (increase(pyoco_runs_total{status!="PENDING"}[5m]))`
- タスク平均時間: `pyoco_task_duration_seconds_sum / clamp_min(pyoco_task_duration_seconds_count, 1)`

## 2. Grafana ダッシュボード

`docs/grafana_pyoco_cute.json` は以下の 3 パネルを含むスターターテンプレートです。

1. Runs in progress（Stat）
2. Run completions (last 5m)（Time series）
3. Average run duration by flow（Table）

### 2.1 インポート手順

1. Grafana の `Dashboards > Import` を開く。
2. 「Upload dashboard JSON file」で `docs/grafana_pyoco_cute.json` を選択。
3. Prometheus データソースを `PyocoProm`（既定名）もしくは任意の名前にリマップ。
4. 保存するだけで利用可能です。

> ダッシュボードをカスタマイズする場合は、「Panel JSON」を編集し、Pyoco が露出するメトリクス名をそのまま利用してください。

## 3. Webhook 通知

Run が `COMPLETED` または `FAILED` になったタイミングで任意のエンドポイントに JSON を POST できます。

| 環境変数 | 説明 |
| --- | --- |
| `PYOCO_WEBHOOK_URL` | 送信先 URL。未設定なら通知は無効。 |
| `PYOCO_WEBHOOK_TIMEOUT` | タイムアウト秒 (既定 3.0)。 |
| `PYOCO_WEBHOOK_RETRIES` | リトライ回数 (既定 1)。 |
| `PYOCO_WEBHOOK_SECRET` | `X-Pyoco-Token` ヘッダに入るシークレット。 |

ペイロード例:

```json
{
  "event": "run.completed",
  "run_id": "9f0f...",
  "flow_name": "main",
  "status": "COMPLETED",
  "duration_ms": 523.0,
  "tasks": {
    "prepare": {"state": "SUCCEEDED", "duration_ms": 120.4},
    "train": {"state": "SUCCEEDED", "duration_ms": 402.6}
  }
}
```

## 4. REST API 拡張の活用

- `GET /runs?status=RUNNING&flow=demo&limit=10` … ダッシュボードで「実行中一覧」に利用。
- `GET /runs/{run_id}` … `task_summary` と `run_duration_ms` が含まれるので、詳細パネルで表示可能。
- `GET /runs/{run_id}/logs?tail=200` … 直近ログだけを取得し Grafana の Log panel に流用。

## 5. トラブルシューティング

| 症状 | 対応 |
| --- | --- |
| `/metrics` にアクセスできない | Kanban サーバ起動オプション（`--host`/`--port`）が正しいか確認。 |
| Counter が増えない | Worker 側の heartbeat が届いていない可能性。`pyoco.worker.runner` のログを確認。 |
| Webhook が来ない | `PYOCO_WEBHOOK_URL` 設定、ネットワーク、再試行回数を確認。`store.webhook.last_error` をログ出力することで原因追跡可能。 |

## 6. 推奨 CI チェック

- `PYTHONPATH=src .venv/bin/python -m pytest tests/observability` … メトリクスまわりのリグレッション防止。
- `scripts/lint_metrics.sh`（任意で作成） … `/metrics` エンドポイントのフォーマットを curl でチェック。

---

外部監視ツールを優先し、Pyoco 本体は最小限の可観測性を提供する方針です。不足があれば Issue/PR でフィードバックをお願いします。
