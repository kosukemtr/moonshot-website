# AGENTS.md

このディレクトリは、量子リソース見積もり一覧ページの生成元と出力を置く場所です。

## 参照PDFの扱い

- 文献PDFは `references/` に保存してください。
- `references/*.pdf` はリポジトリ直下の `.gitignore` で除外しているため、Gitには追加しないでください。
- 作業前に `references/` が無い、または参照PDFが不足している場合は、`content/preamble.md` の「保存済みPDF」にあるリンクからPDFをダウンロードして補完してください。
- IACR ePrint などで直接ダウンロードできない場合は、同じ論文のHAL-Inria、arXiv、出版社ページなど、信頼できる公開PDFで補完して構いません。その場合もファイル名は既存の命名に寄せてください。

## 生成手順

- データを更新したら、以下を実行してMarkdownとHTMLを再生成してください。

```bash
./build_resource_estimates.sh
```

- 入力データの一次管理ファイルは `data/resource_estimates_rows.json` です。
- 生成時には `data/resource_estimates_rows.json` から `data/resource_estimates.tsv` を逆生成し、そのTSV相当の行データからHTMLと数値JSONを作ります。
- 生成時には `data/resource_estimates_numeric.json` も作られます。これはインタラクティブなグラフ表示に使うための機械可読な数値データです。
- 数値として表現できる値は、表示用TSVの文字列だけに閉じ込めず、生成スクリプトで必ず `resource_estimates_numeric.json` に抽出・標準化されるようにしてください。
- 生成後は、表の行数、リンク、表示崩れに加えて、数値JSONが生成され、`physical_qubits`、`logical_qubits`、`runtime_seconds`、`spacetime_volume_qubit_days` などの主要指標が入っているか確認してください。

## ローカル確認の扱い

- このディレクトリのHTMLは、原則として `./build_resource_estimates.sh` による生成完了を確認基準にしてください。
- Codex内蔵ブラウザでの `file://` HTML確認は環境依存のエラーが出やすいため、利用者から明示的に依頼されない限り実施しないでください。
- 生成後の報告では、HTMLを生成したこと、未公開か公開済みか、必要なら生成されたHTMLファイルへのリンクを簡潔に伝えてください。

## 主要ファイルと公開対象

- 入力データは `data/resource_estimates_rows.json` です。原則として新規エントリ追加・修正はここに入れてください。
- `data/resource_estimates.tsv` は生成物です。HTML生成時に `data/resource_estimates_rows.json` から逆変換されます。直接編集した場合は、同じ内容を必ずJSONへ反映してください。
- 生成スクリプトは `scripts/render_resource_estimates.py` です。列の追加、グラフ仕様、換算ルール、表示ロジックを変える場合はここを更新してください。
- `data/resource_estimates_numeric.json` は生成物ですが、公開グラフで使うためGit管理対象です。JSON更新後は必ず再生成して差分に含めてください。
- 公開対象のHTMLは原則として次の2つです。
- `quantum_resource_estimates_graph.html`: 論理量子ビット数とToffoli換算または論理ゲート数のグラフ。
- `quantum_resource_estimates_speedup_graph.html`: 生デバイス指標と古典/量子時間比のグラフ。
- `quantum_resource_estimates.html` と `quantum_resource_estimates.md` は確認用の表です。利用者が明示しない限り公開・Git追加しないでください。
- `quantum_resource_estimates_physical_graph.html` は過去に試作した物理リソース系グラフです。利用者が明示しない限り公開・Git追加しないでください。
- `references/*.pdf`、`previews/_work/`、一時PNG、`.DS_Store` は公開対象に含めないでください。

## データ入力の基本方針

- `data/resource_estimates_rows.json` の `records` 配列の各オブジェクトは「論文が報告した1つの条件・1つの見積もり」を表してください。
- `columns` 配列はTSVへ逆変換するときの列順です。列を追加・削除・改名するときは、全recordのキーと生成スクリプト側の処理をそろえてください。
- 1つの論文表セルに複数の数値がある場合、グラフ化できるように原則として別行に分けてください。例: 実行時間、物理量子ビット数、対象サイズ、アルゴリズム条件が複数ある場合。
- 数値で表せる列には、必ず数値だけを入れてください。単位、`p=`、説明文、約物、範囲説明は入れないでください。
- 不明値は `NA` を使ってください。空欄、`-`、`unknown`、説明文の混在は避けてください。
- 単位は列名に合わせて統一してください。実行時間は秒、エラー率はfraction、物理・論理量子ビット数はqubit数、時空間体積はqubit-daysです。
- 数値の根拠、単位変換、推定した事情、ただし書きは `数値根拠`、`備考`、`通信・その他仮定`、`古典計算根拠` などの文章列に書いてください。
- 論文内の表記が曖昧、図から読み取った、別論文の古典基準を近接ベンチマークとして使った、推定値を使った、などの場合は必ず `備考` に明記してください。
- 根拠リンクは残してください。リンクはMarkdown形式で構いませんが、数値列には入れず、根拠列に入れてください。
- 物理量子ビット種と誤り訂正符号は別列です。`デバイス` や `物理量子ビット種` に `surface code` などの符号名を入れないでください。物理量子ビット種が不明なら `not specified` または `NA` としてください。
- 誤り訂正なしの実験は、必要に応じて物理量子ビット数と論理量子ビット数を同じ値として扱って構いません。その場合は `実験実施` を `1` にし、備考に実験済みであることを書いてください。
- ブロックエンコーディング、SELECT、QSVT などのサブルーチンだけのコストは、end-to-endの資源と混同しないでください。入れる場合は `見積もりの種類` と `備考` にサブルーチンのみであることを明記し、生成JSONの `isSubroutineOnly` が真になるようにしてください。

## グラフ用の換算ルール

- 論理グラフの縦軸は `toffoli_equiv_gates` 相当です。優先順位は、Toffoli数があればToffoli数、なければTゲート数をT/4で換算、なければCCZ数、なければその他論理ゲート数を換算なしで扱います。
- HTMLではT/4をデフォルトにし、UIでT/2にも切り替えられるようにしています。この挙動を壊さないでください。
- CCZはToffoli相当として1対1で扱います。
- `Toffoli数`、`Tゲート数`、`Cliffordゲート数`、`その他論理ゲート数` は、論文が直接報告している値を優先してください。合成や外挿を行った場合は根拠列と備考に式を書いてください。
- 論理量子ビット数がない行は、論理グラフではスキップされます。グラフに出したい場合は、論文根拠または明記した推定ルールに基づいて数値を入れてください。
- 実行時間からToffoli数を逆算する場合や、Rz合成の平均Tゲート数など補助仮定を使う場合は、仮定と式を備考に残してください。

## 古典時間・加速比の扱い

- `古典計算時間(s)` は、論文に記載された値またはユーザーが明示した外挿モデルに基づく値だけを入れてください。
- `古典/量子時間比` は、論文が値を報告していない場合、TSVに推測値として保存せず、HTML生成時に `古典計算時間(s) / 実行時間(s)` から計算する方針です。
- RSA系の古典時間は、ユーザー指定のGNFS外挿を用いてよいです。基準点はRSA-250、829 bits、2700 core-yearsで、秒換算では10^6 coreを仮定します。この仮定はページ内注意書きと根拠列に残してください。
- 量子超越性やNISQ実験の古典比較では、後続の反論・改善論文を古典時間として採用することがあります。どの古典論文を使ったかを `古典計算根拠` に明記してください。

## 文献確認とPDF

- 新しい論文を追加するときは、まずPDFを `references/` に保存してください。arXivなら `arxiv_XXXX_XXXXX.pdf` のように既存命名へ寄せてください。
- PDFがすでにある場合は再ダウンロードしなくて構いませんが、参照ページ・表・図番号を確認してください。
- ネットワークが必要な場合は、必要最小限の取得だけ行い、取得元がarXiv、出版社、著者、IACR、GitHubなど信頼できる一次情報に近いことを優先してください。
- 画像プレビューは検証補助です。公開グラフに必要な場合を除き、`previews/` や `previews/_work/` の新規生成物はGitに入れないでください。
- 論文中で表と本文の値が食い違う場合は、勝手に片方へ丸めず、採用した値と不整合の存在を備考に書いてください。

## 生成と検証の手順

1. `data/resource_estimates_rows.json` を編集します。
2. 必要なら `scripts/render_resource_estimates.py` を編集します。
3. `./build_resource_estimates.sh` を実行します。
4. `data/resource_estimates.tsv`、`data/resource_estimates_numeric.json`、公開HTMLが再生成されたことを確認します。
5. `git diff --check` を実行し、空白や構文上の問題がないことを確認します。
6. `git status --short` を確認し、公開対象外の確認用HTML、PDF、プレビュー、`.DS_Store` をstageしないようにします。
7. 公開する場合は、公開対象ファイルだけをstageしてcommit/pushします。

## ブラウザ確認

- 利用者から明示的に依頼されない限り、Codex内蔵ブラウザで確認しないでください。このプロジェクトでは内蔵ブラウザ確認で環境依存エラーが出やすいためです。
- 生成確認は `./build_resource_estimates.sh`、`git diff --check`、必要に応じてHTML内の該当文字列検索で行ってください。
- もしレイアウトをどうしても検証する必要がある場合は、事前に利用者へ一言断り、ブラウザ確認でなく生成物の静的検査やスクリーンショット生成など、より再現性の高い方法を優先してください。

## 公開時の注意

- ユーザーが「公開してOK」と明示したときだけcommit/pushしてください。
- 公開対象は通常、`data/resource_estimates_rows.json`、`data/resource_estimates.tsv`、`data/resource_estimates_numeric.json`、`quantum_resource_estimates_graph.html`、`quantum_resource_estimates_speedup_graph.html`、`scripts/render_resource_estimates.py`、必要なら `content/*.md` と `data/physical_conversion_calibration.tsv` です。
- 確認用表HTML/Markdown、物理グラフ試作HTML、参照PDF、プレビュー画像、一時ファイルはstageしないでください。
- 公開後は、commit hash、公開したページ、まだローカルに残っている未追跡ファイルがあればその扱いを短く報告してください。
