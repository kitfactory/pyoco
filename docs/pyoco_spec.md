# pyoco 現行仕様サマリ

この文書は、現行の pyoco 仕様を短く整理したものです。詳細は `docs/spec.md` / `docs/architecture.md` を正本とします。

## 1) 基本方針
- ローカル実行を前提にした軽量ワークフローエンジン。
- flow 定義は `flow.yaml` の単一 `flow:` を正とする。
- グラフDSLは `>>` のみを連結演算子として扱う。

## 2) Graph DSL（現行）
- 逐次連結: `A >> B >> C`
- 参照パイプ: `pipe(NAME)`
- 分岐: `switch(on=...){ case: ...; default: ...; }`
- 反復:
  - `repeat(count=...){ ... }`
  - `foreach(over=..., item=..., index=...){ ... }`
  - `until(cond=..., max_iter=...){ ... }`

### 2.1 主要ルール
- 単独 `>` は非対応（`>>` のみ）。
- `switch` の `default` 省略は実行時エラー。
- `pipe(NAME)` は `pipes:` から展開し、循環参照・上限超過はエラー。
- dry-run は形式検証中心（式の実評価は対象外）。

## 3) flow.yaml 例
```yaml
version: 1

pipes:
  setup: "task_a >> task_b"

tasks:
  task_a:
    callable: "pkg.module:task_a"
  task_b:
    callable: "pkg.module:task_b"
  task_c:
    callable: "pkg.module:task_c"

flow:
  defaults:
    mode: "batch"
    items: ["x", "y"]
    done: false
  graph: |
    pipe(setup)
    >> switch(on={{mode}}){
      batch: repeat(count=2){ task_c };
      default: task_c;
    }
    >> foreach(over={{items}}, item=it, index=idx){ task_c }
    >> until(cond={{params.done}}, max_iter=5){ task_c }
```

## 4) 入力参照
- 推奨: `$ctx.params.<key>`
- 上流出力を明示する場合: `$node.<task>.output`
- 環境変数: `$env.<KEY>`

## 5) タスク探索
- `flow.yaml` で `discovery:` は非対応。
- discovery は次の2系統:
  - `pyoco.tasks` entry points
  - `PYOCO_DISCOVERY_MODULES` で指定したモジュール

## 6) CLI
- 実行: `pyoco run --config flow.yaml`
- 検証: `pyoco check --config flow.yaml --dry-run`
- 支援情報:
  - `pyoco support tasks --config flow.yaml`
  - `pyoco support task --config flow.yaml --name <task>`
  - `pyoco support guide --config flow.yaml`

## 7) 補足
- 仕様の変更時は `docs/spec.md` と `docs/architecture.md` を先に更新する。
- 本文書はチーム内の早見表として維持する。
