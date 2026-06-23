### 論理のみの行へ使うなら

論理回路だけの論文、例えばChevignard et al. 2025やSchrottenloher 2026を物理量子ビットに換算する場合は、次の2段階で書くのが無難。

1. **storage-only下限**  
   `N_phys_storage ~= alpha d^2 N_logical`。例えば `d=25`、`alpha=2` と置くと、1論理量子ビットあたり約1250物理量子ビットになる。ただしこれはmagic-state工場やroutingを含まない下限。

2. **end-to-end推定**  
   `N_T` または `N_Toffoli`、目標実行時間、cycle time、reaction time、magic-state factoryの設計を入れて `N_factory` を足す。RSA-2048のようにToffoli数が大きい場合、`N_factory` が支配的になりやすい。

したがって、例えばChevignard et al. 2025のRSA-2048 `1730 logical qubits` を、Gidney 2025風のsurface-code仮定で読むなら、データ保持だけなら `O(10^6)` 物理量子ビット級がまず粗い下限になる。ただし、同論文の `2^40.87` Toffoli規模を何日・何時間で処理するかを決めると、magic-state工場分が上乗せされる。これは論文本文の値ではないので、スライドでは「surface-code仮定による外挿」と明示する。

## 次に追加するとよい候補

- Van Meter et al. 2009、Jones et al. 2010、O'Gorman et al. 2017を個別PDFで保存し、Gidney and Ekera 2021 Table 2のhistorical rowsを一次文献で確認する。
- 量子化学、格子問題、HHL/線形方程式、Hamiltonian simulation、最適化を別Markdownに追加する。
