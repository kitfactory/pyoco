# 6. 応用: エラーハンドリング

この章では、「うまくいく日」ではなく「崩れそうな日」に flow をどう行儀よく動かすかを扱います。実運用では、失敗・遅延・不安定さへの備えが効いてきます。

## 🎯 目標
- 不安定なタスクのリトライを設定する。
- 長時間実行されるタスクにタイムアウトを設定する。
- 障害ポリシー (`fail_policy`) を使用する。

## 🔁 1. リトライ
タスクが失敗（例外が発生）した場合、Pyoco は自動的にリトライできます。

```python
@task(retries=3)
def flaky_api_call(ctx):
    import random
    if random.random() < 0.7:
        raise ValueError("Network error!")
    return "Success"
```

または `flow.yaml` で設定します:
```yaml
tasks:
  flaky_api_call:
    retries: 3
```

## ⏱️ 2. タイムアウト
タスクの実行時間を制限できます。

```python
@task(timeout_sec=5.0)
def long_job(ctx):
    import time
    time.sleep(10) # これは失敗します！
```

## 🧯 3. 障害ポリシー
デフォルトでは、タスクが失敗するとフロー全体が停止します (`fail_policy="stop"`)。
これを `isolate` に変更すると、独立したタスクの実行を継続できます。

```python
@task(fail_policy="isolate")
def non_critical_task(ctx):
    raise ValueError("Oops")
```

`non_critical_task` が失敗した場合:
- それに依存するタスクはスキップされます。
- 独立したタスクは実行を継続します。

これは、オプションのステップや、1つの失敗がパイプライン全体をクラッシュさせるべきではない並列処理の場合に役立ちます。

---
**ここまでで十分戦えます。** 小さく書けて、分岐できて、失敗にも備えられるようになりました。もし 7 章を後回しにしていたら、ここで plug-in-first の形へ戻るのが自然です。
