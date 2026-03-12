# 🐇 Pyoco チュートリアル

ようこそ。このチュートリアルは、まず小さな成功体験をすぐ得て、その後で Pyoco の今の推奨モデルに自然に移れるように並べています。

## ✨ こんな読み方がおすすめ

- ⚡ とにかく一回動かしたい: まず 1 章だけ読んで実行する
- 🧩 ちゃんとした形で使いたい: 1 章のあと 7 章へ進む
- 🛠️ graph DSL まで一気に掴みたい: 1 章から 4 章まで順に読む

基本方針として、再利用するタスクは **entry point plug-in として登録** し、`flow.yaml` では `tasks.<local_name>.use` で公開名を束ねます。前半の章では例を短く保つために `tasks.<name>.callable` も使います。

## 📚 目次

1.  [Hello World](01_hello_ja.md)
    *   数分で最初の Pyoco 実行まで進みます。
2.  [パラメータと入力 (Parameters & Inputs)](02_params_ja.md)
    *   ただのデモから、使える workflow に近づけます。
3.  [データフローと依存関係 (Data Flow & Dependencies)](03_data_flow_ja.md)
    *   タスク間で結果をつなぎ、graph を読みやすく保ちます。
4.  [制御コンポーネント (pipe/switch/repeat/foreach/until)](04_parallel_ja.md)
    *   graph DSL に分岐、再利用、反復を追加します。
5.  [アーティファクトと保存 (Artifacts & Saving)](05_artifacts_ja.md)
    *   残したい成果物をファイルへ保存します。
6.  [応用: エラーハンドリング (Advanced: Error Handling)](06_errors_ja.md)
    *   リトライや制限を入れて、現実的な workflow に寄せます。
7.  [BaseTask を使ったカスタムタスク (Custom Tasks)](07_custom_tasks_ja.md)
    *   推奨ルートである `BaseTask` + plug-in + `use` を学びます。
8.  [制御と可観測性 (Control & Observability)](08_control_ja.md)
    *   Run ID の見方と Ctrl+C での安全停止を学びます。

---
[English Version](index.md)
