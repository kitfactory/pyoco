# フェーズ 3: DSL とディスカバリー タスクリスト

> [!IMPORTANT]
> **テスト要件**: 各チェックリスト項目は、関連するテスト（既存または新規追加）がパスしたことを確認してから完了とし、次の項目に進んでください。

## 1. 制御DSL（現行仕様） (`dsl/graph.py`, `core/engine.py`)
- [x] **`switch` のDSLサポート**
    - [x] `switch(on=...){ ... }` の構文解析と実行を実装する。
    - [x] `default` 省略時エラーを実行時に返す。
- [x] **反復DSLのサポート**
    - [x] `repeat` / `foreach` / `until` の構文解析と実行を実装する。
    - [x] collect 既定値（repeat/foreach=`list`, until=`last`）を適用する。

## 2. ディスカバリーの競合解決 (`discovery/loader.py`)
- [x] **優先順位ルールの実装**
    - [x] `config.tasks`（明示的）からのタスクを最初に読み込むか、高優先度としてマークする。
    - [x] パッケージ/モジュールから読み込む際、タスク名が既に存在するか確認する。
    - [x] 存在し、かつ明示的な場合はスキップ/警告する。
    - [x] 存在し、かつ暗黙的（別のパッケージ由来）な場合は、`--strict` ならエラー、そうでなければ警告ログを出力する。
- [x] **Strict モード**
    - [x] `TaskLoader` に `strict: bool` フラグを追加する。
    - [x] Strict モードでの名前衝突時に `AmbiguousTaskError` を発生させる。

## 3. ディスカバリー方式の一本化 (`discovery/loader.py`)
- [x] **flow.yaml 依存探索設定の廃止**
    - [x] `flow.yaml` の `discovery` キーを拒否する。
    - [x] 明示エラーを返し、利用者へ修正方法を提示する。
- [x] **探索元の限定**
    - [x] `pyoco.tasks` entry points を自動ロードする。
    - [x] `PYOCO_DISCOVERY_MODULES` 指定モジュールを追加ロードする。
