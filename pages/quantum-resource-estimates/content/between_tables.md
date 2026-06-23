## NA監査メモ

- Gidney and Ekerå 2021 Table 3/4: `code distance` と `通信・その他仮定` は表中に明記があったため、`d1,d2,δoff,cmul,cexp,csep,z,volume` を補完した。論理ゲート数はTable 3の一部RSA行以外では単一スカラー値として表にないため、該当行はNAのまま。
- Gidney 2025 Table 5: `s,l,w1,w3,w4,f,m,Pdeviant,E(shots)` は全Table 5行に補完した。RSA-2048だけは物理換算節で `d=25`、hot/cold storage、6 CCZ factories、897864 physical qubitsが明記されるため補完した。他サイズの物理量子ビット・実行時間・code distanceは同論文中に個別換算がないためNAのまま。
- Lee et al. 2020 Table III: Table IIIはlogical qubitsとToffoli-equivalent countの表で、物理量子ビット・runtime・code distance・cycle/reaction timeは出ていないためNAのまま。Appendix C/Dのsurface-code layout行だけ物理実装値を別行にしている。
- QREChem 2024 Table I: Table IはFeMocoのlogical T gate数比較で、物理量子ビット・runtime・code distanceは同表にないためNAのまま。Table IIのhardware examplesは備考に記載したが、Table I各行の物理見積もり値ではない。
- Yoshioka et al. 2022 Table S12: Table S12はphysical qubits、code distance、runtime、repetition countを明記するが、総論理量子ビット数・論理ゲート数・深さは同表の列ではないためNAのまま。

## 比較時の注意

- 量子化学・量子シミュレーションのQPE系見積もりでは、Hamiltonian simulationやmagic-state供給のコストと、QPEに投入する近似固有状態の準備コストが分かれている。主表では各行の備考に状態準備仮定を明示した。
- Yoshioka et al. 2022/2024のTable S12は、Table Iの単純なT-countではなく、surface-code floor plan、magic-state factory、lattice-surgery routingを含むactual runtime見積もりとして読む。
- 量子化学・量子シミュレーションの行では、同じ「FeMoco」でもactive space、Hamiltonian、精度、Trotter/qDRIFT/qubitization/THCなどの手法が異なる。横比較では対象サイズと見積もりの種類を必ず見る。
- 「論理量子ビット」は論文により意味が異なる。抽象回路のqubit数、active logical qubits、idle storageを含むlogical qubits、コードブロック内のencoded logical qubitsが混在する。
- 「論理ゲート数」は、論文が `Toffoli`、`T gates`、`CNOT`、`X` などとして数えている回路レベルのゲート数を指す。`surface code cycles`、`QEC cycles`、`CCZ states` は論理ゲート数ではなく、エラー訂正やmagic-state供給側の資源量として分けて読む。
- 多くの論文はToffoli数またはT数だけを主要指標として報告しており、CNOT、X、RZ、測定などの総数は記載されていないことが多い。表では、該当箇所に他ゲート種の総数が見当たらない場合は備考で「記載なし」とした。
- 「物理量子ビット」はエラー訂正方式、cycle time、reaction time、magic state supply、routing、connectivityで大きく変わる。特にGidney 2025とWebster et al. 2026は物理仮定が近いが、エラー訂正アーキテクチャが異なる。
- Chevignard et al. 2025は論理量子ビット数を大幅に下げるが、論文自身がphysical architecture、routing、distillationを含めない論理回路見積もりとして扱っている。
- Fowler et al. 2012はN=2000 bitの概算であり、RSA-2048の値ではない。
- Regev 2024は、今回の「具体的な物理リソース表」では補助文献として扱う。具体的なRSA-2048物理量子ビット数は表中で「なし」とした。

## cycle time / measurement time のメモ

- Lee et al. 2020のFeMoCo surface-code見積もりは、1 us cycle、0.1% physical gate error、code distance 31、4 CCZ factories、Toffoli production rate 25 kHzを仮定し、約4 Mq・3 daysを得ている。Figure 10の1908 logical qubitsは床面図全体のfootprintで、Figure 11/本文のdata qubits <700はその内訳であり追加分ではない。本文にある0.01% physical gate errorの楽観ケースは、物理量子ビット数1e6・実行時間1.5 days・code distance 15として別行にしている。
- FeMoCoの古典計算時間については、Zhai et al. 2026のLLDUC 76 orbital / 152 qubit FeMo-co benchmarkから、FrontierのCPU+GPU合算FLOPに理想換算したvariational DMRG D=393000・2 sweepsの22.9 hoursを8.244e4 sとして記録している。この値はLee et al. 2020 Table IIIおよびLow et al. 2025 Table VのLi/FeMoco-76 active space側に対応する古典基準として扱い、Reiher Hamiltonianのsurface-code物理実装行には割り当てない。Low et al. 2025のFeMoco-76物理見積もりは4.5e6 physical qubits、8.6 hours、p=0.001、d=27で、速度比グラフでは8.244e4 s / 3.096e4 s ~= 2.66として計算される。
- Gidney and Ekera 2021、Gidney 2025、Webster et al. 2026は、比較的そろった仮定として `QEC cycle = 1 us`、`reaction time = 10 us` を使う。
- Cain et al. 2026は neutral atom 系で、本文中では `1 ms stabilizer measurement cycle` を仮定する一方、将来の高速readoutとして `~1 ms` から `~1 us` への改善可能性にも触れる。
- Xue and Covey 2026は、QEC cycle timeをmeasurement timeで見積もり、Table IIで `tmea = 1 ms` と `tmea = 0.25 ms` を比較する。本文では、論理操作時間が少なくとも `tmea + 10d us` と説明されている。
- Pinnacle 2026のTable VIで `1 year` と `1 month` が同じ `94 kq` になるのは、94 kqが「実行に必要な最小構成」の下限であり、その最小構成でも期待実行時間が1か月以内に収まるため、と解釈できる。時間制約をさらに厳しくして `1 week` や `1 day` にすると、並列度を上げるために必要物理量子ビット数が増える。

## 論理量子ビットから物理量子ビットへの換算メモ

主表の `物理量子ビット` 列は、論文本文に明記された値だけを入れている。論理量子ビット数しか載っていない論文についても、surface codeなどのエラー訂正を仮定すれば概算換算はできる。ただし、これは論文記載値ではなく二次的な推定なので、主表には混ぜず、この節で分けて扱う。

### 換算式の骨格

surface-code系での概算は、少なくとも次の形に分けるのがよい。

```text
N_phys ~= N_data + N_factory + N_routing + N_io

N_data ~= c_patch(d) * N_logical
c_patch(d) ~= alpha * d^2

d = smallest code distance satisfying
    N_fail ~= N_locations * p_L(d, p_phys) <= epsilon

p_L(d, p_phys) ~= A * (p_phys / p_th)^((d+1)/2)

N_factory ~= R_magic * Q_factory(p_phys, d, target_error)
R_magic ~= N_T_or_Toffoli / target_runtime
```

- `N_logical`: 論理量子ビット数。論文によってactive logical qubits、storage込み、ancilla込みなど意味が違う。
- `d`: code distance。物理エラー率、論理ゲート数、許容失敗確率、実行時間で決まる。
- `c_patch(d)`: 1論理量子ビットあたりの物理量子ビット係数。rotated surface codeの粗い見積もりでは `alpha d^2` 型になる。Pinnacle論文では、比較対象として「rotated surface code block uses `2d^2 - 1` physical qubits」と書いている（[Webster et al. 2026, p.5](https://arxiv.org/pdf/2602.11457#page=5)）。
- `N_factory`: T state、CCZ stateなどのmagic-state生成に必要な物理量子ビット。Toffoli/T数と目標実行時間に強く依存する。
- `N_routing`, `N_io`: lattice surgery、通信、measurement、古典制御待ち、モジュール間通信などの余白。

このため、論理量子ビット数だけから `N_phys = 定数 × N_logical` とするのは危険。特に暗号解読では、magic-state生成と並列化の入れ方が支配的になりうる。

### 既存論文からのキャリブレーション
