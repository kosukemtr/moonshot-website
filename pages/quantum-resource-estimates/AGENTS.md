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

- 生成時には `data/resource_estimates_numeric.json` も作られます。これはインタラクティブなグラフ表示に使うための機械可読な数値データです。
- 数値として表現できる値は、表示用TSVの文字列だけに閉じ込めず、生成スクリプトで必ず `resource_estimates_numeric.json` に抽出・標準化されるようにしてください。
- 生成後は、表の行数、リンク、表示崩れに加えて、数値JSONが生成され、`physical_qubits`、`logical_qubits`、`runtime_seconds`、`spacetime_volume_qubit_days` などの主要指標が入っているか確認してください。

## ローカル確認の扱い

- このディレクトリのHTMLは、原則として `./build_resource_estimates.sh` による生成完了を確認基準にしてください。
- Codex内蔵ブラウザでの `file://` HTML確認は環境依存のエラーが出やすいため、利用者から明示的に依頼されない限り実施しないでください。
- 生成後の報告では、HTMLを生成したこと、未公開か公開済みか、必要なら生成されたHTMLファイルへのリンクを簡潔に伝えてください。
