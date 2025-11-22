# チュートリアル 7: 制御と可観測性 (Control & Observability)

v0.2.0 で導入された「実行制御」と「可観測性」の機能について学びます。
Pyoco は、実行ごとにユニークな **Run ID** を発行し、実行中のフローを安全に **キャンセル** する機能を提供します。

## 目標

1.  **Run ID** を確認する。
2.  長時間実行されるタスクを作成し、`Ctrl+C` でキャンセルする。
3.  `ctx.is_cancelled` を使用して、タスク側でキャンセルに協調する（Cooperative Cancellation）。

## 1. Run ID の確認

Pyoco を実行すると、ログの最初に `run_id` が表示されるようになりました。

```bash
🐇 pyoco > start flow=my_flow run_id=a1b2c3d4-...
```

この ID は、将来的にログの検索や、サーバー機能（v0.3.0予定）での実行管理に使用されます。

## 2. キャンセル可能なタスクの作成

長時間実行されるタスクは、ユーザーからのキャンセル要求（`Ctrl+C`）に反応して、処理を中断すべきです。
Pyoco は `ctx.is_cancelled` プロパティを通じて、現在の実行がキャンセルされたかどうかをタスクに伝えます。

`tasks.py` を作成します：

```python
import time
from pyoco import task

@task
def long_running_job(ctx):
    print("🏃 長い処理を開始します...")
    
    for i in range(10):
        # キャンセルチェック
        if ctx.is_cancelled:
            print("🛑 キャンセルを検知しました！クリーンアップして終了します。")
            return "cancelled"
            
        print(f"⏳ 処理中... {i+1}/10")
        time.sleep(1.0) # 重い処理のシミュレーション
        
    print("✅ 処理完了")
    return "done"
```

`flow.yaml` を作成します：

```yaml
flows:
  control_demo:
    graph: |
      long_running_job
    defaults: {}

tasks:
  long_running_job:
    callable: tasks:long_running_job
```

## 3. 実行とキャンセル

このフローを実行し、途中で `Ctrl+C` を押してみましょう。

```bash
pyoco run --config flow.yaml --flow control_demo
```

**出力例:**

```
🐇 pyoco > start flow=control_demo run_id=...
🏃 start node=long_running_job
🏃 長い処理を開始します...
⏳ 処理中... 1/10
⏳ 処理中... 2/10
^C
🛑 Ctrl+C detected. Cancelling active runs...
🛑 キャンセルを検知しました！クリーンアップして終了します。
✅ done node=long_running_job (2015.32 ms)
🥕 done flow=control_demo
```

### 解説

1.  **Ctrl+C 検知**: CLI が `SIGINT` を受け取り、エンジンにキャンセルを要求します。
2.  **ステータス変更**: 実行コンテキスト (`RunContext`) のステータスが `CANCELLING` に変わります。
3.  **タスクへの通知**: タスク内の `ctx.is_cancelled` が `True` を返すようになります。
4.  **早期終了**: タスクがループを抜けて終了します。これにより、リソースの無駄遣いを防ぎ、安全にシャットダウンできます。

もし `ctx.is_cancelled` をチェックしない場合、タスクは最後まで実行され続けます（Pyoco は強制終了を行いません）。「協調的キャンセル」を実装することで、より行儀の良いワークフローを作成できます。

## まとめ

- **Run ID** で実行を識別できます。
- **Ctrl+C** で実行をキャンセルできます。
- **ctx.is_cancelled** を使うことで、タスク内でキャンセルに応じた処理（中断、クリーンアップ）を実装できます。
