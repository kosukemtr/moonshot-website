# 量子リソース見積もりメモ

作成日: 2026-06-16  
対象: 量子コンピューターによる素因数分解、離散対数、ECDLP、Grover型探索、量子化学、量子シミュレーション  
方針: 表中の数値は、保存済みPDF本文に明記された値だけを記載する。単位表記は読みやすさのために統一する。PDFリンクは該当値が載っているページへ飛ぶ `#page=` 付きリンクにする。

## 表記・単位

- `q`: physical qubits または logical qubits の個数。どちらかは列名で区別する。
- `kq`: kiloqubits。`1 kq = 1,000 q`。
- `Mq`: megaqubits。`1 Mq = 1,000,000 q`。
- `Bq`: billion qubits。`1 Bq = 1,000,000,000 q`。
- `megaqubitdays`: 時空間体積の単位。`1 megaqubitday = 1,000,000 physical qubits × 1 day`。
- `NL`: Xue and Covey 2026 の表記で、Table IIでは各QPUモジュール内のsurface-code logical qubits数を表す。これはmemoryを除くper-module値であり、アルゴリズム全体の総論理量子ビット数ではない。
- `QEC cycle`: エラー訂正サイクル。論文により `surface code cycle`、`code cycle`、`stabilizer measurement cycle`、`measurement time` として扱われる。
- `code distance (d)`: 量子誤り訂正コードの距離。回路深さやcode cycle数ではないので、主表では専用列に分ける。
- `reaction time`: 測定結果に応じた古典制御の反応時間。
- `shot`: 確率的アルゴリズムの1回の実行・試行。1 shotで成功するとは限らない場合、論文は期待shot数、retry risk、per-shot runtimeなどを別々に報告することがある。
- `論理ゲート数`: 表中の `Toffoli`、`T gates`、`CNOT`、`X` などのゲート数は、特に断りがない限り論理回路上のゲート数として読む。`surface code cycles`、`QEC cycles`、`CCZ states`、magic state数は論理ゲート数そのものではないので、行内で区別する。
- `quantum security parameter (qs)`: Gheorghiu and Mosca 2019では、security parameterを「破るのに必要なfundamental operations数のlog2」と定義している。この論文の対称鍵・ハッシュの解析ではfundamental operationsをsurface code cyclesとして扱う（[定義箇所](https://arxiv.org/pdf/1902.02332#page=3), [Table I](https://arxiv.org/pdf/1902.02332#page=18)）。

## 保存済みPDF

- [Gidney and Ekera, 2021, How to factor 2048 bit RSA integers in 8 hours using 20 million noisy qubits](https://arxiv.org/pdf/1905.09749)
- [Gidney, 2025, How to factor 2048 bit RSA integers with less than a million noisy qubits](https://arxiv.org/pdf/2505.15917)
- [Webster et al., 2026, The Pinnacle Architecture: Reducing the cost of breaking RSA-2048 to 100 000 physical qubits using quantum LDPC codes](https://arxiv.org/pdf/2602.11457)
- [Cain et al., 2026, Shor's algorithm is possible with as few as 10,000 reconfigurable atomic qubits](https://arxiv.org/pdf/2603.28627)
- [Xue and Covey, 2026, Factoring 2048 bit RSA integers with a half-million-qubit modular atomic processor](https://arxiv.org/pdf/2605.03951)
- [Babbush et al., 2026, Securing Elliptic Curve Cryptocurrencies against Quantum Vulnerabilities: Resource Estimates and Mitigations](https://arxiv.org/pdf/2603.28846)
- [Schrottenloher, 2026, Optimized Point Addition Circuits for Elliptic Curve Discrete Logarithms](https://arxiv.org/pdf/2606.02235)
- [Gheorghiu and Mosca, 2019, Benchmarking the quantum cryptanalysis of symmetric, public-key and hash-based cryptographic schemes](https://arxiv.org/pdf/1902.02332)
- [Chevignard, Fouque, Schrottenloher, 2025, Reducing the Number of Qubits in Quantum Factoring](https://eprint.iacr.org/2024/222.pdf)
- [Fowler et al., 2012, Surface codes: Towards practical large-scale quantum computation](https://arxiv.org/pdf/1208.0928)
- [Gidney, 2017, Factoring with n + 2 clean qubits and n - 1 dirty qubits](https://arxiv.org/pdf/1706.07884)
- [Ekera and Hastad, 2017, Quantum algorithms for computing short discrete logarithms and factoring RSA integers](https://arxiv.org/pdf/1702.00249)
- [Regev, 2024, An Efficient Quantum Factoring Algorithm](https://arxiv.org/pdf/2308.06572)
- [QREChem, 2024, Quantum Resource Estimation Software for Chemistry](https://arxiv.org/pdf/2404.16351)
- [Yoshioka et al., 2022/2024, Hunting for quantum-classical crossover in condensed matter problems](https://arxiv.org/pdf/2210.14109)
- [Lee et al., 2020, Even more efficient quantum computations of chemistry through tensor hypercontraction](https://arxiv.org/pdf/2011.03494)
- [von Burg et al., 2020, Quantum computing enhanced computational catalysis](https://arxiv.org/pdf/2007.14460)
- [Reiher et al., 2016, Elucidating Reaction Mechanisms on Quantum Computers](https://arxiv.org/pdf/1605.03590)

## 主表

発表日（初出）順。`発表日（初出）` は arXiv v1 の投稿日を優先し、arXivでないものはPDF本文の投稿日・会議提出月を使う。対象問題・対象サイズごとに1行へ分けた。
