#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import html
import json
import math
import re
import subprocess
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


MAIN_ALIGN: list[str] | None = None

NUMERIC_JSON_NAME = "resource_estimates_numeric.json"
ROWS_JSON_NAME = "resource_estimates_rows.json"
GRAPH_HTML_NAME = "quantum_resource_estimates_graph.html"
GRAPH_HTML_EN_NAME = "quantum_resource_estimates_graph_en.html"
PHYSICAL_GRAPH_HTML_NAME = "quantum_resource_estimates_physical_graph.html"
SPEEDUP_GRAPH_HTML_NAME = "quantum_resource_estimates_speedup_graph.html"
SPEEDUP_GRAPH_HTML_EN_NAME = "quantum_resource_estimates_speedup_graph_en.html"
PREVIEW_DIR_NAME = "previews"
FEEDBACK_ISSUE_URL = (
    "https://github.com/kosukemtr/moonshot-website/issues/new"
    "?title=%E9%87%8F%E5%AD%90%E3%83%AA%E3%82%BD%E3%83%BC%E3%82%B9%E8%A6%8B%E7%A9%8D%E3%82%82%E3%82%8A%E3%82%B0%E3%83%A9%E3%83%95%E3%81%AE%E4%BF%AE%E6%AD%A3%E6%8F%90%E6%A1%88"
    "&body=%23%23+%E4%BF%AE%E6%AD%A3%E3%81%97%E3%81%9F%E3%81%84%E7%82%B9%0A%0A%E4%BE%8B%3A+%E8%AB%96%E6%96%87%E5%90%8D%E3%80%81%E3%83%97%E3%83%AD%E3%83%83%E3%83%88%E7%82%B9%E3%80%81%E6%95%B0%E5%80%A4%E3%80%81%E6%8F%9B%E7%AE%97%E3%83%AB%E3%83%BC%E3%83%AB%E3%81%AA%E3%81%A9%0A%0A%23%23+%E8%A9%B2%E5%BD%93%E3%81%99%E3%82%8B%E8%AB%96%E6%96%87%E3%83%BB%E3%83%87%E3%83%BC%E3%82%BF%0A%0A-+%E8%AB%96%E6%96%87%3A%0A-+%E5%AF%BE%E8%B1%A1%E3%82%B5%E3%82%A4%E3%82%BA%3A%0A-+%E7%8F%BE%E5%9C%A8%E8%A1%A8%E7%A4%BA%E3%81%95%E3%82%8C%E3%81%A6%E3%81%84%E3%82%8B%E5%80%A4%3A%0A-+%E6%AD%A3%E3%81%97%E3%81%84%E3%81%A8%E6%80%9D%E3%81%86%E5%80%A4%3A%0A%0A%23%23+%E6%A0%B9%E6%8B%A0%0A%0A%E8%AB%96%E6%96%87%E4%B8%AD%E3%81%AE%E3%83%9A%E3%83%BC%E3%82%B8%E3%80%81%E8%A1%A8%E3%80%81%E5%BC%8F%E3%80%81%E3%81%BE%E3%81%9F%E3%81%AF%E8%A3%9C%E8%B6%B3%E8%AA%AC%E6%98%8E%E3%81%B8%E3%81%AE%E3%83%AA%E3%83%B3%E3%82%AF%E3%82%92%E8%B2%BC%E3%81%A3%E3%81%A6%E3%81%8F%E3%81%A0%E3%81%95%E3%81%84%E3%80%82%0A%0A%23%23+%E8%A3%9C%E8%B6%B3%0A%0A%E5%BF%85%E8%A6%81%E3%81%AA%E3%82%89%E8%87%AA%E7%94%B1%E3%81%AB%E8%BF%BD%E8%A8%98%E3%81%97%E3%81%A6%E3%81%8F%E3%81%A0%E3%81%95%E3%81%84%E3%80%82%0A"
)
FEEDBACK_ISSUE_HREF = FEEDBACK_ISSUE_URL.replace("&", "&amp;")
AI_EXTRACTION_NOTICE = (
    f'データは論文を確認しながら整備していますが、AIによる情報抽出を含むため、'
    f'一部に誤りがある可能性があります。間違いを見つけた場合は '
    f'<a href="{FEEDBACK_ISSUE_HREF}" target="_blank" rel="noopener">下書き入りのGitHub Issue</a> からお知らせください。'
)
AI_EXTRACTION_NOTICE_EN = (
    f'The dataset is curated from the papers, but it includes AI-assisted extraction '
    f'and may contain errors. Please report corrections via '
    f'<a href="{FEEDBACK_ISSUE_HREF}" target="_blank" rel="noopener">this prefilled GitHub Issue</a>.'
)
PDF_SOURCE_MAP = {
    "1208.0928": "fowler_etal_2012_surface_codes.pdf",
    "1605.03590": "reiher_etal_2016_femoco_reaction_mechanisms.pdf",
    "1702.00249": "ekera_hastad_2017_short_dlp_factoring_rsa.pdf",
    "1706.07884": "gidney_2017_factoring_nplus2_clean.pdf",
    "1902.02332": "gheorghiu_mosca_2019_benchmarking_quantum_cryptanalysis.pdf",
    "1905.09749": "gidney_ekera_2021_rsa2048_8h_20m.pdf",
    "1910.11333": "arute_etal_2019_sycamore_quantum_supremacy.pdf",
    "2007.14460": "von_burg_etal_2020_quantum_catalysis.pdf",
    "2012.03819": "arxiv_2012_03819.pdf",
    "2011.03494": "lee_etal_2020_thc_quantum_chemistry.pdf",
    "2106.14734": "wu_etal_2021_zuchongzhi_quantum_advantage.pdf",
    "2109.03494": "zhu_etal_2021_zuchongzhi_2_1_quantum_advantage.pdf",
    "2111.12509": "stamatopoulos_etal_2022_financial_market_risk_gradient.pdf",
    "2110.14502": "liu_etal_2021_closing_quantum_supremacy_gap_sunway.pdf",
    "2210.14109": "yoshioka_etal_2022_quantum_classical_crossover_condensed_matter.pdf",
    "2211.12489": "dalzell_etal_2022_qipm_portfolio_optimization.pdf",
    "2304.11119": "arxiv_2304_11119.pdf",
    "2311.17388": "arxiv_2311_17388.pdf",
    "2308.05077": "begusic_gray_chan_2023_fast_converged_classical_utility.pdf",
    "s41586-023-06096-3": "kim_etal_2023_utility_before_fault_tolerance.pdf",
    "2308.06572": "regev_2024_efficient_quantum_factoring_algorithm.pdf",
    "2311.05933": "mckay_etal_2023_layer_fidelity_benchmarking.pdf",
    "2307.14310": "stamatopoulos_zeng_2024_derivative_pricing_qsp.pdf",
    "2404.16351": "qrechem_2024_resource_estimation_chemistry.pdf",
    "2406.06323": "arxiv_2406_06323.pdf",
    "2406.02501": "decross_etal_2024_h2_random_circuits.pdf",
    "2502.15882": "low_etal_2025_spectrum_amplification_electronic_structure.pdf",
    "2503.05647": "arxiv_2503_05647.pdf",
    "2505.15917": "gidney_2025_rsa2048_less_than_million.pdf",
    "2510.25838": "gharibyan_etal_2025_heuristic_quantum_advantage_peaked_circuits.pdf",
    "2510.26547": "arxiv_2510_26547.pdf",
    "2509.08807": "zhuang_etal_2025_navier_stokes_quantum_advantage.pdf",
    "2601.04621": "arxiv_2601_04621.pdf",
    "2602.11457": "webster_etal_2026_pinnacle_rsa2048_100k.pdf",
    "2603.22778v1": "arxiv_2603_22778v1.pdf",
    "2603.28627": "cain_etal_2026_shor_10000_reconfigurable_atomic_qubits.pdf",
    "2603.28846": "babbush_etal_2026_google_ethereum_ecdlp_whitepaper.pdf",
    "2604.21908": "kremer_dupuis_2026_quantum_no_advantage_peaked_circuit.pdf",
    "2605.00745": "arxiv_2605_00745.pdf",
    "2605.04025": "hartnett_etal_2026_fermi_hubbard_digital_quantum_processor.pdf",
    "2605.03951": "xue_covey_2026_half_million_modular_atomic_processor.pdf",
    "2605.30967": "arxiv_2605_30967.pdf",
    "2606.04771": "rausch_etal_2026_classical_frontier_fermi_hubbard_quench.pdf",
    "2606.02235": "schrottenloher_2026_optimized_point_addition_ecdlp.pdf",
    "eprint-2024-222": "chevignard_fouque_schrottenloher_2025_reducing_qubits_factoring.pdf",
}
MANUAL_PREVIEW_MAP = {
    ("1208.0928", 2): "fowler_2012_p2_table_text.png",
    ("1208.0928", 12): "fowler_2012_p12_error_rate.png",
    ("1605.03590", 5): "reiher_2016_p5_table1.png",
    ("1605.03590", 7): "reiher_2016_p7_table2.png",
    ("1702.00249", 1): "ekera_hastad_2017_p1_abstract.png",
    ("1702.00249", 2): "ekera_hastad_2017_p2_exponent_length.png",
    ("1706.07884", 12): "gidney_2017_p12_figure26.png",
    ("1902.02332", 3): "gheorghiu_mosca_2019_p3_grover_method.png",
    ("1902.02332", 13): "gheorghiu_mosca_2019_p13_rsa2048_fig45.png",
    ("1902.02332", 18): "gheorghiu_mosca_2019_p18_table2_rsa.png",
    ("1905.09749", 1): "gidney_ekera_2021_p1_abstract_costs.png",
    ("1905.09749", 3): "gidney_ekera_2021_p3_tables1_2.png",
    ("1905.09749", 13): "gidney_ekera_2021_p13_error_physical_count.png",
    ("1905.09749", 16): "gidney_ekera_2021_p16_table3_rsa.png",
    ("1905.09749", 18): "gidney_ekera_2021_p18_table4_dlp.png",
    ("2007.14460", 13): "von_burg_2020_p13_table1.png",
    ("2007.14460", 14): "von_burg_2020_p14_table2.png",
    ("2011.03494", 7): "lee_2020_p7_table3.png",
    ("2011.03494", 28): "lee_2020_p28_fig10_floorplan.png",
    ("2210.14109", 6): "yoshioka_2022_p6_table1.png",
    ("2210.14109", 55): "yoshioka_2022_p55_table_s12.png",
    ("2211.12489", 4): "dalzell_2022_p4_table1.png",
    ("2308.06572", 1): "regev_2024_p1_abstract_intro.png",
    ("2404.16351", 7): "qrechem_2024_p7_table1.png",
    ("2505.15917", 18): "gidney_2025_p18_table5.png",
    ("2505.15917", 20): "gidney_2025_p20_source.png",
    ("2509.08807", 8): "zhuang_2025_p8_resource_summary.png",
    ("2509.08807", 50): "zhuang_2025_p50_code_distance.png",
    ("2509.08807", 51): "zhuang_2025_p51_overhead.png",
    ("2602.11457", 14): "webster_2026_p14_table4.png",
    ("2602.11457", 16): "webster_2026_p16_eq23.png",
    ("2602.11457", 18): "webster_2026_p18_table6_physical_qubits.png",
    ("2602.11457", 5): "webster_2026_p5_surface_code_block.png",
    ("2603.28627", 2): "cain_2026_p2_fig1_overview.png",
    ("2603.28627", 6): "cain_2026_p6_fig3_resources.png",
    ("2603.28846", 8): "babbush_2026_p8_fig1_ecdlp.png",
    ("2605.03951", 9): "xue_covey_2026_p9_table2.png",
    ("2606.02235", 4): "schrottenloher_2026_p4_table2.png",
    ("eprint-2024-222", 2): "chevignard_2025_p2_abstract.png",
    ("eprint-2024-222", 43): "chevignard_2025_p43_table3_rsa.png",
}
LABEL_PREVIEW_MAP = {
    ("1902.02332", 18, "Table I"): "gheorghiu_mosca_2019_p18_table1_symmetric.png",
    ("1902.02332", 18, "Table II"): "gheorghiu_mosca_2019_p18_table2_rsa.png",
    ("1902.02332", 18, "Table III"): "gheorghiu_mosca_2019_p18_table3_ecc.png",
}
NUMERIC_ONLY_COLUMNS = {
    "実験実施",
    "論理量子ビット(q)",
    "物理量子ビット(q)",
    "Toffoli数",
    "Tゲート数",
    "Cliffordゲート数",
    "その他論理ゲート数",
    "深さ/サイクル(count)",
    "実行時間(s)",
    "時空間体積(qubit-days)",
    "物理エラー率(fraction)",
    "code distance",
    "cycle/測定時間(s)",
    "reaction time(s)",
    "shot/run(count)",
    "retry risk(fraction)",
    "論理エラー率推定(fraction)",
    "古典計算時間(s)",
    "古典/量子時間比",
    "倍率",
}
NUMERIC_CHECK_COLUMNS = [
    "対象サイズ",
    "見積もりの種類",
    "実験実施",
    "論理量子ビット(q)",
    "物理量子ビット(q)",
    "Toffoli数",
    "Tゲート数",
    "Cliffordゲート数",
    "その他論理ゲート数",
    "深さ/サイクル(count)",
    "実行時間(s)",
    "時空間体積(qubit-days)",
    "物理エラー率(fraction)",
    "code distance",
    "cycle/測定時間(s)",
    "reaction time(s)",
    "shot/run(count)",
    "retry risk(fraction)",
    "論理エラー率推定(fraction)",
    "古典計算時間(s)",
    "古典/量子時間比",
    "通信・その他仮定",
    "古典計算仮定",
    "備考",
]

NUMBER_RE = re.compile(
    r"(?P<qualifier>about|approx\.?|approximately|fewer than|less than|under|at most|at least|"
    r"<=|>=|<|>|約|ほぼ|最大|最小)?\s*"
    r"(?P<number>2\^-?\d+(?:\.\d+)?|-?\d+(?:\.\d+)?(?:e[+-]?\d+)?|-?\d+(?:\.\d+)?[kKMB])\s*"
    r"(?P<scale>thousand|million|billion|trillion)?\s*"
    r"(?P<unit>megaqubitdays?|qubitdecades?|surface code cycles|logical cycles|QEC cycles|"
    r"Toffoli-equivalent gates|Toffoli\+T/2 count|Toffoli gates|Toffolis|T gates|Clifford gates|"
    r"CNOT/X|CCZ states|logical qubits|physical qubits|qubits|bits|orbitals|electrons|"
    r"kq|Mq|Bq|q|days?|hours?|years?|weeks?|h|min|ms|us|ns|MHz|kHz|Hz|%|mHa|mHartree|shots?|runs?)?",
    re.IGNORECASE,
)

MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

POPOVER_COLUMNS = {"通信・その他仮定", "数値根拠", "備考", "論理エラー率推定根拠"}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def read_tsv(path: Path) -> tuple[list[str], list[list[str]]]:
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f, delimiter="\t"))
    if not rows:
        raise ValueError(f"{path} is empty")
    header, body = rows[0], rows[1:]
    bad = [(i + 2, len(row)) for i, row in enumerate(body) if len(row) != len(header)]
    if bad:
        sample = ", ".join(f"line {line}: {cols} cols" for line, cols in bad[:10])
        raise ValueError(f"{path} has rows with wrong column count: {sample}")
    return header, body


def rows_json_payload(header: list[str], rows: list[list[str]], source: str) -> dict[str, object]:
    return {
        "schema_version": 1,
        "description": "Primary row-object data for quantum resource estimate entries.",
        "source": source,
        "columns": header,
        "row_count": len(rows),
        "records": [dict(zip(header, row)) for row in rows],
    }


def write_rows_json(path: Path, header: list[str], rows: list[list[str]], source: str) -> None:
    path.write_text(
        json.dumps(rows_json_payload(header, rows, source), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def write_tsv(path: Path, header: list[str], rows: list[list[str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def read_rows_json(path: Path) -> tuple[list[str], list[list[str]]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise ValueError(f"{path} has unsupported schema_version: {payload.get('schema_version')}")
    header = payload.get("columns")
    records = payload.get("records")
    if not isinstance(header, list) or not all(isinstance(column, str) for column in header):
        raise ValueError(f"{path} has invalid columns")
    if not isinstance(records, list):
        raise ValueError(f"{path} has invalid records")
    rows: list[list[str]] = []
    expected = set(header)
    for index, record in enumerate(records, start=1):
        if not isinstance(record, dict):
            raise ValueError(f"{path} record {index} is not an object")
        keys = set(record)
        if keys != expected:
            missing = sorted(expected - keys)
            extra = sorted(keys - expected)
            raise ValueError(f"{path} record {index} column mismatch: missing={missing[:5]}, extra={extra[:5]}")
        row = []
        for column in header:
            value = record[column]
            if not isinstance(value, str):
                raise ValueError(f"{path} record {index} column {column} is not a string")
            row.append(value)
        rows.append(row)
    row_count = payload.get("row_count")
    if row_count != len(rows):
        raise ValueError(f"{path} row_count mismatch: declared {row_count}, actual {len(rows)}")
    return header, rows


def load_main_rows(base: Path) -> tuple[list[str], list[list[str]]]:
    tsv_path = base / "data" / "resource_estimates.tsv"
    json_path = base / "data" / ROWS_JSON_NAME
    header, rows = read_rows_json(json_path)
    write_tsv(tsv_path, header, rows)
    return header, rows


def strip_markdown_links(text: str) -> str:
    return MARKDOWN_LINK_RE.sub(lambda match: match.group(1), text)


def pdf_key_and_page(href: str) -> tuple[str, int] | None:
    parsed = urlparse(href)
    page = 1
    if parsed.fragment.startswith("page="):
        try:
            page = int(parsed.fragment.split("=", 1)[1])
        except ValueError:
            page = 1
    if "arxiv.org" in parsed.netloc and parsed.path.startswith("/pdf/"):
        key = parsed.path.rsplit("/", 1)[-1].replace(".pdf", "")
        return key, page
    if "nature.com" in parsed.netloc and parsed.path == "/articles/s41586-023-06096-3.pdf":
        return "s41586-023-06096-3", page
    if "eprint.iacr.org" in parsed.netloc and parsed.path == "/2024/222.pdf":
        return "eprint-2024-222", page
    return None


def preview_filename(key: str, page: int) -> str:
    safe = re.sub(r"[^A-Za-z0-9_-]+", "_", key)
    return f"{safe}_p{page}_crop.png"


def preview_href_for_link(href: str, label: str = "") -> str | None:
    parsed = pdf_key_and_page(href)
    if parsed is None:
        return None
    key, page = parsed
    for (label_key, label_page, label_snippet), label_filename in LABEL_PREVIEW_MAP.items():
        if key == label_key and page == label_page and label_snippet in label:
            return f"{PREVIEW_DIR_NAME}/{label_filename}"
    filename = MANUAL_PREVIEW_MAP.get((key, page))
    if not filename:
        return None
    return f"{PREVIEW_DIR_NAME}/{filename}"


def collect_pdf_preview_targets(markdown: str) -> set[tuple[str, int]]:
    targets: set[tuple[str, int]] = set()
    for _label, href in MARKDOWN_LINK_RE.findall(markdown):
        parsed = pdf_key_and_page(href)
        if parsed is not None:
            targets.add(parsed)
    return targets


def ensure_pdf_previews(base: Path, markdown: str) -> None:
    targets = collect_pdf_preview_targets(markdown)
    if not targets:
        return
    preview_dir = base / PREVIEW_DIR_NAME
    preview_dir.mkdir(parents=True, exist_ok=True)
    missing_pdfs: list[str] = []
    for key, page in sorted(targets):
        pdf_name = PDF_SOURCE_MAP.get(key)
        if not pdf_name:
            continue
        pdf_path = base / "references" / pdf_name
        if not pdf_path.exists():
            missing_pdfs.append(str(pdf_path))
            continue
        output = preview_dir / preview_filename(key, page)
        if output.exists():
            continue
        prefix = preview_dir / f".tmp_{preview_filename(key, page).removesuffix('.png')}"
        subprocess.run(
            [
                "pdftoppm",
                "-png",
                "-r",
                "120",
                "-f",
                str(page),
                "-l",
                str(page),
                "-x",
                "40",
                "-y",
                "60",
                "-W",
                "950",
                "-H",
                "1050",
                str(pdf_path),
                str(prefix),
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        rendered = preview_dir / f"{prefix.name}-{page}.png"
        if not rendered.exists():
            matches = sorted(preview_dir.glob(f"{prefix.name}-*.png"))
            if not matches:
                raise FileNotFoundError(f"pdftoppm did not create preview for {pdf_path} page {page}")
            rendered = matches[0]
        rendered.replace(output)
        for leftover in preview_dir.glob(f"{prefix.name}-*.png"):
            leftover.unlink(missing_ok=True)
    if missing_pdfs:
        raise FileNotFoundError("missing local PDFs for previews: " + ", ".join(missing_pdfs[:10]))


def number_to_float(raw: str) -> float:
    raw = raw.strip()
    if raw.startswith("2^"):
        return math.pow(2, float(raw[2:]))
    multiplier = 1.0
    if raw[-1:] in {"k", "K"}:
        multiplier = 1_000.0
        raw = raw[:-1]
    elif raw[-1:] == "M":
        multiplier = 1_000_000.0
        raw = raw[:-1]
    elif raw[-1:] == "B":
        multiplier = 1_000_000_000.0
        raw = raw[:-1]
    return float(raw) * multiplier


def scale_multiplier(scale: str | None) -> float:
    if not scale:
        return 1.0
    return {
        "thousand": 1_000.0,
        "million": 1_000_000.0,
        "billion": 1_000_000_000.0,
        "trillion": 1_000_000_000_000.0,
    }[scale.lower()]


def normalize_numeric(field: str, value: float, unit: str) -> tuple[str, float, str]:
    unit_l = unit.lower()
    if field == "論理量子ビット(q)":
        return "logical_qubits", value, "qubits"
    if field == "物理量子ビット(q)":
        return "physical_qubits", value, "qubits"
    if field == "Toffoli数":
        return "toffoli_count", value, "gates"
    if field == "Tゲート数":
        return "t_gate_count", value, "gates"
    if field == "Cliffordゲート数":
        return "clifford_gate_count", value, "gates"
    if field == "その他論理ゲート数":
        return "other_logical_gate_count", value, "gates"
    if field == "深さ/サイクル(count)":
        return "cycle_count", value, "cycles"
    if field == "実行時間(s)":
        return "runtime_seconds", value, "seconds"
    if field == "時空間体積(qubit-days)":
        return "spacetime_volume_qubit_days", value, "qubit_days"
    if field == "物理エラー率(fraction)":
        return "physical_error_rate", value, "fraction"
    if field == "cycle/測定時間(s)" or field == "reaction time(s)":
        return "time_seconds", value, "seconds"
    if field == "shot/run(count)":
        return "shots_or_runs", value, "count"
    if field == "retry risk(fraction)":
        return "retry_risk", value, "fraction"
    if field == "論理エラー率推定(fraction)":
        return "estimated_logical_error_rate", value, "fraction"
    if unit_l == "kq":
        metric = "physical_qubits" if field == "物理量子ビット" else "qubits"
        return metric, value * 1_000.0, "qubits"
    if unit_l == "mq":
        metric = "physical_qubits" if field == "物理量子ビット" else "qubits"
        return metric, value * 1_000_000.0, "qubits"
    if unit_l == "bq":
        metric = "physical_qubits" if field == "物理量子ビット" else "qubits"
        return metric, value * 1_000_000_000.0, "qubits"
    if unit_l == "q" or unit_l == "qubits":
        if field == "論理量子ビット":
            return "logical_qubits", value, "qubits"
        if field == "物理量子ビット":
            return "physical_qubits", value, "qubits"
        return "qubits", value, "qubits"
    if field == "論理量子ビット" or unit_l == "logical qubits":
        return "logical_qubits", value, "qubits"
    if field == "物理量子ビット" or unit_l == "physical qubits":
        return "physical_qubits", value, "qubits"
    if "toffoli" in unit_l:
        return "toffoli_count", value, "gates"
    if unit_l == "t gates":
        return "t_gate_count", value, "gates"
    if unit_l == "clifford gates":
        return "clifford_gate_count", value, "gates"
    if unit_l in {"surface code cycles", "logical cycles", "qec cycles"} or field == "深さ/サイクル":
        return "cycle_count", value, "cycles"
    if unit_l in {"day", "days"}:
        return "runtime_seconds", value * 86_400.0, "seconds"
    if unit_l in {"hour", "hours", "h"}:
        return "runtime_seconds", value * 3_600.0, "seconds"
    if unit_l == "min":
        return "runtime_seconds", value * 60.0, "seconds"
    if unit_l == "year" or unit_l == "years":
        return "runtime_seconds", value * 365.25 * 86_400.0, "seconds"
    if unit_l == "week" or unit_l == "weeks":
        return "runtime_seconds", value * 7.0 * 86_400.0, "seconds"
    if unit_l == "ms":
        return "time_seconds", value * 1e-3, "seconds"
    if unit_l == "us":
        return "time_seconds", value * 1e-6, "seconds"
    if unit_l == "ns":
        return "time_seconds", value * 1e-9, "seconds"
    if unit_l == "mhz":
        return "frequency_hz", value * 1_000_000.0, "Hz"
    if unit_l == "khz":
        return "frequency_hz", value * 1_000.0, "Hz"
    if unit_l == "hz":
        return "frequency_hz", value, "Hz"
    if field == "物理エラー率":
        if unit_l == "%":
            return "physical_error_rate", value / 100.0, "fraction"
        return "physical_error_rate", value, "fraction"
    if unit_l == "%":
        return "fraction", value / 100.0, "fraction"
    if unit_l in {"megaqubitday", "megaqubitdays"}:
        return "spacetime_volume_qubit_days", value * 1_000_000.0, "qubit_days"
    if unit_l in {"qubitdecade", "qubitdecades"}:
        return "spacetime_volume_qubit_days", value * 365.25 * 10.0, "qubit_days"
    if field == "code distance":
        return "code_distance", value, "distance"
    if field == "shot/run" or unit_l in {"shot", "shots", "run", "runs"}:
        return "shots_or_runs", value, "count"
    if unit_l in {"bits", "bit", "orbitals", "electrons", "mha", "mhartree"}:
        return "target_or_accuracy", value, unit_l
    return "generic_numeric", value, unit or "number"


def numeric_observations(header: list[str], rows: list[list[str]]) -> list[dict[str, object]]:
    observations: list[dict[str, object]] = []
    for row_index, row in enumerate(rows, start=1):
        row_map = dict(zip(header, row))
        row_id = f"r{row_index:04d}"
        for field in NUMERIC_CHECK_COLUMNS:
            if field not in row_map:
                continue
            cell = row_map[field]
            if not cell or cell == "NA":
                continue
            searchable = strip_markdown_links(cell)
            for match in NUMBER_RE.finditer(searchable):
                raw = match.group(0).strip()
                unit = (match.group("unit") or "").strip()
                value = number_to_float(match.group("number")) * scale_multiplier(match.group("scale"))
                metric, normalized_value, normalized_unit = normalize_numeric(field, value, unit)
                observations.append(
                    {
                        "row_id": row_id,
                        "row_index": row_index,
                        "field": field,
                        "problem": row_map.get("解ける問題", ""),
                        "paper": strip_markdown_links(row_map.get("論文", "")),
                        "target": row_map.get("対象サイズ", ""),
                        "estimate_type": row_map.get("見積もりの種類", ""),
                        "raw": raw,
                        "value": value,
                        "unit": unit,
                        "qualifier": (match.group("qualifier") or "").strip(),
                        "metric": metric,
                        "normalized_value": normalized_value,
                        "normalized_unit": normalized_unit,
                    }
                )
    return observations


def validate_numeric_coverage(header: list[str], rows: list[list[str]], observations: list[dict[str, object]]) -> None:
    checked = 0
    for row in rows:
        row_map = dict(zip(header, row))
        for field in NUMERIC_CHECK_COLUMNS:
            if field in row_map and row_map[field] and row_map[field] != "NA":
                checked += len(list(NUMBER_RE.finditer(strip_markdown_links(row_map[field]))))
    if checked != len(observations):
        raise ValueError(f"numeric extraction mismatch: matched {checked} values but wrote {len(observations)} observations")
    if checked == 0:
        raise ValueError("numeric extraction found no numeric values")


def validate_numeric_only_columns(header: list[str], rows: list[list[str]]) -> None:
    allowed = re.compile(r"^(?:NA|[-+]?\d+(?:\.\d+)?(?:e[-+]?\d+)?(?:;[-+]?\d+(?:\.\d+)?(?:e[-+]?\d+)?)*)$", re.IGNORECASE)
    numeric_columns = [column for column in header if column in NUMERIC_ONLY_COLUMNS]
    problems: list[str] = []
    for row_number, row in enumerate(rows, start=2):
        row_map = dict(zip(header, row))
        for column in numeric_columns:
            value = row_map[column].strip()
            if not allowed.fullmatch(value):
                problems.append(f"line {row_number}, {column}: {value}")
                if len(problems) >= 10:
                    raise ValueError("non-numeric value in numeric-only columns: " + "; ".join(problems))
    if problems:
        raise ValueError("non-numeric value in numeric-only columns: " + "; ".join(problems))


def numeric_cell_values(value: str) -> list[float]:
    if not value or value == "NA":
        return []
    return [float(part) for part in value.split(";")]


def validate_numeric_semantics(header: list[str], rows: list[list[str]]) -> None:
    problems: list[str] = []
    for row_number, row in enumerate(rows, start=2):
        row_map = dict(zip(header, row))
        for column in NUMERIC_ONLY_COLUMNS.intersection(row_map):
            if ";" in row_map[column]:
                problems.append(f"line {row_number}, {column} must be split into separate rows: {row_map[column]}")
        if "論理量子ビット(q)" in row_map:
            values = numeric_cell_values(row_map["論理量子ビット(q)"])
            allow_small_logical_qubits = "2605.30967" in row_map.get("論文", "")
            if not allow_small_logical_qubits and any(0 < value < 10 for value in values):
                problems.append(f"line {row_number}, 論理量子ビット(q): {row_map['論理量子ビット(q)']}")
            if any(not value.is_integer() for value in values):
                problems.append(f"line {row_number}, 論理量子ビット(q) must be integer: {row_map['論理量子ビット(q)']}")
        if "物理量子ビット(q)" in row_map:
            values = numeric_cell_values(row_map["物理量子ビット(q)"])
            no_error_correction_experiment = (
                row_map.get("誤り訂正符号", "").strip() == "NA"
                and "no error correction" in row_map.get("見積もりの種類", "").lower()
            )
            if not no_error_correction_experiment and any(0 < value < 100 for value in values):
                problems.append(f"line {row_number}, 物理量子ビット(q): {row_map['物理量子ビット(q)']}")
        if len(problems) >= 10:
            raise ValueError("numeric semantic checks failed: " + "; ".join(problems))
    if problems:
        raise ValueError("numeric semantic checks failed: " + "; ".join(problems))


def write_numeric_json(base: Path, header: list[str], rows: list[list[str]]) -> None:
    validate_numeric_only_columns(header, rows)
    validate_numeric_semantics(header, rows)
    observations = numeric_observations(header, rows)
    validate_numeric_coverage(header, rows, observations)
    payload = {
        "schema_version": 1,
        "description": "Machine-readable numeric values extracted from resource_estimates_rows.json for plotting.",
        "source": f"data/{ROWS_JSON_NAME}",
        "checked_columns": NUMERIC_CHECK_COLUMNS,
        "row_count": len(rows),
        "observation_count": len(observations),
        "observations": observations,
    }
    (base / "data" / NUMERIC_JSON_NAME).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def first_markdown_link(markdown: str) -> str:
    match = MARKDOWN_LINK_RE.search(markdown)
    return match.group(2) if match else ""


def graph_category(problem: str) -> str:
    if any(token in problem for token in ("量子化学", "量子シミュレーション", "FeMoco", "Fermi", "Hubbard", "Heisenberg", "spin")):
        return "chemistry"
    if any(token in problem for token in ("ECDLP", "ECC", "離散対数", "対称鍵", "ハッシュ", "Bitcoin", "素因数分解", "RSA整数")):
        return "crypto"
    return "other"


def graph_category_label(category: str) -> str:
    return {
        "chemistry": "量子化学・量子シミュレーション",
        "crypto": "素因数分解・暗号系",
        "other": "その他",
    }.get(category, category)


def is_subroutine_only(row_map: dict[str, str]) -> bool:
    text = " ".join(
        [
            row_map.get("見積もりの種類", ""),
            row_map.get("通信・その他仮定", ""),
            row_map.get("備考", ""),
        ]
    ).lower()
    markers = (
        "subroutine-only",
        "サブルーチン",
        "single qsvt-based",
        "end-to-end資源ではない",
        "not end-to-end",
    )
    return any(marker in text for marker in markers)


def parse_optional_float(value: str) -> float | None:
    value = value.strip()
    if not value or value == "NA":
        return None
    return float(value)


def classical_quantum_runtime_ratio(
    reported_ratio: float | None, classical_runtime: float | None, quantum_runtime: float | None
) -> float | None:
    if reported_ratio is not None:
        return reported_ratio
    if classical_runtime is None or quantum_runtime is None or quantum_runtime <= 0:
        return None
    return classical_runtime / quantum_runtime


CORE_YEAR_SECONDS = 365.25 * 86_400.0
RSA_CLASSICAL_PARALLEL_CORES = 1_000_000.0
RSA250_BITS = 829
RSA250_CORE_YEARS = 2700.0
RSA250_SOURCE_URL = "https://en.wikipedia.org/wiki/RSA_numbers#RSA-250"


def gnfs_complexity_proxy(bits: int) -> float:
    c = (64.0 / 9.0) ** (1.0 / 3.0)
    log_n = bits * math.log(2.0)
    return math.exp(c * (log_n ** (1.0 / 3.0)) * (math.log(log_n) ** (2.0 / 3.0)))


GNFS_RSA250_COMPLEXITY = gnfs_complexity_proxy(RSA250_BITS)


def gnfs_rsa_classical_core_years(bits: int) -> float:
    return RSA250_CORE_YEARS * gnfs_complexity_proxy(bits) / GNFS_RSA250_COMPLEXITY


def gnfs_rsa_classical_runtime_seconds(bits: int) -> float:
    core_years = gnfs_rsa_classical_core_years(bits)
    return core_years * CORE_YEAR_SECONDS / RSA_CLASSICAL_PARALLEL_CORES


def rsa_bit_length(row_map: dict[str, str]) -> int | None:
    text = " ".join(
        [
            row_map.get("解ける問題", ""),
            row_map.get("対象サイズ", ""),
            row_map.get("見積もりの種類", ""),
            strip_markdown_links(row_map.get("論文", "")),
        ]
    )
    if not any(token in text for token in ("RSA", "整数の素因数分解", "factoring")):
        return None
    patterns = [
        r"RSA[-–](\d{3,5})",
        r"N\s*=\s*(\d{3,5})\s*bits?",
        r"(\d{3,5})\s*bit\s+RSA",
        r"(\d{3,5})[-\s]*bit\s+integer",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None


def classical_runtime_for_row(row_map: dict[str, str]) -> tuple[float | None, str, str, int | None]:
    reported = parse_optional_float(row_map.get("古典計算時間(s)", "NA"))
    if reported is not None and reported > 0:
        return (
            reported,
            "reported",
            strip_markdown_links(row_map.get("古典計算仮定", "")) or "論文または元データに記載された古典計算時間",
            None,
        )
    bits = rsa_bit_length(row_map)
    if bits is None:
        return None, "", "", None
    runtime = gnfs_rsa_classical_runtime_seconds(bits)
    assumption = (
        f"RSA-{bits} の古典計算時間はGNFS主項 L_N[1/3,(64/9)^(1/3)] を用い、"
        f"RSA-250 ({RSA250_BITS} bits) = {RSA250_CORE_YEARS:g} core-years を基準に外挿し、"
        f"{RSA_CLASSICAL_PARALLEL_CORES:.0e} coresで並列実行した壁時計時間に換算。"
    )
    return runtime, "gnfs-rsa250", assumption, bits


def speedup_reference_values() -> list[dict[str, object]]:
    values: list[dict[str, object]] = []
    for bits in (1024, 2048, 3072, 4096):
        core_years = gnfs_rsa_classical_core_years(bits)
        seconds = gnfs_rsa_classical_runtime_seconds(bits)
        values.append(
            {
                "bits": bits,
                "seconds": seconds,
                "coreYears": core_years,
            }
        )
    return values


def graph_points(header: list[str], rows: list[list[str]]) -> list[dict[str, object]]:
    points: list[dict[str, object]] = []
    for row_index, row in enumerate(rows, start=1):
        row_map = dict(zip(header, row))
        logical = parse_optional_float(row_map.get("論理量子ビット(q)", "NA"))
        toffoli = parse_optional_float(row_map.get("Toffoli数", "NA"))
        t_gates = parse_optional_float(row_map.get("Tゲート数", "NA"))
        other_gates = parse_optional_float(row_map.get("その他論理ゲート数", "NA"))
        if logical is None:
            continue
        source = ""
        y_base = None
        if toffoli is not None:
            source = "toffoli"
            y_base = toffoli
        elif t_gates is not None:
            source = "t"
            y_base = t_gates
        elif other_gates is not None and "CCZ" in (row_map.get("数値根拠", "") + row_map.get("備考", "") + row_map.get("通信・その他仮定", "")):
            source = "ccz"
            y_base = other_gates
        elif other_gates is not None:
            source = "other"
            y_base = other_gates
        if y_base is None:
            continue
        problem = row_map.get("解ける問題", "")
        category = graph_category(problem)
        paper = strip_markdown_links(row_map.get("論文", ""))
        note = strip_markdown_links(row_map.get("備考", ""))
        if paper == "Webster et al. 2026 Table IV" and "Fermi-Hubbard" in problem:
            note = (note + " " if note else "") + (
                "グラフのToffoli換算にはCampbell 2022 Table IIのPLAQ T gates (NT) を用い、"
                "Websterのlogical cycles upper bound 8e6は深さ/サイクルとして別に保持しています。"
            )
        points.append(
            {
                "rowIndex": row_index,
                "date": row_map.get("発表日（初出）", ""),
                "problem": problem,
                "category": category,
                "categoryLabel": graph_category_label(category),
                "paper": paper,
                "paperHref": first_markdown_link(row_map.get("論文", "")),
                "target": row_map.get("対象サイズ", ""),
                "estimateType": row_map.get("見積もりの種類", ""),
                "isExperiment": parse_optional_float(row_map.get("実験実施", "0")) == 1,
                "isSubroutineOnly": is_subroutine_only(row_map),
                "logicalQubits": logical,
                "physicalQubits": parse_optional_float(row_map.get("物理量子ビット(q)", "NA")),
                "toffoliCount": toffoli,
                "tGateCount": t_gates,
                "otherLogicalGateCount": other_gates,
                "toffoliEquivBase": y_base,
                "gateSource": source,
                "runtimeSeconds": parse_optional_float(row_map.get("実行時間(s)", "NA")),
                "device": row_map.get("デバイス", ""),
                "errorCorrectionCode": row_map.get("誤り訂正符号", ""),
                "physicalQubitType": row_map.get("物理量子ビット種", ""),
                "physicalErrorRate": parse_optional_float(row_map.get("物理エラー率(fraction)", "NA")),
                "codeDistance": parse_optional_float(row_map.get("code distance", "NA")),
                "assumptions": strip_markdown_links(row_map.get("通信・その他仮定", "")),
                "evidence": strip_markdown_links(row_map.get("数値根拠", "")),
                "note": note,
            }
        )
    return points


def reported_logical_gate_metric(row_map: dict[str, str]) -> tuple[float | None, str, str]:
    candidates = [
        ("Toffoli数", "toffoli", "Toffoli数"),
        ("Tゲート数", "t", "Tゲート数"),
        ("Cliffordゲート数", "clifford", "Cliffordゲート数"),
        ("その他論理ゲート数", "other", "その他論理ゲート数"),
    ]
    for column, source, label in candidates:
        value = parse_optional_float(row_map.get(column, "NA"))
        if value is not None and value > 0:
            return value, source, label
    return None, "", ""


def physical_graph_points(header: list[str], rows: list[list[str]]) -> list[dict[str, object]]:
    points: list[dict[str, object]] = []
    for row_index, row in enumerate(rows, start=1):
        row_map = dict(zip(header, row))
        physical = parse_optional_float(row_map.get("物理量子ビット(q)", "NA"))
        error_rate = parse_optional_float(row_map.get("物理エラー率(fraction)", "NA"))
        runtime = parse_optional_float(row_map.get("実行時間(s)", "NA"))
        classical_runtime = parse_optional_float(row_map.get("古典計算時間(s)", "NA"))
        reported_ratio = parse_optional_float(row_map.get("古典/量子時間比", "NA"))
        logical_gate_count, logical_gate_source, logical_gate_label = reported_logical_gate_metric(row_map)
        if physical is None or physical <= 0:
            continue
        if (runtime is None or runtime <= 0) and logical_gate_count is None:
            continue
        problem = row_map.get("解ける問題", "")
        points.append(
            {
                "rowIndex": row_index,
                "date": row_map.get("発表日（初出）", ""),
                "problem": problem,
                "category": graph_category(problem),
                "categoryLabel": graph_category_label(graph_category(problem)),
                "paper": strip_markdown_links(row_map.get("論文", "")),
                "paperHref": first_markdown_link(row_map.get("論文", "")),
                "target": row_map.get("対象サイズ", ""),
                "estimateType": row_map.get("見積もりの種類", ""),
                "isExperiment": parse_optional_float(row_map.get("実験実施", "0")) == 1,
                "isSubroutineOnly": is_subroutine_only(row_map),
                "logicalQubits": parse_optional_float(row_map.get("論理量子ビット(q)", "NA")),
                "physicalQubits": physical,
                "physicalErrorRate": error_rate,
                "codeDistance": parse_optional_float(row_map.get("code distance", "NA")),
                "cycleTimeSeconds": parse_optional_float(row_map.get("cycle/測定時間(s)", "NA")),
                "runtimeSeconds": runtime,
                "classicalRuntimeSeconds": classical_runtime,
                "classicalQuantumRuntimeRatio": classical_quantum_runtime_ratio(reported_ratio, classical_runtime, runtime),
                "classicalAssumptions": strip_markdown_links(row_map.get("古典計算仮定", "")),
                "classicalEvidence": strip_markdown_links(row_map.get("古典計算根拠", "")),
                "logicalGateCount": logical_gate_count,
                "logicalGateSource": logical_gate_source,
                "logicalGateLabel": logical_gate_label,
                "toffoliCount": parse_optional_float(row_map.get("Toffoli数", "NA")),
                "tGateCount": parse_optional_float(row_map.get("Tゲート数", "NA")),
                "cliffordGateCount": parse_optional_float(row_map.get("Cliffordゲート数", "NA")),
                "otherLogicalGateCount": parse_optional_float(row_map.get("その他論理ゲート数", "NA")),
                "spacetimeVolumeQubitDays": parse_optional_float(row_map.get("時空間体積(qubit-days)", "NA")),
                "device": row_map.get("デバイス", ""),
                "errorCorrectionCode": row_map.get("誤り訂正符号", ""),
                "physicalQubitType": row_map.get("物理量子ビット種", ""),
                "assumptions": strip_markdown_links(row_map.get("通信・その他仮定", "")),
                "evidence": strip_markdown_links(row_map.get("数値根拠", "")),
                "note": strip_markdown_links(row_map.get("備考", "")),
            }
        )
    return points


def speedup_graph_points(header: list[str], rows: list[list[str]]) -> list[dict[str, object]]:
    points: list[dict[str, object]] = []
    for row_index, row in enumerate(rows, start=1):
        row_map = dict(zip(header, row))
        physical = parse_optional_float(row_map.get("物理量子ビット(q)", "NA"))
        error_rate = parse_optional_float(row_map.get("物理エラー率(fraction)", "NA"))
        quantum_runtime = parse_optional_float(row_map.get("実行時間(s)", "NA"))
        if (
            physical is None
            or physical <= 0
            or error_rate is None
            or error_rate <= 0
            or quantum_runtime is None
            or quantum_runtime <= 0
        ):
            continue
        classical_runtime, source, assumption, rsa_bits = classical_runtime_for_row(row_map)
        reported_ratio = parse_optional_float(row_map.get("古典/量子時間比", "NA"))
        ratio = classical_quantum_runtime_ratio(reported_ratio, classical_runtime, quantum_runtime)
        if ratio is None or ratio <= 0:
            continue
        problem = row_map.get("解ける問題", "")
        points.append(
            {
                "rowIndex": row_index,
                "date": row_map.get("発表日（初出）", ""),
                "problem": problem,
                "category": graph_category(problem),
                "categoryLabel": graph_category_label(graph_category(problem)),
                "paper": strip_markdown_links(row_map.get("論文", "")),
                "paperHref": first_markdown_link(row_map.get("論文", "")),
                "target": row_map.get("対象サイズ", ""),
                "estimateType": row_map.get("見積もりの種類", ""),
                "isExperiment": parse_optional_float(row_map.get("実験実施", "0")) == 1,
                "isSubroutineOnly": is_subroutine_only(row_map),
                "logicalQubits": parse_optional_float(row_map.get("論理量子ビット(q)", "NA")),
                "physicalQubits": physical,
                "physicalErrorRate": error_rate,
                "devicePerformance": physical / error_rate,
                "quantumRuntimeSeconds": quantum_runtime,
                "classicalRuntimeSeconds": classical_runtime,
                "classicalQuantumRuntimeRatio": ratio,
                "classicalRuntimeSource": source,
                "rsaBits": rsa_bits,
                "codeDistance": parse_optional_float(row_map.get("code distance", "NA")),
                "cycleTimeSeconds": parse_optional_float(row_map.get("cycle/測定時間(s)", "NA")),
                "device": row_map.get("デバイス", ""),
                "errorCorrectionCode": row_map.get("誤り訂正符号", ""),
                "physicalQubitType": row_map.get("物理量子ビット種", ""),
                "assumptions": strip_markdown_links(row_map.get("通信・その他仮定", "")),
                "classicalAssumptions": assumption,
                "classicalEvidence": strip_markdown_links(row_map.get("古典計算根拠", "")),
                "evidence": strip_markdown_links(row_map.get("数値根拠", "")),
                "note": strip_markdown_links(row_map.get("備考", "")),
            }
        )
    return points


def build_speedup_graph_html(base: Path, header: list[str], rows: list[list[str]]) -> str:
    points_json = json.dumps(speedup_graph_points(header, rows), ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    refs_json = json.dumps(speedup_reference_values(), ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    css = """
html{box-sizing:border-box;overflow-x:hidden}*,*:before,*:after{box-sizing:inherit}body{margin:0;overflow-x:hidden;background:#f7f7f5;color:#17202f;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;line-height:1.5}.page{min-height:100vh;width:100%;max-width:100vw;overflow-x:hidden;padding:22px clamp(14px,2.4vw,34px)}.topbar{display:flex;align-items:flex-end;justify-content:space-between;gap:18px;margin:0 0 14px;width:100%;min-width:0}.title{margin:0;font-size:24px;letter-spacing:0}.subtitle{margin:4px 0 0;color:#667085;font-size:13px;overflow-wrap:anywhere}.controls{display:flex;flex-wrap:wrap;align-items:center;gap:10px;max-width:100%}.action,.check{border:1px solid #cfd6e2;border-radius:8px;background:#fff;color:#344054;font:inherit;font-size:13px}.action{padding:8px 10px;cursor:pointer}.action:hover{border-color:#98a2b3;background:#f8fafc}.check{display:inline-flex;align-items:center;gap:6px;padding:7px 9px;white-space:nowrap}.check input{margin:0}.marker{display:inline-block;width:11px;height:11px;flex:0 0 auto}.marker.chemistry{background:#b6423a;border-radius:2px}.marker.crypto{background:#2454a6;border-radius:50%}.marker.other{width:0;height:0;border-left:6px solid transparent;border-right:6px solid transparent;border-bottom:11px solid #d39b18}.layout{display:grid;grid-template-columns:minmax(0,1fr) 370px;gap:14px;align-items:start;width:100%;min-width:0}.chart-card,.side{max-width:100%;background:#fff;border:1px solid #d6d6d6;border-radius:8px}.chart-card{min-width:0;overflow:hidden}.chart-wrap{position:relative;height:calc(100vh - 168px);min-height:560px}.chart{display:block;width:100%;height:100%;touch-action:none}.plot-bg{fill:#fff}.axis-label{fill:#111827;font-size:14px;font-weight:700}.tick text{fill:#374151;font-size:12px}.tick line{stroke:#e7e7e7;stroke-width:1}.runtime-guide line{stroke:#5f6b7a;stroke-width:1.15;stroke-dasharray:4 5;opacity:.72}.runtime-guide text{fill:#344054;font-size:12px;font-weight:650;paint-order:stroke;stroke:#fff;stroke-width:3px}.domain{stroke:#111827;stroke-width:1.35}.point{cursor:pointer;stroke:#fff;stroke-width:1.5;opacity:.9}.point.is-experiment{stroke:#111827;stroke-width:3;opacity:1}.point.is-hovered,.point.is-pinned{stroke:#111827;stroke-width:2.5;opacity:1}.ratio-one{stroke:#7a8699;stroke-width:1.2;stroke-dasharray:5 5}.ratio-one-label{fill:#667085;font-size:12px}.side{padding:14px;min-height:360px}.side h2{margin:0 0 8px;font-size:16px}.side h3{margin:16px 0 6px;font-size:14px}.side p{margin:8px 0;color:#475467;font-size:13px}.side ul{margin:8px 0 0;padding-left:18px;color:#475467;font-size:13px}.side li{margin:6px 0}.side a{color:#184e77;text-decoration-thickness:1px;text-underline-offset:2px}.formula{display:block;overflow:auto;background:#f8fafc;border:1px solid #e4e7ec;border-radius:6px;padding:8px;font-size:12px;color:#344054;white-space:nowrap}.ref-table{width:100%;border-collapse:collapse;margin-top:8px;font-size:12px}.ref-table th,.ref-table td{border-bottom:1px solid #e4e7ec;padding:5px 4px;text-align:right}.ref-table th:first-child,.ref-table td:first-child{text-align:left}.tooltip{position:fixed;z-index:20;width:min(440px,calc(100vw - 24px));max-height:calc(100vh - 24px);overflow:auto;display:none;background:#fff;border:1px solid #aeb8c8;border-radius:8px;box-shadow:0 18px 48px rgba(20,31,50,.24);padding:12px;pointer-events:auto}.tooltip.is-open{display:block}.tooltip.is-pinned{border-color:#2454a6}.tip-header{display:flex;align-items:flex-start;justify-content:space-between;gap:10px;margin:0 0 6px}.tip-title{font-weight:700;margin:0;min-width:0}.tip-title a{color:#2454a6;text-decoration-thickness:1px;text-underline-offset:2px}.tip-close{flex:0 0 auto;width:26px;height:26px;border:1px solid #cfd6e2;border-radius:50%;background:#fff;color:#344054;font-size:18px;line-height:20px;cursor:pointer}.tip-close:hover{background:#f8fafc;border-color:#98a2b3}.tip-grid{display:grid;grid-template-columns:140px 1fr;gap:4px 8px;font-size:12px}.tip-grid dt{color:#667085}.tip-grid dd{margin:0;color:#17202f;overflow-wrap:anywhere}.tip-note{margin:8px 0 0;color:#475467;font-size:12px;white-space:normal;overflow-wrap:anywhere}.empty{display:none;position:absolute;inset:0;align-items:center;justify-content:center;color:#667085;font-size:14px}.empty.is-open{display:flex}.footer-note{max-width:1120px;margin:14px 0 0;color:#667085;font-size:12px}@media(max-width:1240px){.topbar{align-items:flex-start;flex-direction:column}.topbar>div{min-width:0;max-width:100%}.layout{grid-template-columns:minmax(0,1fr)}.side{max-width:none}.page{overflow-x:hidden}}@media(max-width:720px){.page{padding:16px 10px}.chart-card,.side{border-radius:6px}.chart-wrap{height:62vh;min-height:430px}.title{font-size:21px}.controls{display:grid;grid-template-columns:minmax(0,1fr);gap:8px;width:100%;align-items:stretch}.action,.check{justify-content:center;min-width:0;font-size:12px;white-space:normal}.check{justify-content:flex-start}.side{min-width:0}.axis-label{font-size:13px}.tick text{font-size:11px}.tip-grid{grid-template-columns:118px 1fr}}
"""
    css += "\n.point.is-experiment{stroke:#111827;stroke-width:3;opacity:1}\n"
    script = f"""
<script>
const DATA = {points_json};
const REFS = {refs_json};
const Y_DISPLAY_MAX = 1e25;
const colors = {{ chemistry: "#b6423a", crypto: "#2454a6", other: "#d39b18" }};
const state = {{ categories: new Set(["chemistry","crypto","other"]) }};
const svg = document.querySelector(".chart");
const plot = document.querySelector(".plot");
const tooltip = document.querySelector(".tooltip");
const empty = document.querySelector(".empty");
const refTableBody = document.querySelector("[data-ref-table]");
let tooltipHideTimer;
let pinnedTip = false;
function esc(value) {{
  return String(value ?? "").replace(/[&<>"']/g, ch => ({{"&":"&amp;","<":"&lt;",">":"&gt;","\\"":"&quot;","'":"&#39;"}}[ch]));
}}
function fmt(x) {{
  if (x == null || Number.isNaN(x)) return "NA";
  if (x === 0) return "0";
  const ax = Math.abs(x);
  if (ax >= 1e4 || ax < 1e-2) return x.toExponential(2).replace(/\\.0+e/,"e").replace(/(\\.\\d*?)0+e/,"$1e");
  return new Intl.NumberFormat("en-US", {{ maximumSignificantDigits: 3 }}).format(x);
}}
function fmtDuration(seconds) {{
  if (seconds == null || Number.isNaN(seconds) || !Number.isFinite(seconds)) return "NA";
  const abs = Math.abs(seconds);
  if (abs < 60) return `${{fmt(seconds)}} s`;
  if (abs < 3600) return `${{fmt(seconds / 60)}} min`;
  if (abs < 86400) return `${{fmt(seconds / 3600)}} h`;
  if (abs < 31557600) return `${{fmt(seconds / 86400)}} day`;
  return `${{fmt(seconds / 31557600)}} year`;
}}
function fmtCoreYears(coreYears) {{
  return `${{fmt(coreYears)}} core-year`;
}}
function log10(x) {{ return Math.log(x) / Math.LN10; }}
function powTickLabel(value, attrs) {{
  const exponent = Math.round(log10(value));
  return `<text ${{attrs}}>10<tspan baseline-shift="super" font-size="8">${{exponent}}</tspan></text>`;
}}
function nicePow(min, max) {{
  const lo = Math.floor(log10(min));
  const hi = Math.ceil(log10(max));
  return [Math.pow(10, lo), Math.pow(10, hi), lo, hi];
}}
function ticks(lo, hi) {{
  const out = [];
  for (let e = lo; e <= hi; e++) out.push(Math.pow(10, e));
  return out;
}}
function pointClass(d) {{
  return "point" + (d.isExperiment ? " is-experiment" : "") + (d.isSubroutineOnly ? " is-subroutine" : "");
}}
function categoryShape(d, x, y, r) {{
  const cls = pointClass(d);
  if (d.isSubroutineOnly) return `<path class="${{cls}}" d="M ${{x}} ${{y-r}} L ${{x+r}} ${{y}} L ${{x}} ${{y+r}} L ${{x-r}} ${{y}} Z"></path>`;
  if (d.category === "crypto") return `<circle class="${{cls}}" cx="${{x}}" cy="${{y}}" r="${{r}}"></circle>`;
  if (d.category === "chemistry") return `<rect class="${{cls}}" x="${{x-r}}" y="${{y-r}}" width="${{2*r}}" height="${{2*r}}" rx="2"></rect>`;
  return `<path class="${{cls}}" d="M ${{x}} ${{y-r}} L ${{x+r}} ${{y+r}} L ${{x-r}} ${{y+r}} Z"></path>`;
}}
function legendShape(kind, x, y, color) {{
  if (kind === "crypto") return `<circle cx="${{x}}" cy="${{y}}" r="5.5" fill="${{color}}" stroke="${{color}}" stroke-width="1.4"></circle>`;
  if (kind === "chemistry") return `<rect x="${{x-5.5}}" y="${{y-5.5}}" width="11" height="11" rx="2" fill="${{color}}" stroke="${{color}}" stroke-width="1.4"></rect>`;
  if (kind === "subroutine") return `<path d="M ${{x}} ${{y-6.5}} L ${{x+6.5}} ${{y}} L ${{x}} ${{y+6.5}} L ${{x-6.5}} ${{y}} Z" fill="#fff" stroke="${{color}}" stroke-width="2.2"></path>`;
  if (kind === "experiment") return `<circle cx="${{x}}" cy="${{y}}" r="6" fill="#fff" stroke="#111827" stroke-width="3"></circle>`;
  return `<path d="M ${{x}} ${{y-6}} L ${{x+6.5}} ${{y+6}} L ${{x-6.5}} ${{y+6}} Z" fill="${{color}}" stroke="${{color}}" stroke-width="1.4"></path>`;
}}
function renderSvgLegend(x, y, isNarrow, data) {{
  const entries = [
    ["chemistry", "量子化学・量子シミュレーション", colors.chemistry],
    ["crypto", "素因数分解・暗号系", colors.crypto],
    ["other", "その他", colors.other],
  ].filter(([kind]) => state.categories.has(kind) && data.some(d => d.category === kind));
  if (data.some(d => d.isSubroutineOnly)) entries.push(["subroutine", "サブルーチンのみ", "#475467"]);
  if (data.some(d => d.isExperiment)) entries.push(["experiment", "実験実現あり", "#111827"]);
  if (!entries.length) return "";
  const rowH = 18;
  const width = isNarrow ? 204 : 268;
  const height = 14 + entries.length * rowH;
  let html = `<g class="svg-legend" pointer-events="none"><rect class="svg-legend-bg" x="${{x}}" y="${{y}}" width="${{width}}" height="${{height}}" rx="6" fill="#fff" fill-opacity=".94" stroke="#d0d5dd" stroke-width="1"></rect>`;
  entries.forEach((entry, i) => {{
    const [kind, label, color] = entry;
    const yy = y + 17 + i * rowH;
    const labelText = isNarrow && label.length > 12 ? label.replace("・量子シミュレーション", "") : label;
    html += `<g class="svg-legend-row">${{legendShape(kind, x + 15, yy - 3, color)}}<text x="${{x + 30}}" y="${{yy + 1}}" fill="#344054" font-size="12" font-weight="650" font-family="-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif">${{labelText}}</text></g>`;
  }});
  return html + `</g>`;
}}
function visibleData() {{
  return DATA.filter(d =>
    state.categories.has(d.category) &&
    d.physicalQubits > 0 &&
    d.physicalErrorRate > 0 &&
    d.devicePerformance > 0 &&
    d.classicalQuantumRuntimeRatio > 0 &&
    d.classicalQuantumRuntimeRatio <= Y_DISPLAY_MAX
  );
}}
function renderReferenceTable() {{
  refTableBody.innerHTML = REFS.map(r => `<tr><td>RSA-${{r.bits}}</td><td>${{fmtCoreYears(r.coreYears)}}</td><td>${{fmtDuration(r.seconds)}}</td></tr>`).join("");
}}
function render() {{
  const rect = svg.getBoundingClientRect();
  const width = Math.max(320, rect.width || 900);
  const height = Math.max(520, rect.height || 620);
  svg.setAttribute("viewBox", `0 0 ${{width}} ${{height}}`);
  const isNarrow = width <= 520;
  const margin = {{ left: isNarrow ? 74 : 90, right: isNarrow ? 34 : 34, top: 28, bottom: 76 }};
  const innerW = width - margin.left - margin.right;
  const innerH = height - margin.top - margin.bottom;
  const data = visibleData();
  empty.classList.toggle("is-open", data.length === 0);
  if (!data.length) {{ plot.innerHTML = ""; return; }}
  const [xMin,xMax,xLo,xHi] = nicePow(Math.min(...data.map(d=>d.devicePerformance)), Math.max(...data.map(d=>d.devicePerformance)));
  const [yMin,yMax,yLo,yHi] = nicePow(Math.min(...data.map(d=>d.classicalQuantumRuntimeRatio)), Math.max(...data.map(d=>d.classicalQuantumRuntimeRatio)));
  const sx = v => margin.left + (log10(v) - log10(xMin)) / (log10(xMax) - log10(xMin)) * innerW;
  const sy = v => margin.top + innerH - (log10(v) - log10(yMin)) / (log10(yMax) - log10(yMin)) * innerH;
  let html = `<rect class="plot-bg" x="0" y="0" width="${{width}}" height="${{height}}"></rect>`;
  for (const t of ticks(xLo, xHi)) {{
    const x = sx(t);
    html += `<g class="tick"><line x1="${{x}}" x2="${{x}}" y1="${{margin.top}}" y2="${{margin.top+innerH}}"></line>${{powTickLabel(t, `x="${{x}}" y="${{margin.top+innerH+24}}" text-anchor="middle"`)}}</g>`;
  }}
  for (const t of ticks(yLo, yHi)) {{
    const y = sy(t);
    html += `<g class="tick"><line x1="${{margin.left}}" x2="${{margin.left+innerW}}" y1="${{y}}" y2="${{y}}"></line>${{powTickLabel(t, `x="${{margin.left-10}}" y="${{y+4}}" text-anchor="end"`)}}</g>`;
  }}
  if (yMin <= 1 && yMax >= 1) {{
    const y = sy(1);
    html += `<line class="ratio-one" x1="${{margin.left}}" x2="${{margin.left+innerW}}" y1="${{y}}" y2="${{y}}"></line>`;
    html += `<text class="ratio-one-label" x="${{margin.left+innerW-6}}" y="${{y-7}}" text-anchor="end">古典=量子</text>`;
  }}
  html += `<rect class="domain" x="${{margin.left}}" y="${{margin.top}}" width="${{innerW}}" height="${{innerH}}" fill="none"></rect>`;
  html += `<text class="axis-label" x="${{margin.left + innerW/2}}" y="${{height-24}}" text-anchor="middle">物理量子ビット数 / 物理エラー率</text>`;
  html += `<text class="axis-label" transform="translate(26 ${{margin.top + innerH/2}}) rotate(-90)" text-anchor="middle">古典計算時間 / 量子計算時間</text>`;
  data.forEach(d => {{
    const x = sx(d.devicePerformance);
    const y = sy(d.classicalQuantumRuntimeRatio);
    const r = d.isExperiment ? 8 : 6.4;
    html += `<g data-i="${{DATA.indexOf(d)}}" style="fill:${{colors[d.category] || colors.other}}">${{categoryShape(d,x,y,r)}}</g>`;
  }});
  html += renderSvgLegend(margin.left + 12, margin.top + 12, isNarrow, data);
  plot.innerHTML = html;
  plot.querySelectorAll("g[data-i]").forEach(g => {{
    g.addEventListener("mouseenter", e => showTip(DATA[+g.dataset.i], e));
    g.addEventListener("mousemove", e => {{ if (!pinnedTip) positionTip(e); }});
    g.addEventListener("mouseleave", hideTip);
    g.addEventListener("focusin", e => showTip(DATA[+g.dataset.i], e));
    g.addEventListener("click", e => pinTip(DATA[+g.dataset.i], e));
    g.setAttribute("tabindex", "0");
  }});
}}
function clearPinnedPoint() {{
  document.querySelectorAll(".point.is-pinned").forEach(point => point.classList.remove("is-pinned"));
}}
function setPinnedPoint(d) {{
  clearPinnedPoint();
  const index = DATA.indexOf(d);
  document.querySelectorAll(`g[data-i="${{index}}"] .point`).forEach(point => point.classList.add("is-pinned"));
}}
function pinTip(d, event) {{
  event.preventDefault();
  event.stopPropagation();
  pinnedTip = true;
  setPinnedPoint(d);
  showTip(d, event, true);
}}
function closeTip() {{
  pinnedTip = false;
  clearPinnedPoint();
  tooltip.classList.remove("is-open", "is-pinned");
}}
function showTip(d, event, force = false) {{
  if (pinnedTip && !force) return;
  clearTimeout(tooltipHideTimer);
  const paperTitle = d.paperHref
    ? `<a href="${{esc(d.paperHref)}}" target="_blank" rel="noopener">${{esc(d.paper)}}</a>`
    : esc(d.paper);
  const source = d.classicalRuntimeSource === "gnfs-rsa250" ? `GNFS外挿 (RSA-${{d.rsaBits}})` : "元データ/論文記載";
  tooltip.innerHTML = `<div class="tip-header"><p class="tip-title">${{paperTitle}}</p><button type="button" class="tip-close" data-close-tip aria-label="詳細を閉じる">×</button></div>
    <dl class="tip-grid">
      <dt>分類</dt><dd>${{esc(d.categoryLabel)}}</dd>
      <dt>問題</dt><dd>${{esc(d.problem)}}</dd>
      <dt>対象</dt><dd>${{esc(d.target)}}</dd>
      <dt>見積もり</dt><dd>${{esc(d.estimateType)}}</dd>
      <dt>実験実施</dt><dd>${{d.isExperiment ? "あり" : "なし"}}</dd>
      <dt>物理量子ビット</dt><dd>${{fmt(d.physicalQubits)}}</dd>
      <dt>物理量子ビット/物理エラー率</dt><dd>${{fmt(d.devicePerformance)}}</dd>
      <dt>量子計算時間</dt><dd>${{fmtDuration(d.quantumRuntimeSeconds)}}</dd>
      <dt>古典計算時間</dt><dd>${{fmtDuration(d.classicalRuntimeSeconds)}}</dd>
      <dt>古典/量子比</dt><dd>${{fmt(d.classicalQuantumRuntimeRatio)}}</dd>
      <dt>古典時間の扱い</dt><dd>${{esc(source)}}</dd>
      <dt>物理エラー率</dt><dd>${{fmt(d.physicalErrorRate)}}</dd>
      <dt>cycle/測定時間</dt><dd>${{fmt(d.cycleTimeSeconds)}}</dd>
      <dt>デバイス</dt><dd>${{esc(d.device || "NA")}}</dd>
      <dt>誤り訂正符号</dt><dd>${{esc(d.errorCorrectionCode || "NA")}}</dd>
      <dt>物理量子ビット種</dt><dd>${{esc(d.physicalQubitType || "NA")}}</dd>
    </dl>
    <p class="tip-note">${{esc(d.classicalAssumptions || d.note || d.evidence || "")}}</p>`;
  tooltip.classList.add("is-open");
  tooltip.classList.toggle("is-pinned", pinnedTip);
  positionTip(event);
}}
function positionTip(event) {{
  const pad = 12;
  const box = tooltip.getBoundingClientRect();
  let x = event.clientX + 14;
  let y = event.clientY + 14;
  if (x + box.width + pad > window.innerWidth) x = event.clientX - box.width - 14;
  if (y + box.height + pad > window.innerHeight) y = event.clientY - box.height - 14;
  tooltip.style.left = Math.max(pad, x) + "px";
  tooltip.style.top = Math.max(pad, y) + "px";
}}
function hideTip() {{
  if (pinnedTip) return;
  clearTimeout(tooltipHideTimer);
  tooltipHideTimer = setTimeout(() => tooltip.classList.remove("is-open"), 180);
}}
function downloadBlob(blob, filename) {{
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 500);
}}
function graphSvgSource() {{
  render();
  const clone = svg.cloneNode(true);
  const viewBox = svg.getAttribute("viewBox") || "0 0 1200 720";
  const parts = viewBox.split(/\\s+/).map(Number);
  clone.setAttribute("xmlns", "http://www.w3.org/2000/svg");
  clone.setAttribute("width", String(parts[2] || 1200));
  clone.setAttribute("height", String(parts[3] || 720));
  const style = document.createElementNS("http://www.w3.org/2000/svg", "style");
  style.textContent = `.plot-bg{{fill:#fff}}.axis-label{{fill:#111827;font:700 14px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}.tick text{{fill:#374151;font:12px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}.tick line{{stroke:#e7e7e7;stroke-width:1}}.runtime-guide line{{stroke:#5f6b7a;stroke-width:1.15;stroke-dasharray:4 5;opacity:.72}}.runtime-guide text{{fill:#344054;font:650 12px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;paint-order:stroke;stroke:#fff;stroke-width:3px}}.domain{{stroke:#111827;stroke-width:1.35}}.point{{stroke:#fff;stroke-width:1.5;opacity:.9}}.point.is-experiment{{stroke:#111827;stroke-width:3;opacity:1}}.ratio-one{{stroke:#7a8699;stroke-width:1.2;stroke-dasharray:5 5}}.ratio-one-label{{fill:#667085;font:12px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}`;
  clone.insertBefore(style, clone.firstChild);
  return new XMLSerializer().serializeToString(clone);
}}
function downloadGraph(format) {{
  const source = graphSvgSource();
  const svgBlob = new Blob([source], {{ type: "image/svg+xml;charset=utf-8" }});
  if (format === "svg") {{
    downloadBlob(svgBlob, "quantum_resource_estimates_speedup_graph.svg");
    return;
  }}
  const url = URL.createObjectURL(svgBlob);
  const image = new Image();
  image.onload = () => {{
    const viewBox = svg.getAttribute("viewBox") || "0 0 1200 720";
    const parts = viewBox.split(/\\s+/).map(Number);
    const width = parts[2] || image.width || 1200;
    const height = parts[3] || image.height || 720;
    const scale = 2;
    const canvas = document.createElement("canvas");
    canvas.width = Math.round(width * scale);
    canvas.height = Math.round(height * scale);
    const ctx = canvas.getContext("2d");
    ctx.fillStyle = "#fff";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(image, 0, 0, canvas.width, canvas.height);
    canvas.toBlob(blob => {{
      if (blob) downloadBlob(blob, "quantum_resource_estimates_speedup_graph.png");
      URL.revokeObjectURL(url);
    }}, "image/png");
  }};
  image.onerror = () => URL.revokeObjectURL(url);
  image.src = url;
}}
function tsvEscape(value) {{
  return String(value ?? "NA").replace(/[\\t\\r\\n]+/g, " ").trim();
}}
function downloadCurrentTsv() {{
  const header = ["date","category","problem","paper","paper_url","target","estimate_type","is_experiment","physical_qubits","physical_error_rate","device_performance_physical_qubits_per_error_rate","quantum_runtime_seconds","classical_runtime_seconds","classical_quantum_runtime_ratio","classical_runtime_source","rsa_bits","device","error_correction_code","physical_qubit_type","note"];
  const rows = visibleData().map(d => [d.date,d.categoryLabel,d.problem,d.paper,d.paperHref,d.target,d.estimateType,d.isExperiment ? 1 : 0,d.physicalQubits,d.physicalErrorRate,d.devicePerformance,d.quantumRuntimeSeconds,d.classicalRuntimeSeconds,d.classicalQuantumRuntimeRatio,d.classicalRuntimeSource,d.rsaBits,d.device,d.errorCorrectionCode,d.physicalQubitType,d.classicalAssumptions || d.note || d.evidence || ""]);
  const text = [header, ...rows].map(row => row.map(tsvEscape).join("\\t")).join("\\n") + "\\n";
  downloadBlob(new Blob([text], {{ type: "text/tab-separated-values;charset=utf-8" }}), "quantum_resource_estimates_speedup_graph_data.tsv");
}}
tooltip.addEventListener("mouseenter", () => clearTimeout(tooltipHideTimer));
tooltip.addEventListener("mouseleave", hideTip);
tooltip.addEventListener("click", event => {{
  if (event.target.closest("[data-close-tip]")) closeTip();
}});
document.querySelectorAll("[data-download]").forEach(btn => {{
  btn.addEventListener("click", () => downloadGraph(btn.dataset.download));
}});
document.querySelector("[data-download-tsv]")?.addEventListener("click", downloadCurrentTsv);
document.querySelectorAll("[data-category]").forEach(input => {{
  input.addEventListener("change", () => {{
    if (input.checked) state.categories.add(input.dataset.category);
    else state.categories.delete(input.dataset.category);
    render();
  }});
}});
window.addEventListener("resize", render);
renderReferenceTable();
render();
</script>
"""
    return f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>量子・古典計算時間比と生デバイス性能指標</title>
<style>{css}</style>
</head>
<body>
<main class="page">
  <div class="topbar">
    <div>
      <h1 class="title">量子・古典計算時間比と生デバイス性能指標</h1>
      <p class="subtitle">{AI_EXTRACTION_NOTICE}</p>
      <p class="subtitle">横軸は物理量子ビット数 / 物理エラー率、縦軸は古典計算時間 / 量子計算時間です。RSA系の古典時間はGNFS主項をRSA-250実績に合わせて外挿しています。</p>
    </div>
    <div class="controls" aria-label="graph controls">
      <button type="button" class="action" data-download="svg">SVG保存</button>
      <button type="button" class="action" data-download="png">PNG保存</button>
      <button type="button" class="action" data-download-tsv>TSV保存</button>
      <label class="check"><input type="checkbox" data-category="chemistry" checked><span class="marker chemistry"></span>量子化学・量子シミュレーション</label>
      <label class="check"><input type="checkbox" data-category="crypto" checked><span class="marker crypto"></span>素因数分解・暗号系</label>
      <label class="check"><input type="checkbox" data-category="other" checked><span class="marker other"></span>その他</label>
      <span class="legend-key"><span class="marker subroutine"></span>サブルーチンのみ</span>
    </div>
  </div>
  <div class="layout">
    <section class="chart-card" aria-label="device performance and classical quantum runtime ratio scatter plot">
      <div class="chart-wrap">
        <svg class="chart" role="img" aria-label="物理量子ビット数/物理エラー率と古典計算時間/量子計算時間比の散布図"><g class="plot"></g></svg>
        <div class="empty">表示できる点がありません。</div>
      </div>
    </section>
    <aside class="side">
      <h2>RSA古典時間の概算</h2>
      <p>RSA系の古典計算時間は、General Number Field Sieve (GNFS) の主項を使って概算しています。RSA modulusのbit長を b とし、N ≃ 2^b と近似します。</p>
      <code class="formula">C(b)=exp(c(b log 2)^(1/3)(log(b log 2))^(2/3)), c=(64/9)^(1/3)</code>
      <p>基準点は <a href="{RSA250_SOURCE_URL}" target="_blank" rel="noopener">RSA-250 の分解実績</a>です。RSA-250 は250 decimal digits、約829 bitsで、公開報告の約2700 core-yearsを T_829 として使います。</p>
      <code class="formula">T_b = 2700 core-years × C(b)/C(829)</code>
      <p>グラフの古典計算時間は、このcore-year値を100万 coreで並列実行した壁時計時間として秒へ換算しています。実際の古典実行時間は実装、ハードウェア、並列化、メモリ、線形代数部の扱いで変わります。</p>
      <h3>参考値</h3>
      <table class="ref-table">
        <thead><tr><th>bit長</th><th>core-years</th><th>100万 core 秒換算</th></tr></thead>
        <tbody data-ref-table></tbody>
      </table>
      <h3>表示する点</h3>
      <ul>
        <li>量子計算時間、物理量子ビット数、物理エラー率がある行だけを表示します。</li>
        <li>RSA系は上記GNFS外挿で古典時間を生成します。</li>
        <li>RSA以外は、元データに古典計算時間または古典/量子時間比がある場合だけ表示します。</li>
        <li>黒い太枠で強調した点は、元論文で実際に実験として実施されたエントリです。</li>
      </ul>
      <p>横軸は誤り訂正前の生デバイス性能を粗く表す補助指標として、物理量子ビット数を物理エラー率で割った値を使っています。誤り訂正なしのランダム量子回路サンプリング実験では、論文記載の代表的な同時2量子ビットゲートエラーを物理エラー率として使っています。点にマウスを合わせると詳細を表示し、クリックすると表示を固定できます。固定表示は×ボタンで閉じられます。</p>
    </aside>
  </div>
  <p class="footer-note">注: この図は古典/量子の大まかな速度比を見るための補助図です。RSAの古典時間は論文記載値ではなく、GNFS漸近主項をRSA-250実績に正規化した概算です。縦軸は10^25で表示を打ち切り、これを超える点は非表示にしています。縦軸の下限は表示対象データに合わせて自動で決まります。</p>
</main>
<div class="tooltip" role="tooltip"></div>
{script}
</body>
</html>
"""


def build_physical_graph_html(base: Path, header: list[str], rows: list[list[str]]) -> str:
    points_json = json.dumps(physical_graph_points(header, rows), ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    css = """
html{box-sizing:border-box;overflow-x:hidden}*,*:before,*:after{box-sizing:inherit}body{margin:0;overflow-x:hidden;background:#f7f7f5;color:#17202f;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;line-height:1.5}.page{min-height:100vh;width:100%;max-width:100vw;overflow-x:hidden;padding:22px clamp(14px,2.4vw,34px)}.topbar{display:flex;align-items:flex-end;justify-content:space-between;gap:18px;margin:0 0 14px;width:100%;min-width:0}.title{margin:0;font-size:24px;letter-spacing:0}.subtitle{margin:4px 0 0;color:#667085;font-size:13px;overflow-wrap:anywhere;word-break:break-all}.controls{display:flex;flex-wrap:wrap;align-items:center;gap:10px;max-width:100%}.action,.check{border:1px solid #cfd6e2;border-radius:8px;background:#fff;color:#344054;font:inherit;font-size:13px}.action{padding:8px 10px;cursor:pointer}.action:hover{border-color:#98a2b3;background:#f8fafc}.check{display:inline-flex;align-items:center;gap:6px;padding:7px 9px;white-space:nowrap}.check input{margin:0}.marker{display:inline-block;width:11px;height:11px;flex:0 0 auto}.marker.chemistry{background:#b6423a;border-radius:2px}.marker.crypto{background:#2454a6;border-radius:50%}.marker.other{width:0;height:0;border-left:6px solid transparent;border-right:6px solid transparent;border-bottom:11px solid #d39b18}.layout{display:grid;grid-template-columns:minmax(0,1fr) 340px;gap:14px;align-items:start;width:100%;min-width:0}.chart-stack{display:grid;gap:14px;min-width:0}.chart-card,.side{max-width:100%;background:#fff;border:1px solid #d6d6d6;border-radius:8px}.chart-card{min-width:0;overflow:hidden}.chart-heading{margin:14px 16px 0;font-size:15px}.chart-note{margin:4px 16px 0;color:#667085;font-size:12px}.chart-wrap{position:relative;height:calc(100vh - 188px);min-height:500px}.chart{display:block;width:100%;height:100%;touch-action:none}.plot-bg{fill:#fff}.axis-label{fill:#111827;font-size:14px;font-weight:700}.tick text{fill:#374151;font-size:12px}.tick line{stroke:#e7e7e7;stroke-width:1}.domain{stroke:#111827;stroke-width:1.35}.point{cursor:pointer;stroke:#fff;stroke-width:1.5;opacity:.88}.point.is-hovered,.point.is-pinned{stroke:#111827;stroke-width:2.5;opacity:1}.side{padding:14px;min-height:360px}.side h2{margin:0 0 8px;font-size:16px}.side p{margin:8px 0;color:#475467;font-size:13px}.side ul{margin:8px 0 0;padding-left:18px;color:#475467;font-size:13px}.side li{margin:6px 0}.side a{color:#184e77;text-decoration-thickness:1px;text-underline-offset:2px}.tooltip{position:fixed;z-index:20;width:min(430px,calc(100vw - 24px));max-height:calc(100vh - 24px);overflow:auto;display:none;background:#fff;border:1px solid #aeb8c8;border-radius:8px;box-shadow:0 18px 48px rgba(20,31,50,.24);padding:12px;pointer-events:auto}.tooltip.is-open{display:block}.tooltip.is-pinned{border-color:#2454a6}.tip-header{display:flex;align-items:flex-start;justify-content:space-between;gap:10px;margin:0 0 6px}.tip-title{font-weight:700;margin:0;min-width:0}.tip-title a{color:#2454a6;text-decoration-thickness:1px;text-underline-offset:2px}.tip-close{flex:0 0 auto;width:26px;height:26px;border:1px solid #cfd6e2;border-radius:50%;background:#fff;color:#344054;font-size:18px;line-height:20px;cursor:pointer}.tip-close:hover{background:#f8fafc;border-color:#98a2b3}.tip-grid{display:grid;grid-template-columns:132px 1fr;gap:4px 8px;font-size:12px}.tip-grid dt{color:#667085}.tip-grid dd{margin:0;color:#17202f;overflow-wrap:anywhere}.tip-note{margin:8px 0 0;color:#475467;font-size:12px;white-space:normal;overflow-wrap:anywhere}.empty{display:none;position:absolute;inset:0;align-items:center;justify-content:center;color:#667085;font-size:14px}.empty.is-open{display:flex}.footer-note{max-width:1120px;margin:14px 0 0;color:#667085;font-size:12px}@media(max-width:1240px){.topbar{align-items:flex-start;flex-direction:column}.topbar>div{min-width:0;max-width:100%}.layout{grid-template-columns:minmax(0,1fr)}.side{max-width:none}.page{overflow-x:hidden}}@media(max-width:720px){.page{padding:16px 10px}.chart-card,.side{border-radius:6px}.chart-heading{margin:12px 12px 0}.chart-note{margin:4px 12px 0}.chart-wrap{height:62vh;min-height:420px}.title{font-size:21px}.controls{display:grid;grid-template-columns:minmax(0,1fr);gap:8px;width:100%;align-items:stretch}.action,.check{justify-content:center;min-width:0;font-size:12px;white-space:normal}.check{justify-content:flex-start}.side{min-width:0}.axis-label{font-size:13px}.tick text{font-size:11px}}
"""
    css += "\n.point.is-experiment{stroke:#111827;stroke-width:3;opacity:1}\n"
    script = f"""
<script>
const DATA = {points_json};
const colors = {{ chemistry: "#b6423a", crypto: "#2454a6", other: "#d39b18" }};
const state = {{ categories: new Set(["chemistry","crypto","other"]) }};
const svg = document.querySelector(".chart");
const plot = document.querySelector(".plot");
const gateSvg = document.querySelector(".chart-gates");
const gatePlot = document.querySelector(".plot-gates");
const gateEmpty = document.querySelector(".empty-gates");
const tooltip = document.querySelector(".tooltip");
const empty = document.querySelector(".empty");
let tooltipHideTimer;
let pinnedTip = false;
function esc(value) {{
  return String(value ?? "").replace(/[&<>"']/g, ch => ({{"&":"&amp;","<":"&lt;",">":"&gt;","\\"":"&quot;","'":"&#39;"}}[ch]));
}}
function fmt(x) {{
  if (x == null || Number.isNaN(x)) return "NA";
  if (x === 0) return "0";
  const ax = Math.abs(x);
  if (ax >= 1e4 || ax < 1e-2) return x.toExponential(3).replace(/\\.0+e/,"e").replace(/(\\.\\d*?)0+e/,"$1e");
  return new Intl.NumberFormat("en-US", {{ maximumSignificantDigits: 4 }}).format(x);
}}
function fmtDuration(seconds) {{
  if (seconds == null || Number.isNaN(seconds) || !Number.isFinite(seconds)) return "NA";
  const abs = Math.abs(seconds);
  if (abs < 60) return `${{fmt(seconds)}} s`;
  if (abs < 3600) return `${{fmt(seconds / 60)}} min`;
  if (abs < 86400) return `${{fmt(seconds / 3600)}} h`;
  if (abs < 31557600) return `${{fmt(seconds / 86400)}} day`;
  return `${{fmt(seconds / 31557600)}} year`;
}}
function log10(x) {{ return Math.log(x) / Math.LN10; }}
function powTickLabel(value, attrs) {{
  const exponent = Math.round(log10(value));
  return `<text ${{attrs}}>10<tspan baseline-shift="super" font-size="8">${{exponent}}</tspan></text>`;
}}
function nicePow(min, max) {{
  const lo = Math.floor(log10(min));
  const hi = Math.ceil(log10(max));
  return [Math.pow(10, lo), Math.pow(10, hi), lo, hi];
}}
function ticks(lo, hi) {{
  const out = [];
  for (let e = lo; e <= hi; e++) out.push(Math.pow(10, e));
  return out;
}}
function pointClass(d) {{
  return "point" + (d.isExperiment ? " is-experiment" : "") + (d.isSubroutineOnly ? " is-subroutine" : "");
}}
function categoryShape(d, x, y, r) {{
  const cls = pointClass(d);
  if (d.isSubroutineOnly) return `<path class="${{cls}}" d="M ${{x}} ${{y-r}} L ${{x+r}} ${{y}} L ${{x}} ${{y+r}} L ${{x-r}} ${{y}} Z"></path>`;
  if (d.category === "crypto") return `<circle class="${{cls}}" cx="${{x}}" cy="${{y}}" r="${{r}}"></circle>`;
  if (d.category === "chemistry") return `<rect class="${{cls}}" x="${{x-r}}" y="${{y-r}}" width="${{2*r}}" height="${{2*r}}" rx="2"></rect>`;
  return `<path class="${{cls}}" d="M ${{x}} ${{y-r}} L ${{x+r}} ${{y+r}} L ${{x-r}} ${{y+r}} Z"></path>`;
}}
function visibleData() {{
  return DATA.filter(d => state.categories.has(d.category) && d.physicalQubits > 0 && d.runtimeSeconds > 0);
}}
function visibleGateData() {{
  return DATA.filter(d => state.categories.has(d.category) && d.physicalQubits > 0 && d.logicalGateCount > 0);
}}
function render() {{
  const rect = svg.getBoundingClientRect();
  const width = Math.max(320, rect.width || 900);
  const height = Math.max(520, rect.height || 620);
  svg.setAttribute("viewBox", `0 0 ${{width}} ${{height}}`);
  const isNarrow = width <= 520;
  const margin = {{ left: isNarrow ? 70 : 86, right: isNarrow ? 34 : 30, top: 28, bottom: 72 }};
  const innerW = width - margin.left - margin.right;
  const innerH = height - margin.top - margin.bottom;
  const data = visibleData();
  empty.classList.toggle("is-open", data.length === 0);
  if (!data.length) {{ plot.innerHTML = ""; return; }}
  const [xMin,xMax,xLo,xHi] = nicePow(Math.min(...data.map(d=>d.physicalQubits)), Math.max(...data.map(d=>d.physicalQubits)));
  const [yMin,yMax,yLo,yHi] = nicePow(Math.min(...data.map(d=>d.runtimeSeconds)), Math.max(...data.map(d=>d.runtimeSeconds)));
  const sx = v => margin.left + (log10(v) - log10(xMin)) / (log10(xMax) - log10(xMin)) * innerW;
  const sy = v => margin.top + innerH - (log10(v) - log10(yMin)) / (log10(yMax) - log10(yMin)) * innerH;
  let html = `<rect class="plot-bg" x="0" y="0" width="${{width}}" height="${{height}}"></rect>`;
  for (const t of ticks(xLo, xHi)) {{
    const x = sx(t);
    html += `<g class="tick"><line x1="${{x}}" x2="${{x}}" y1="${{margin.top}}" y2="${{margin.top+innerH}}"></line>${{powTickLabel(t, `x="${{x}}" y="${{margin.top+innerH+24}}" text-anchor="middle"`)}}</g>`;
  }}
  for (const t of ticks(yLo, yHi)) {{
    const y = sy(t);
    html += `<g class="tick"><line x1="${{margin.left}}" x2="${{margin.left+innerW}}" y1="${{y}}" y2="${{y}}"></line>${{powTickLabel(t, `x="${{margin.left-10}}" y="${{y+4}}" text-anchor="end"`)}}</g>`;
  }}
  html += `<rect class="domain" x="${{margin.left}}" y="${{margin.top}}" width="${{innerW}}" height="${{innerH}}" fill="none"></rect>`;
  html += `<text class="axis-label" x="${{margin.left + innerW/2}}" y="${{height-22}}" text-anchor="middle">必要物理量子ビット数</text>`;
  html += `<text class="axis-label" transform="translate(25 ${{margin.top + innerH/2}}) rotate(-90)" text-anchor="middle">実行時間 (s)</text>`;
  data.forEach(d => {{
    const x = sx(d.physicalQubits);
    const y = sy(d.runtimeSeconds);
    const r = d.isExperiment ? 7.8 : 6.2;
    html += `<g data-i="${{DATA.indexOf(d)}}" style="fill:${{colors[d.category] || colors.other}}">${{categoryShape(d,x,y,r)}}</g>`;
  }});
  plot.innerHTML = html;
  plot.querySelectorAll("g[data-i]").forEach(g => {{
    g.addEventListener("mouseenter", e => showTip(DATA[+g.dataset.i], e));
    g.addEventListener("mousemove", e => {{ if (!pinnedTip) positionTip(e); }});
    g.addEventListener("mouseleave", hideTip);
    g.addEventListener("focusin", e => showTip(DATA[+g.dataset.i], e));
    g.addEventListener("click", e => pinTip(DATA[+g.dataset.i], e));
    g.setAttribute("tabindex", "0");
  }});
}}
function renderGateChart() {{
  if (!gateSvg || !gatePlot || !gateEmpty) return;
  const rect = gateSvg.getBoundingClientRect();
  const width = Math.max(320, rect.width || 900);
  const height = Math.max(520, rect.height || 620);
  gateSvg.setAttribute("viewBox", `0 0 ${{width}} ${{height}}`);
  const isNarrow = width <= 520;
  const margin = {{ left: isNarrow ? 70 : 86, right: isNarrow ? 34 : 30, top: 28, bottom: 72 }};
  const innerW = width - margin.left - margin.right;
  const innerH = height - margin.top - margin.bottom;
  const data = visibleGateData();
  gateEmpty.classList.toggle("is-open", data.length === 0);
  if (!data.length) {{ gatePlot.innerHTML = ""; return; }}
  const [xMin,xMax,xLo,xHi] = nicePow(Math.min(...data.map(d=>d.physicalQubits)), Math.max(...data.map(d=>d.physicalQubits)));
  const [yMin,yMax,yLo,yHi] = nicePow(Math.min(...data.map(d=>d.logicalGateCount)), Math.max(...data.map(d=>d.logicalGateCount)));
  const sx = v => margin.left + (log10(v) - log10(xMin)) / (log10(xMax) - log10(xMin)) * innerW;
  const sy = v => margin.top + innerH - (log10(v) - log10(yMin)) / (log10(yMax) - log10(yMin)) * innerH;
  let html = `<rect class="plot-bg" x="0" y="0" width="${{width}}" height="${{height}}"></rect>`;
  for (const t of ticks(xLo, xHi)) {{
    const x = sx(t);
    html += `<g class="tick"><line x1="${{x}}" x2="${{x}}" y1="${{margin.top}}" y2="${{margin.top+innerH}}"></line>${{powTickLabel(t, `x="${{x}}" y="${{margin.top+innerH+24}}" text-anchor="middle"`)}}</g>`;
  }}
  for (const t of ticks(yLo, yHi)) {{
    const y = sy(t);
    html += `<g class="tick"><line x1="${{margin.left}}" x2="${{margin.left+innerW}}" y1="${{y}}" y2="${{y}}"></line>${{powTickLabel(t, `x="${{margin.left-10}}" y="${{y+4}}" text-anchor="end"`)}}</g>`;
  }}
  html += `<rect class="domain" x="${{margin.left}}" y="${{margin.top}}" width="${{innerW}}" height="${{innerH}}" fill="none"></rect>`;
  html += `<text class="axis-label" x="${{margin.left + innerW/2}}" y="${{height-22}}" text-anchor="middle">必要物理量子ビット数</text>`;
  html += `<text class="axis-label" transform="translate(25 ${{margin.top + innerH/2}}) rotate(-90)" text-anchor="middle">報告論理ゲート数</text>`;
  data.forEach(d => {{
    const x = sx(d.physicalQubits);
    const y = sy(d.logicalGateCount);
    const r = d.isExperiment ? 7.8 : 6.2;
    html += `<g data-i="${{DATA.indexOf(d)}}" style="fill:${{colors[d.category] || colors.other}}">${{categoryShape(d,x,y,r)}}</g>`;
  }});
  gatePlot.innerHTML = html;
  gatePlot.querySelectorAll("g[data-i]").forEach(g => {{
    g.addEventListener("mouseenter", e => showTip(DATA[+g.dataset.i], e));
    g.addEventListener("mousemove", e => {{ if (!pinnedTip) positionTip(e); }});
    g.addEventListener("mouseleave", hideTip);
    g.addEventListener("focusin", e => showTip(DATA[+g.dataset.i], e));
    g.addEventListener("click", e => pinTip(DATA[+g.dataset.i], e));
    g.setAttribute("tabindex", "0");
  }});
}}
function renderAll() {{
  render();
  renderGateChart();
}}
function clearPinnedPoint() {{
  document.querySelectorAll(".point.is-pinned").forEach(point => point.classList.remove("is-pinned"));
}}
function setPinnedPoint(d) {{
  clearPinnedPoint();
  const index = DATA.indexOf(d);
  document.querySelectorAll(`g[data-i="${{index}}"] .point`).forEach(point => point.classList.add("is-pinned"));
}}
function pinTip(d, event) {{
  event.preventDefault();
  event.stopPropagation();
  pinnedTip = true;
  setPinnedPoint(d);
  showTip(d, event, true);
}}
function closeTip() {{
  pinnedTip = false;
  clearPinnedPoint();
  tooltip.classList.remove("is-open", "is-pinned");
}}
function showTip(d, event, force = false) {{
  if (pinnedTip && !force) return;
  clearTimeout(tooltipHideTimer);
  const paperTitle = d.paperHref
    ? `<a href="${{esc(d.paperHref)}}" target="_blank" rel="noopener">${{esc(d.paper)}}</a>`
    : esc(d.paper);
  tooltip.innerHTML = `<div class="tip-header"><p class="tip-title">${{paperTitle}}</p><button type="button" class="tip-close" data-close-tip aria-label="詳細を閉じる">×</button></div>
    <dl class="tip-grid">
      <dt>分類</dt><dd>${{esc(d.categoryLabel)}}</dd>
      <dt>問題</dt><dd>${{esc(d.problem)}}</dd>
      <dt>対象</dt><dd>${{esc(d.target)}}</dd>
      <dt>見積もり</dt><dd>${{esc(d.estimateType)}}</dd>
      <dt>実験実施</dt><dd>${{d.isExperiment ? "あり" : "なし"}}</dd>
      <dt>物理エラー率</dt><dd>${{fmt(d.physicalErrorRate)}}</dd>
      <dt>物理量子ビット</dt><dd>${{fmt(d.physicalQubits)}}</dd>
      <dt>論理量子ビット</dt><dd>${{fmt(d.logicalQubits)}}</dd>
      <dt>code distance</dt><dd>${{fmt(d.codeDistance)}}</dd>
      <dt>cycle/測定時間(s)</dt><dd>${{fmt(d.cycleTimeSeconds)}}</dd>
      <dt>実行時間</dt><dd>${{fmtDuration(d.runtimeSeconds)}}</dd>
      <dt>古典計算時間</dt><dd>${{fmtDuration(d.classicalRuntimeSeconds)}}</dd>
      <dt>古典/量子時間比</dt><dd>${{fmt(d.classicalQuantumRuntimeRatio)}}</dd>
      <dt>論理ゲート数</dt><dd>${{fmt(d.logicalGateCount)}} ${{esc(d.logicalGateLabel || "")}}</dd>
      <dt>時空間体積</dt><dd>${{fmt(d.spacetimeVolumeQubitDays)}} qubit-days</dd>
      <dt>デバイス</dt><dd>${{esc(d.device || "NA")}}</dd>
      <dt>誤り訂正符号</dt><dd>${{esc(d.errorCorrectionCode || "NA")}}</dd>
      <dt>物理量子ビット種</dt><dd>${{esc(d.physicalQubitType || "NA")}}</dd>
    </dl>
    <p class="tip-note">${{esc(d.classicalAssumptions || d.note || d.evidence || "")}}</p>`;
  tooltip.classList.add("is-open");
  tooltip.classList.toggle("is-pinned", pinnedTip);
  positionTip(event);
}}
function positionTip(event) {{
  const pad = 12;
  const box = tooltip.getBoundingClientRect();
  let x = event.clientX + 14;
  let y = event.clientY + 14;
  if (x + box.width + pad > window.innerWidth) x = event.clientX - box.width - 14;
  if (y + box.height + pad > window.innerHeight) y = event.clientY - box.height - 14;
  tooltip.style.left = Math.max(pad, x) + "px";
  tooltip.style.top = Math.max(pad, y) + "px";
}}
function hideTip() {{
  if (pinnedTip) return;
  clearTimeout(tooltipHideTimer);
  tooltipHideTimer = setTimeout(() => tooltip.classList.remove("is-open"), 180);
}}
function downloadBlob(blob, filename) {{
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 500);
}}
function graphSvgSource() {{
  render();
  const clone = svg.cloneNode(true);
  const viewBox = svg.getAttribute("viewBox") || "0 0 1200 720";
  const parts = viewBox.split(/\\s+/).map(Number);
  clone.setAttribute("xmlns", "http://www.w3.org/2000/svg");
  clone.setAttribute("width", String(parts[2] || 1200));
  clone.setAttribute("height", String(parts[3] || 720));
  const style = document.createElementNS("http://www.w3.org/2000/svg", "style");
  style.textContent = `.plot-bg{{fill:#fff}}.axis-label{{fill:#111827;font:700 14px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}.tick text{{fill:#374151;font:12px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}.tick line{{stroke:#e7e7e7;stroke-width:1}}.domain{{stroke:#111827;stroke-width:1.35}}.point{{stroke:#fff;stroke-width:1.5;opacity:.88}}.point.is-experiment{{stroke:#111827;stroke-width:3;opacity:1}}`;
  clone.insertBefore(style, clone.firstChild);
  return new XMLSerializer().serializeToString(clone);
}}
function downloadGraph(format) {{
  const source = graphSvgSource();
  const svgBlob = new Blob([source], {{ type: "image/svg+xml;charset=utf-8" }});
  if (format === "svg") {{
    downloadBlob(svgBlob, "quantum_resource_estimates_physical_graph.svg");
    return;
  }}
  const url = URL.createObjectURL(svgBlob);
  const image = new Image();
  image.onload = () => {{
    const viewBox = svg.getAttribute("viewBox") || "0 0 1200 720";
    const parts = viewBox.split(/\\s+/).map(Number);
    const width = parts[2] || image.width || 1200;
    const height = parts[3] || image.height || 720;
    const scale = 2;
    const canvas = document.createElement("canvas");
    canvas.width = Math.round(width * scale);
    canvas.height = Math.round(height * scale);
    const ctx = canvas.getContext("2d");
    ctx.fillStyle = "#fff";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(image, 0, 0, canvas.width, canvas.height);
    canvas.toBlob(blob => {{
      if (blob) downloadBlob(blob, "quantum_resource_estimates_physical_graph.png");
      URL.revokeObjectURL(url);
    }}, "image/png");
  }};
  image.onerror = () => URL.revokeObjectURL(url);
  image.src = url;
}}
function tsvEscape(value) {{
  return String(value ?? "NA").replace(/[\\t\\r\\n]+/g, " ").trim();
}}
function downloadCurrentTsv() {{
  const header = ["date","category","problem","paper","paper_url","target","estimate_type","is_experiment","physical_qubits","runtime_seconds","runtime_human","classical_runtime_seconds","classical_quantum_runtime_ratio","reported_logical_gate_count","reported_logical_gate_source","physical_error_rate","logical_qubits","code_distance","cycle_time_seconds","spacetime_volume_qubit_days","device","error_correction_code","physical_qubit_type","note"];
  const rows = DATA
    .filter(d => state.categories.has(d.category) && d.physicalQubits > 0 && (d.runtimeSeconds > 0 || d.logicalGateCount > 0))
    .map(d => [d.date,d.categoryLabel,d.problem,d.paper,d.paperHref,d.target,d.estimateType,d.isExperiment ? 1 : 0,d.physicalQubits,d.runtimeSeconds,fmtDuration(d.runtimeSeconds),d.classicalRuntimeSeconds,d.classicalQuantumRuntimeRatio,d.logicalGateCount,d.logicalGateLabel,d.physicalErrorRate,d.logicalQubits,d.codeDistance,d.cycleTimeSeconds,d.spacetimeVolumeQubitDays,d.device,d.errorCorrectionCode,d.physicalQubitType,d.classicalAssumptions || d.note || d.evidence || ""]);
  const text = [header, ...rows].map(row => row.map(tsvEscape).join("\\t")).join("\\n") + "\\n";
  downloadBlob(new Blob([text], {{ type: "text/tab-separated-values;charset=utf-8" }}), "quantum_resource_estimates_physical_graph_data.tsv");
}}
tooltip.addEventListener("mouseenter", () => clearTimeout(tooltipHideTimer));
tooltip.addEventListener("mouseleave", hideTip);
tooltip.addEventListener("click", event => {{
  if (event.target.closest("[data-close-tip]")) closeTip();
}});
document.querySelectorAll("[data-download]").forEach(btn => {{
  btn.addEventListener("click", () => downloadGraph(btn.dataset.download));
}});
document.querySelector("[data-download-tsv]")?.addEventListener("click", downloadCurrentTsv);
document.querySelectorAll("[data-category]").forEach(input => {{
  input.addEventListener("change", () => {{
    if (input.checked) state.categories.add(input.dataset.category);
    else state.categories.delete(input.dataset.category);
    renderAll();
  }});
}});
window.addEventListener("resize", renderAll);
renderAll();
</script>
"""
    return f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>物理量子ビット・物理リソース補助グラフ</title>
<style>{css}</style>
</head>
<body>
<main class="page">
  <div class="topbar">
    <div>
      <h1 class="title">物理量子ビット・物理リソース補助グラフ</h1>
      <p class="subtitle">{AI_EXTRACTION_NOTICE}</p>
      <p class="subtitle">横軸は必要物理量子ビット数。縦軸を実行時間と報告論理ゲート数で見比べます。どちらも対数軸です。</p>
    </div>
    <div class="controls" aria-label="graph controls">
      <button type="button" class="action" data-download="svg">SVG保存</button>
      <button type="button" class="action" data-download="png">PNG保存</button>
      <button type="button" class="action" data-download-tsv>TSV保存</button>
      <label class="check"><input type="checkbox" data-category="chemistry" checked><span class="marker chemistry"></span>量子化学・量子シミュレーション</label>
      <label class="check"><input type="checkbox" data-category="crypto" checked><span class="marker crypto"></span>素因数分解・暗号系</label>
      <label class="check"><input type="checkbox" data-category="other" checked><span class="marker other"></span>その他</label>
    </div>
  </div>
  <div class="layout">
    <div class="chart-stack">
      <section class="chart-card" aria-label="physical qubits and runtime scatter plot">
        <h2 class="chart-heading">必要物理量子ビット数 × 実行時間</h2>
        <p class="chart-note">縦軸は論文が報告した実行時間です。</p>
        <div class="chart-wrap">
          <svg class="chart" role="img" aria-label="必要物理量子ビット数と実行時間の散布図"><g class="plot"></g></svg>
          <div class="empty">表示できる点がありません。</div>
        </div>
      </section>
      <section class="chart-card" aria-label="physical qubits and logical gate count scatter plot">
        <h2 class="chart-heading">必要物理量子ビット数 × 報告論理ゲート数</h2>
        <p class="chart-note">縦軸は Toffoli数、Tゲート数、Cliffordゲート数、その他論理ゲート数のうち、各行で報告されている代表値です。換算はしていません。</p>
        <div class="chart-wrap">
          <svg class="chart chart-gates" role="img" aria-label="必要物理量子ビット数と報告論理ゲート数の散布図"><g class="plot-gates"></g></svg>
          <div class="empty empty-gates">表示できる点がありません。</div>
        </div>
      </section>
    </div>
    <aside class="side">
      <h2>このグラフの読み方</h2>
      <p>横軸はいずれも必要物理量子ビット数です。上の図は実行時間、下の図は報告された論理ゲート数を縦軸にしています。</p>
      <ul>
        <li>物理量子ビット数は、論文が報告した総数または表中の対応する物理量子ビット総数です。</li>
        <li>実行時間は論文内の報告値です。shot数、並列化、factory数、cycle/測定時間などの仮定は論文により異なります。</li>
        <li>論理ゲート数は、Toffoli数、Tゲート数、Cliffordゲート数、その他論理ゲート数の順に、表にある最初の報告値をそのまま使っています。</li>
        <li>物理エラー率、routing、factory、memory、module間通信などの含まれ方は詳細表示で確認できます。</li>
      </ul>
      <p>点にマウスを合わせると詳細を表示し、クリックすると表示を固定できます。固定表示は×ボタンで閉じられます。</p>
      <p>誤りや追加情報の報告は <a href="https://github.com/kosukemtr/moonshot-website/issues/new?title=%E9%87%8F%E5%AD%90%E3%83%AA%E3%82%BD%E3%83%BC%E3%82%B9%E8%A6%8B%E7%A9%8D%E3%82%82%E3%82%8A%E3%82%B0%E3%83%A9%E3%83%95%E3%81%AE%E4%BF%AE%E6%AD%A3%E6%8F%90%E6%A1%88&amp;body=%23%23+%E4%BF%AE%E6%AD%A3%E3%81%97%E3%81%9F%E3%81%84%E7%82%B9%0A%0A%E4%BE%8B%3A+%E8%AB%96%E6%96%87%E5%90%8D%E3%80%81%E3%83%97%E3%83%AD%E3%83%83%E3%83%88%E7%82%B9%E3%80%81%E6%95%B0%E5%80%A4%E3%80%81%E6%8F%9B%E7%AE%97%E3%83%AB%E3%83%BC%E3%83%AB%E3%81%AA%E3%81%A9%0A%0A%23%23+%E8%A9%B2%E5%BD%93%E3%81%99%E3%82%8B%E8%AB%96%E6%96%87%E3%83%BB%E3%83%87%E3%83%BC%E3%82%BF%0A%0A-+%E8%AB%96%E6%96%87%3A%0A-+%E5%AF%BE%E8%B1%A1%E3%82%B5%E3%82%A4%E3%82%BA%3A%0A-+%E7%8F%BE%E5%9C%A8%E8%A1%A8%E7%A4%BA%E3%81%95%E3%82%8C%E3%81%A6%E3%81%84%E3%82%8B%E5%80%A4%3A%0A-+%E6%AD%A3%E3%81%97%E3%81%84%E3%81%A8%E6%80%9D%E3%81%86%E5%80%A4%3A%0A%0A%23%23+%E6%A0%B9%E6%8B%A0%0A%0A%E8%AB%96%E6%96%87%E4%B8%AD%E3%81%AE%E3%83%9A%E3%83%BC%E3%82%B8%E3%80%81%E8%A1%A8%E3%80%81%E5%BC%8F%E3%80%81%E3%81%BE%E3%81%9F%E3%81%AF%E8%A3%9C%E8%B6%B3%E8%AA%AC%E6%98%8E%E3%81%B8%E3%81%AE%E3%83%AA%E3%83%B3%E3%82%AF%E3%82%92%E8%B2%BC%E3%81%A3%E3%81%A6%E3%81%8F%E3%81%A0%E3%81%95%E3%81%84%E3%80%82%0A%0A%23%23+%E8%A3%9C%E8%B6%B3%0A%0A%E5%BF%85%E8%A6%81%E3%81%AA%E3%82%89%E8%87%AA%E7%94%B1%E3%81%AB%E8%BF%BD%E8%A8%98%E3%81%97%E3%81%A6%E3%81%8F%E3%81%A0%E3%81%95%E3%81%84%E3%80%82%0A" target="_blank" rel="noopener">下書き入りのGitHub Issue</a> からお願いします。</p>
    </aside>
  </div>
  <p class="footer-note">注: このグラフは論文間の大まかな位置関係を見るためのものです。物理量子ビット数、実行時間、論理ゲート数に含まれる仮定は論文により異なります。</p>
</main>
<div class="tooltip" role="tooltip"></div>
{script}
</body>
</html>
"""


def build_graph_html(base: Path, header: list[str], rows: list[list[str]]) -> str:
    points_json = json.dumps(graph_points(header, rows), ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    css = """
html{box-sizing:border-box;overflow-x:hidden}*,*:before,*:after{box-sizing:inherit}body{margin:0;overflow-x:hidden;background:#f7f7f5;color:#17202f;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;line-height:1.5}.page{min-height:100vh;width:100%;max-width:100vw;overflow-x:hidden;padding:22px clamp(14px,2.4vw,34px)}.topbar{display:flex;align-items:flex-end;justify-content:space-between;gap:18px;margin:0 0 14px;width:100%;min-width:0}.title{margin:0;font-size:24px;letter-spacing:0}.subtitle{margin:4px 0 0;color:#667085;font-size:13px;overflow-wrap:anywhere;word-break:break-all}.controls{display:flex;flex-wrap:wrap;align-items:center;gap:10px;max-width:100%}.segmented{display:inline-flex;border:1px solid #cfd6e2;border-radius:8px;overflow:hidden;background:#fff}.segmented button{border:0;border-right:1px solid #cfd6e2;background:#fff;color:#344054;padding:8px 10px;font:inherit;font-size:13px;cursor:pointer}.segmented button:last-child{border-right:0}.segmented button[aria-pressed=true]{background:#2454a6;color:#fff}.rate-control{display:inline-flex;align-items:center;gap:6px;border:1px solid #cfd6e2;border-radius:8px;background:#fff;color:#344054;padding:6px 8px;font-size:13px;white-space:nowrap}.rate-control input{width:9.5ch;border:0;border-bottom:1px solid #cfd6e2;border-radius:0;padding:2px 0;font:inherit;text-align:right;color:#17202f;background:transparent}.rate-control input:focus{outline:0;border-bottom-color:#2454a6}.action{border:1px solid #cfd6e2;border-radius:8px;background:#fff;color:#344054;padding:8px 10px;font:inherit;font-size:13px;cursor:pointer}.action:hover{border-color:#98a2b3;background:#f8fafc}.check,.legend-key{display:inline-flex;align-items:center;gap:6px;background:#fff;border:1px solid #cfd6e2;border-radius:8px;padding:7px 9px;font-size:13px;white-space:nowrap}.check input{margin:0}.legend-key{color:#344054}.marker{display:inline-block;width:11px;height:11px;flex:0 0 auto}.marker.chemistry{background:#b6423a;border-radius:2px}.marker.crypto{background:#2454a6;border-radius:50%}.marker.other{width:0;height:0;border-left:6px solid transparent;border-right:6px solid transparent;border-bottom:11px solid #d39b18}.marker.subroutine{width:12px;height:12px;background:#fff;border:2px solid #475467;transform:rotate(45deg)}.layout{display:grid;grid-template-columns:minmax(0,1fr) 340px;gap:14px;align-items:start;width:100%;min-width:0}.chart-card,.side{max-width:100%;background:#fff;border:1px solid #d6d6d6;border-radius:8px}.chart-card{min-width:0;overflow:hidden}.chart-wrap{position:relative;height:calc(100vh - 166px);min-height:560px}.chart{display:block;width:100%;height:100%;touch-action:none}.plot-bg{fill:#fff}.axis-label{fill:#111827;font-size:14px;font-weight:700}.tick text{fill:#374151;font-size:12px}.tick line{stroke:#e7e7e7;stroke-width:1}.runtime-guide line{stroke:#5f6b7a;stroke-width:1.15;stroke-dasharray:4 5;opacity:.72}.runtime-guide text{fill:#344054;font-size:12px;font-weight:650;paint-order:stroke;stroke:#fff;stroke-width:3px}.domain{stroke:#111827;stroke-width:1.35}.point{cursor:pointer;stroke:#fff;stroke-width:1.5;transition:r .12s ease,opacity .12s ease}.point.is-subroutine{fill:#fff;stroke:inherit;stroke-width:2.4;opacity:1}.point.is-muted{opacity:.18}.point.is-hovered,.point.is-pinned{stroke:#111827;stroke-width:2.5}.side{padding:14px;min-height:360px}.side h2{margin:0 0 8px;font-size:16px}.side p{margin:8px 0;color:#475467;font-size:13px}.side ul{margin:8px 0 0;padding-left:18px;color:#475467;font-size:13px}.side li{margin:6px 0}.side a{color:#184e77;text-decoration-thickness:1px;text-underline-offset:2px}.tooltip{position:fixed;z-index:20;width:min(420px,calc(100vw - 24px));max-height:calc(100vh - 24px);overflow:auto;display:none;background:#fff;border:1px solid #aeb8c8;border-radius:8px;box-shadow:0 18px 48px rgba(20,31,50,.24);padding:12px;pointer-events:auto}.tooltip.is-open{display:block}.tooltip.is-pinned{border-color:#2454a6}.tip-header{display:flex;align-items:flex-start;justify-content:space-between;gap:10px;margin:0 0 6px}.tip-title{font-weight:700;margin:0;min-width:0}.tip-title a{color:#2454a6;text-decoration-thickness:1px;text-underline-offset:2px}.tip-close{flex:0 0 auto;width:26px;height:26px;border:1px solid #cfd6e2;border-radius:50%;background:#fff;color:#344054;font-size:18px;line-height:20px;cursor:pointer}.tip-close:hover{background:#f8fafc;border-color:#98a2b3}.tip-grid{display:grid;grid-template-columns:128px 1fr;gap:4px 8px;font-size:12px}.tip-grid dt{color:#667085}.tip-grid dd{margin:0;color:#17202f;overflow-wrap:anywhere}.tip-note{margin:8px 0 0;color:#475467;font-size:12px;white-space:normal;overflow-wrap:anywhere}.empty{display:none;position:absolute;inset:0;align-items:center;justify-content:center;color:#667085;font-size:14px}.empty.is-open{display:flex}.footer-note{max-width:1120px;margin:14px 0 0;color:#667085;font-size:12px}@media(max-width:1240px){.topbar{align-items:flex-start;flex-direction:column}.topbar>div{min-width:0;max-width:100%}.layout{grid-template-columns:minmax(0,1fr)}.side{max-width:none}.page{overflow-x:hidden}}@media(max-width:720px){.page{padding:16px 10px}.chart-card,.side{border-radius:6px}.chart-wrap{height:62vh;min-height:420px}.title{font-size:21px}.controls{display:grid;grid-template-columns:minmax(0,1fr);gap:8px;width:100%;align-items:stretch}.segmented{width:100%}.segmented button{flex:1;padding:8px 6px}.action,.check,.legend-key,.rate-control{justify-content:center;min-width:0;font-size:12px;white-space:normal}.check{justify-content:flex-start}.rate-control input{width:7ch}.side{min-width:0}.axis-label{font-size:13px}.tick text{font-size:11px}}
"""
    css += "\n.point.is-experiment{stroke:#111827;stroke-width:3;opacity:1}\n"
    script = f"""
<script>
const DATA = {points_json};
const colors = {{ chemistry: "#b6423a", crypto: "#2454a6", other: "#d39b18" }};
const labels = {{ chemistry: "量子化学・量子シミュレーション", crypto: "素因数分解・暗号系", other: "その他" }};
const sourceLabels = {{ toffoli: "Toffoli数", t: "Tゲート数から換算", ccz: "CCZ数", other: "報告論理ゲート数（換算なし）" }};
const RUNTIME_GUIDES = [
  {{ label: "1 day", seconds: 86400 }},
  {{ label: "1 week", seconds: 604800 }},
  {{ label: "1 year", seconds: 31557600 }},
  {{ label: "100 years", seconds: 3155760000 }},
  {{ label: "10000 years", seconds: 315576000000 }}
];
const LOGICAL_QUBIT_DISPLAY_MAX = 1e9;
const state = {{ tMode: 4, toffoliPerUs: 1, categories: new Set(["chemistry","crypto","other"]) }};
const svg = document.querySelector(".chart");
const plot = document.querySelector(".plot");
const tooltip = document.querySelector(".tooltip");
const empty = document.querySelector(".empty");
let tooltipHideTimer;
let pinnedTip = false;
function esc(value) {{
  return String(value ?? "").replace(/[&<>"']/g, ch => ({{"&":"&amp;","<":"&lt;",">":"&gt;","\\"":"&quot;","'":"&#39;"}}[ch]));
}}
function fmt(x) {{
  if (x == null || Number.isNaN(x)) return "NA";
  if (x === 0) return "0";
  const ax = Math.abs(x);
  if (ax >= 1e4 || ax < 1e-2) return x.toExponential(3).replace(/\\.0+e/,"e").replace(/(\\.\\d*?)0+e/,"$1e");
  return new Intl.NumberFormat("en-US", {{ maximumSignificantDigits: 4 }}).format(x);
}}
function fmtShort(x) {{
  if (x == null || Number.isNaN(x)) return "NA";
  if (x === 0) return "0";
  const ax = Math.abs(x);
  if (ax >= 1e4 || ax < 1e-2) return x.toExponential(1).replace(/\\.0e/,"e");
  return new Intl.NumberFormat("en-US", {{ maximumSignificantDigits: 2 }}).format(x);
}}
function fmtDuration(seconds) {{
  if (seconds == null || Number.isNaN(seconds) || !Number.isFinite(seconds)) return "NA";
  const abs = Math.abs(seconds);
  if (abs < 1e-3) return `${{fmtShort(seconds)}} s`;
  if (abs < 60) return `${{fmtShort(seconds)}} s`;
  if (abs < 3600) return `${{fmtShort(seconds / 60)}} min`;
  if (abs < 86400) return `${{fmtShort(seconds / 3600)}} h`;
  if (abs < 31557600) return `${{fmtShort(seconds / 86400)}} day`;
  return `${{fmtShort(seconds / 31557600)}} year`;
}}
function powTickLabel(value, attrs) {{
  const exponent = Math.round(log10(value));
  return `<text ${{attrs}}>10<tspan baseline-shift="super" font-size="8">${{exponent}}</tspan></text>`;
}}
function sciTickLabel(value, attrs) {{
  if (value == null || !Number.isFinite(value) || value <= 0) return `<text ${{attrs}}>NA</text>`;
  const exponent = Math.floor(log10(value));
  const coefficient = value / Math.pow(10, exponent);
  return `<text ${{attrs}}>${{coefficient.toFixed(1)}}×10<tspan baseline-shift="super" font-size="8">${{exponent}}</tspan></text>`;
}}
function yValue(d) {{
  if (d.gateSource === "t") return d.tGateCount / state.tMode;
  return d.toffoliEquivBase;
}}
function projectedRuntimeSeconds(d) {{
  if (!state.toffoliPerUs || state.toffoliPerUs <= 0) return null;
  return yValue(d) / (state.toffoliPerUs * 1000000);
}}
function visibleData() {{
  return DATA.filter(d => state.categories.has(d.category) && d.logicalQubits > 0 && d.logicalQubits <= LOGICAL_QUBIT_DISPLAY_MAX && yValue(d) > 0);
}}
function log10(x) {{ return Math.log(x) / Math.LN10; }}
function nicePow(min, max) {{
  const lo = Math.floor(log10(min));
  const hi = Math.ceil(log10(max));
  return [Math.pow(10, lo), Math.pow(10, hi), lo, hi];
}}
function ticks(lo, hi) {{
  const out = [];
  for (let e = lo; e <= hi; e++) out.push(Math.pow(10, e));
  return out;
}}
function pointClass(d) {{
  return "point" + (d.isExperiment ? " is-experiment" : "") + (d.isSubroutineOnly ? " is-subroutine" : "");
}}
function categoryShape(d, x, y, r) {{
  const cls = pointClass(d);
  if (d.isSubroutineOnly) return `<path class="${{cls}}" d="M ${{x}} ${{y-r}} L ${{x+r}} ${{y}} L ${{x}} ${{y+r}} L ${{x-r}} ${{y}} Z"></path>`;
  if (d.category === "crypto") return `<circle class="${{cls}}" cx="${{x}}" cy="${{y}}" r="${{r}}"></circle>`;
  if (d.category === "chemistry") return `<rect class="${{cls}}" x="${{x-r}}" y="${{y-r}}" width="${{2*r}}" height="${{2*r}}" rx="2"></rect>`;
  return `<path class="${{cls}}" d="M ${{x}} ${{y-r}} L ${{x+r}} ${{y+r}} L ${{x-r}} ${{y+r}} Z"></path>`;
}}
function legendShape(kind, x, y, color) {{
  if (kind === "crypto") return `<circle cx="${{x}}" cy="${{y}}" r="5.5" fill="${{color}}" stroke="${{color}}" stroke-width="1.4"></circle>`;
  if (kind === "chemistry") return `<rect x="${{x-5.5}}" y="${{y-5.5}}" width="11" height="11" rx="2" fill="${{color}}" stroke="${{color}}" stroke-width="1.4"></rect>`;
  if (kind === "subroutine") return `<path d="M ${{x}} ${{y-6.5}} L ${{x+6.5}} ${{y}} L ${{x}} ${{y+6.5}} L ${{x-6.5}} ${{y}} Z" fill="#fff" stroke="${{color}}" stroke-width="2.2"></path>`;
  if (kind === "experiment") return `<circle cx="${{x}}" cy="${{y}}" r="6" fill="#fff" stroke="#111827" stroke-width="3"></circle>`;
  return `<path d="M ${{x}} ${{y-6}} L ${{x+6.5}} ${{y+6}} L ${{x-6.5}} ${{y+6}} Z" fill="${{color}}" stroke="${{color}}" stroke-width="1.4"></path>`;
}}
function renderSvgLegend(x, y, isNarrow, data) {{
  const entries = [
    ["chemistry", "量子化学・量子シミュレーション", colors.chemistry],
    ["crypto", "素因数分解・暗号系", colors.crypto],
    ["other", "その他", colors.other],
  ].filter(([kind]) => state.categories.has(kind) && data.some(d => d.category === kind));
  if (data.some(d => d.isSubroutineOnly)) entries.push(["subroutine", "サブルーチンのみ", "#475467"]);
  if (data.some(d => d.isExperiment)) entries.push(["experiment", "実験実現あり", "#111827"]);
  if (!entries.length) return "";
  const rowH = 18;
  const width = isNarrow ? 204 : 268;
  const height = 14 + entries.length * rowH;
  let html = `<g class="svg-legend" pointer-events="none"><rect class="svg-legend-bg" x="${{x}}" y="${{y}}" width="${{width}}" height="${{height}}" rx="6" fill="#fff" fill-opacity=".94" stroke="#d0d5dd" stroke-width="1"></rect>`;
  entries.forEach((entry, i) => {{
    const [kind, label, color] = entry;
    const yy = y + 17 + i * rowH;
    const labelText = isNarrow && label.length > 12 ? label.replace("・量子シミュレーション", "") : label;
    html += `<g class="svg-legend-row">${{legendShape(kind, x + 15, yy - 3, color)}}<text x="${{x + 30}}" y="${{yy + 1}}" fill="#344054" font-size="12" font-weight="650" font-family="-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif">${{labelText}}</text></g>`;
  }});
  return html + `</g>`;
}}
function render() {{
  const rect = svg.getBoundingClientRect();
  const width = Math.max(320, rect.width || 900);
  const height = Math.max(520, rect.height || 620);
  svg.setAttribute("viewBox", `0 0 ${{width}} ${{height}}`);
  const isNarrow = width <= 520;
  const margin = {{ left: isNarrow ? 68 : 82, right: isNarrow ? 78 : 104, top: 28, bottom: 72 }};
  const innerW = width - margin.left - margin.right;
  const innerH = height - margin.top - margin.bottom;
  const data = visibleData();
  empty.classList.toggle("is-open", data.length === 0);
  if (!data.length) {{ plot.innerHTML = ""; return; }}
  const [xMin,xMax,xLo,xHi] = nicePow(Math.min(...data.map(d=>d.logicalQubits)), Math.max(...data.map(d=>d.logicalQubits)));
  const [yMin,yMax,yLo,yHi] = nicePow(Math.min(...data.map(yValue)), Math.max(...data.map(yValue)));
  const sx = v => margin.left + (log10(v) - log10(xMin)) / (log10(xMax) - log10(xMin)) * innerW;
  const sy = v => margin.top + innerH - (log10(v) - log10(yMin)) / (log10(yMax) - log10(yMin)) * innerH;
  let html = `<rect class="plot-bg" x="0" y="0" width="${{width}}" height="${{height}}"></rect>`;
  for (const t of ticks(xLo, xHi)) {{
    const x = sx(t);
    html += `<g class="tick"><line x1="${{x}}" x2="${{x}}" y1="${{margin.top}}" y2="${{margin.top+innerH}}"></line>${{powTickLabel(t, `x="${{x}}" y="${{margin.top+innerH+24}}" text-anchor="middle"`)}}</g>`;
  }}
  for (const t of ticks(yLo, yHi)) {{
    const y = sy(t);
    html += `<g class="tick"><line x1="${{margin.left}}" x2="${{margin.left+innerW}}" y1="${{y}}" y2="${{y}}"></line>${{powTickLabel(t, `x="${{margin.left-10}}" y="${{y+4}}" text-anchor="end"`)}}</g>`;
    if (state.toffoliPerUs > 0) {{
      const seconds = t / (state.toffoliPerUs * 1000000);
      const rightLabel = !isNarrow || Math.round(log10(t)) % 3 === 0
        ? sciTickLabel(seconds, `x="${{margin.left+innerW+10}}" y="${{y+4}}" text-anchor="start"`)
        : "";
      html += `<g class="tick"><line x1="${{margin.left+innerW}}" x2="${{margin.left+innerW+6}}" y1="${{y}}" y2="${{y}}"></line>${{rightLabel}}</g>`;
    }}
  }}
  if (state.toffoliPerUs > 0) {{
    for (const guide of RUNTIME_GUIDES) {{
      const gateValue = guide.seconds * state.toffoliPerUs * 1000000;
      if (gateValue < yMin || gateValue > yMax) continue;
      const y = sy(gateValue);
      html += `<g class="runtime-guide"><line x1="${{margin.left}}" x2="${{margin.left+innerW}}" y1="${{y}}" y2="${{y}}"></line><text x="${{margin.left+innerW-8}}" y="${{y-6}}" text-anchor="end">${{guide.label}}</text></g>`;
    }}
  }}
  html += `<rect class="domain" x="${{margin.left}}" y="${{margin.top}}" width="${{innerW}}" height="${{innerH}}" fill="none"></rect>`;
  html += `<text class="axis-label" x="${{margin.left + innerW/2}}" y="${{height-22}}" text-anchor="middle">報告論理量子ビット数</text>`;
  html += `<text class="axis-label" transform="translate(24 ${{margin.top + innerH/2}}) rotate(-90)" text-anchor="middle">Toffoli換算または報告論理ゲート数</text>`;
  if (state.toffoliPerUs > 0 && !isNarrow) {{
    html += `<text class="axis-label" transform="translate(${{width-18}} ${{margin.top + innerH/2}}) rotate(90)" text-anchor="middle">概算時間</text>`;
  }}
  data.forEach((d, i) => {{
    const x = sx(d.logicalQubits);
    const y = sy(yValue(d));
    const r = d.isExperiment ? 8 : (d.isSubroutineOnly ? 7 : (d.gateSource === "t" ? 5.5 : 6.5));
    html += `<g data-i="${{DATA.indexOf(d)}}" style="fill:${{colors[d.category] || colors.other}};stroke:${{colors[d.category] || colors.other}}">${{categoryShape(d,x,y,r)}}</g>`;
  }});
  html += renderSvgLegend(margin.left + 12, margin.top + 12, isNarrow, data);
  plot.innerHTML = html;
  plot.querySelectorAll("g[data-i]").forEach(g => {{
    g.addEventListener("mouseenter", e => showTip(DATA[+g.dataset.i], e));
    g.addEventListener("mousemove", e => {{ if (!pinnedTip) positionTip(e); }});
    g.addEventListener("mouseleave", hideTip);
    g.addEventListener("focusin", e => showTip(DATA[+g.dataset.i], e));
    g.addEventListener("click", e => pinTip(DATA[+g.dataset.i], e));
    g.setAttribute("tabindex", "0");
  }});
}}
function clearPinnedPoint() {{
  document.querySelectorAll(".point.is-pinned").forEach(point => point.classList.remove("is-pinned"));
}}
function setPinnedPoint(d) {{
  clearPinnedPoint();
  const index = DATA.indexOf(d);
  document.querySelectorAll(`g[data-i="${{index}}"] .point`).forEach(point => point.classList.add("is-pinned"));
}}
function pinTip(d, event) {{
  event.preventDefault();
  event.stopPropagation();
  pinnedTip = true;
  setPinnedPoint(d);
  showTip(d, event, true);
}}
function closeTip() {{
  pinnedTip = false;
  clearPinnedPoint();
  tooltip.classList.remove("is-open", "is-pinned");
}}
function showTip(d, event, force = false) {{
  if (pinnedTip && !force) return;
  const y = yValue(d);
  clearTimeout(tooltipHideTimer);
  const paperTitle = d.paperHref
    ? `<a href="${{esc(d.paperHref)}}" target="_blank" rel="noopener">${{esc(d.paper)}}</a>`
    : esc(d.paper);
  tooltip.innerHTML = `<div class="tip-header"><p class="tip-title">${{paperTitle}}</p><button type="button" class="tip-close" data-close-tip aria-label="詳細を閉じる">×</button></div>
    <dl class="tip-grid">
      <dt>分類</dt><dd>${{esc(d.categoryLabel)}}</dd>
      <dt>問題</dt><dd>${{esc(d.problem)}}</dd>
      <dt>対象</dt><dd>${{esc(d.target)}}</dd>
      <dt>見積もり</dt><dd>${{esc(d.estimateType)}}</dd>
      <dt>実験実施</dt><dd>${{d.isExperiment ? "あり" : "なし"}}</dd>
      <dt>論理量子ビット</dt><dd>${{fmt(d.logicalQubits)}}</dd>
      <dt>縦軸値</dt><dd>${{fmt(y)}} (${{esc(sourceLabels[d.gateSource] || d.gateSource)}})</dd>
      <dt>レート換算時間</dt><dd>${{fmtDuration(projectedRuntimeSeconds(d))}} @ ${{fmtShort(state.toffoliPerUs)}} Toffoli/us</dd>
      <dt>物理量子ビット</dt><dd>${{fmt(d.physicalQubits)}}</dd>
      <dt>実行時間(s)</dt><dd>${{fmt(d.runtimeSeconds)}}</dd>
      <dt>デバイス</dt><dd>${{esc(d.device || "NA")}}</dd>
      <dt>誤り訂正符号</dt><dd>${{esc(d.errorCorrectionCode || "NA")}}</dd>
      <dt>物理量子ビット種</dt><dd>${{esc(d.physicalQubitType || "NA")}}</dd>
    </dl>
    <p class="tip-note">${{esc(d.note || d.evidence || "")}}</p>`;
  tooltip.classList.add("is-open");
  tooltip.classList.toggle("is-pinned", pinnedTip);
  positionTip(event);
}}
function positionTip(event) {{
  const pad = 12;
  const box = tooltip.getBoundingClientRect();
  let x = event.clientX + 14;
  let y = event.clientY + 14;
  if (x + box.width + pad > window.innerWidth) x = event.clientX - box.width - 14;
  if (y + box.height + pad > window.innerHeight) y = event.clientY - box.height - 14;
  tooltip.style.left = Math.max(pad, x) + "px";
  tooltip.style.top = Math.max(pad, y) + "px";
}}
function hideTip() {{
  if (pinnedTip) return;
  clearTimeout(tooltipHideTimer);
  tooltipHideTimer = setTimeout(() => tooltip.classList.remove("is-open"), 180);
}}
function downloadBlob(blob, filename) {{
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 500);
}}
function graphSvgSource() {{
  render();
  const clone = svg.cloneNode(true);
  const viewBox = svg.getAttribute("viewBox") || "0 0 1200 720";
  const parts = viewBox.split(/\\s+/).map(Number);
  const width = parts[2] || 1200;
  const height = parts[3] || 720;
  clone.setAttribute("xmlns", "http://www.w3.org/2000/svg");
  clone.setAttribute("width", String(width));
  clone.setAttribute("height", String(height));
  const style = document.createElementNS("http://www.w3.org/2000/svg", "style");
  style.textContent = `.plot-bg{{fill:#fff}}.axis-label{{fill:#111827;font:700 14px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}.tick text{{fill:#374151;font:12px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}.tick line{{stroke:#e7e7e7;stroke-width:1}}.runtime-guide line{{stroke:#5f6b7a;stroke-width:1.15;stroke-dasharray:4 5;opacity:.72}}.runtime-guide text{{fill:#344054;font:650 12px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;paint-order:stroke;stroke:#fff;stroke-width:3px}}.domain{{stroke:#111827;stroke-width:1.35}}.point{{stroke:#fff;stroke-width:1.5}}.point.is-subroutine{{fill:#fff;stroke:inherit;stroke-width:2.4;opacity:1}}.point.is-experiment{{stroke:#111827;stroke-width:3;opacity:1}}`;
  clone.insertBefore(style, clone.firstChild);
  return new XMLSerializer().serializeToString(clone);
}}
function downloadGraph(format) {{
  const source = graphSvgSource();
  const svgBlob = new Blob([source], {{ type: "image/svg+xml;charset=utf-8" }});
  if (format === "svg") {{
    downloadBlob(svgBlob, "quantum_resource_estimates_graph.svg");
    return;
  }}
  const url = URL.createObjectURL(svgBlob);
  const image = new Image();
  image.onload = () => {{
    const viewBox = svg.getAttribute("viewBox") || "0 0 1200 720";
    const parts = viewBox.split(/\\s+/).map(Number);
    const width = parts[2] || image.width || 1200;
    const height = parts[3] || image.height || 720;
    const scale = 2;
    const canvas = document.createElement("canvas");
    canvas.width = Math.round(width * scale);
    canvas.height = Math.round(height * scale);
    const ctx = canvas.getContext("2d");
    ctx.fillStyle = "#fff";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(image, 0, 0, canvas.width, canvas.height);
    canvas.toBlob(blob => {{
      if (blob) downloadBlob(blob, "quantum_resource_estimates_graph.png");
      URL.revokeObjectURL(url);
    }}, "image/png");
  }};
  image.onerror = () => URL.revokeObjectURL(url);
  image.src = url;
}}
function tsvEscape(value) {{
  return String(value ?? "NA").replace(/[\\t\\r\\n]+/g, " ").trim();
}}
function downloadCurrentTsv() {{
  const header = [
    "date",
    "category",
    "problem",
    "paper",
    "paper_url",
    "target",
    "estimate_type",
    "is_experiment",
    "is_subroutine_only",
    "logical_qubits",
    "physical_qubits",
    "plotted_gate_count",
    "gate_source",
    "t_mode",
    "toffoli_per_microsecond",
    "runtime_from_rate_seconds",
    "reported_runtime_seconds",
    "device",
    "error_correction_code",
    "physical_qubit_type",
    "note"
  ];
  const rows = visibleData().map(d => [
    d.date,
    d.categoryLabel,
    d.problem,
    d.paper,
    d.paperHref,
    d.target,
    d.estimateType,
    d.isExperiment ? 1 : 0,
    d.isSubroutineOnly ? 1 : 0,
    d.logicalQubits,
    d.physicalQubits,
    yValue(d),
    sourceLabels[d.gateSource] || d.gateSource,
    d.gateSource === "t" ? `T/${{state.tMode}}` : "NA",
    state.toffoliPerUs || "NA",
    projectedRuntimeSeconds(d),
    d.runtimeSeconds,
    d.device,
    d.errorCorrectionCode,
    d.physicalQubitType,
    d.note || d.evidence || ""
  ]);
  const text = [header, ...rows].map(row => row.map(tsvEscape).join("\\t")).join("\\n") + "\\n";
  downloadBlob(new Blob([text], {{ type: "text/tab-separated-values;charset=utf-8" }}), "quantum_resource_estimates_graph_data.tsv");
}}
tooltip.addEventListener("mouseenter", () => clearTimeout(tooltipHideTimer));
tooltip.addEventListener("mouseleave", hideTip);
tooltip.addEventListener("click", event => {{
  if (event.target.closest("[data-close-tip]")) closeTip();
}});
document.querySelectorAll("[data-download]").forEach(btn => {{
  btn.addEventListener("click", () => downloadGraph(btn.dataset.download));
}});
document.querySelector("[data-download-tsv]")?.addEventListener("click", downloadCurrentTsv);
document.querySelectorAll("[data-t-mode]").forEach(btn => {{
  btn.addEventListener("click", () => {{
    state.tMode = +btn.dataset.tMode;
    document.querySelectorAll("[data-t-mode]").forEach(b => b.setAttribute("aria-pressed", String(b === btn)));
    render();
  }});
}});
document.querySelector("[data-toffoli-per-us]")?.addEventListener("input", event => {{
  const value = Number(event.target.value);
  state.toffoliPerUs = Number.isFinite(value) && value > 0 ? value : 0;
  render();
}});
document.querySelectorAll("[data-category]").forEach(input => {{
  input.addEventListener("change", () => {{
    if (input.checked) state.categories.add(input.dataset.category);
    else state.categories.delete(input.dataset.category);
    render();
  }});
}});
window.addEventListener("resize", render);
render();
</script>
"""
    return f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>量子リソース見積もりグラフ</title>
<style>{css}</style>
</head>
<body>
<main class="page">
  <div class="topbar">
    <div>
      <h1 class="title">量子リソース見積もりグラフ</h1>
      <p class="subtitle">{AI_EXTRACTION_NOTICE}</p>
      <p class="subtitle">横軸は報告論理量子ビット数、縦軸はToffoli換算ゲート数または論文が報告した論理ゲート数。どちらも対数軸で、論理量子ビット数は1e9以下を表示しています。</p>
    </div>
    <div class="controls" aria-label="graph controls">
      <div class="segmented" aria-label="Tゲート換算">
        <button type="button" data-t-mode="4" aria-pressed="true">T/4</button>
        <button type="button" data-t-mode="2" aria-pressed="false">T/2</button>
      </div>
      <label class="rate-control">Toffoli/us <input type="number" data-toffoli-per-us min="0.001" step="0.1" value="1" inputmode="decimal"></label>
      <button type="button" class="action" data-download="svg">SVG保存</button>
      <button type="button" class="action" data-download="png">PNG保存</button>
      <button type="button" class="action" data-download-tsv>TSV保存</button>
      <label class="check"><input type="checkbox" data-category="chemistry" checked><span class="marker chemistry"></span>量子化学・量子シミュレーション</label>
      <label class="check"><input type="checkbox" data-category="crypto" checked><span class="marker crypto"></span>素因数分解・暗号系</label>
      <label class="check"><input type="checkbox" data-category="other" checked><span class="marker other"></span>その他</label>
    </div>
  </div>
  <div class="layout">
    <section class="chart-card" aria-label="resource estimate scatter plot">
      <div class="chart-wrap">
        <svg class="chart" role="img" aria-label="論理量子ビット数と論理ゲート数の散布図"><g class="plot"></g></svg>
        <div class="empty">表示できる点がありません。</div>
      </div>
    </section>
    <aside class="side">
      <h2>このグラフの読み方</h2>
      <p>横軸は各論文が報告した論理量子ビット数、縦軸は原則としてToffoli換算ゲート数です。Toffoli/T/CCZのいずれも報告されていない場合は、論文が報告した論理ゲート数を換算せずに表示します。論理量子ビット数が報告されていない見積もりと、論理量子ビット数が1e6を超える見積もりは表示していません。</p>
      <p>この図は、論文が報告した論理リソース見積もりを比較しやすく配置したものです。各点は量子計算が古典計算より速いことや、実用的な量子加速が得られることを示すものではありません。量子加速の有無は、問題設定、入出力、精度、状態準備、読み出し、古典アルゴリズム、ハードウェア仮定などを含めて別途評価する必要があります。</p>
      <ul>
        <li>Toffoli数がある場合は、その値をそのまま使います。</li>
        <li>Toffoli数がなくTゲート数がある場合は、既定ではT/4でToffoli換算します。この換算は <a href="https://arxiv.org/pdf/2602.11457#page=18">Webster et al. 2026</a>、<a href="https://arxiv.org/pdf/2404.16351#page=5">QREChem 2024</a>、<a href="https://arxiv.org/pdf/2007.14460#page=49">von Burg et al. 2020</a> の記述に沿ったものです。</li>
        <li>T/2は <a href="https://arxiv.org/pdf/2011.03494#page=7">Lee et al. 2020</a> のようなsurface-codeコスト寄りの見方を確認するための参考表示です。</li>
        <li>CCZ数が明示されている場合は、1 CCZを1 Toffoli相当として扱っています。</li>
        <li><a href="https://arxiv.org/pdf/2605.30967#page=4">Abe et al. 2026</a> のPauli/RZ rotation数とRZ layer depthは、<a href="https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/pull/2">HIROMU1015 PR #2</a> のBETA=1.56、target error=CA/10、DECOMPO_NUM、PF_RZ_LAYER、alpha cacheに基づく再計算値を使っています。Tゲート数は <a href="https://arxiv.org/abs/1403.2975">Ross-Selinger 2014</a> のancillaなしClifford+TによるRz合成を仮定し、epsilon=1e-10で平均99.6578428466209 T/Rzとして換算しています。</li>
        <li>中抜きの菱形は、block-encodingやQSVTなどのサブルーチン単体の資源見積もりで、問題全体のend-to-end資源ではない点です。</li>
        <li>Pauli rotation数、RZZ数、その他の論理ゲート数しか報告されていない行は、換算せずに報告値をそのまま縦軸に置いています。</li>
        <li>論理量子ビット数は論文内の報告値です。レジスタ、ancilla、layout、routing、factoryなどの含まれ方は論文により異なります。</li>
      </ul>
      <p>上部のToffoli/usに処理レートを入れると、各点の縦軸値をそのレートで割った概算時間を右軸と詳細表示に表示します。換算なしの報告論理ゲート数に対する時間表示は参考値です。</p>
      <p>点にマウスを合わせると詳細を表示し、クリックすると表示を固定できます。固定表示は×ボタンで閉じられます。</p>
      <p>誤りや追加情報の報告は <a href="https://github.com/kosukemtr/moonshot-website/issues/new?title=%E9%87%8F%E5%AD%90%E3%83%AA%E3%82%BD%E3%83%BC%E3%82%B9%E8%A6%8B%E7%A9%8D%E3%82%82%E3%82%8A%E3%82%B0%E3%83%A9%E3%83%95%E3%81%AE%E4%BF%AE%E6%AD%A3%E6%8F%90%E6%A1%88&amp;body=%23%23+%E4%BF%AE%E6%AD%A3%E3%81%97%E3%81%9F%E3%81%84%E7%82%B9%0A%0A%E4%BE%8B%3A+%E8%AB%96%E6%96%87%E5%90%8D%E3%80%81%E3%83%97%E3%83%AD%E3%83%83%E3%83%88%E7%82%B9%E3%80%81%E6%95%B0%E5%80%A4%E3%80%81%E6%8F%9B%E7%AE%97%E3%83%AB%E3%83%BC%E3%83%AB%E3%81%AA%E3%81%A9%0A%0A%23%23+%E8%A9%B2%E5%BD%93%E3%81%99%E3%82%8B%E8%AB%96%E6%96%87%E3%83%BB%E3%83%87%E3%83%BC%E3%82%BF%0A%0A-+%E8%AB%96%E6%96%87%3A%0A-+%E5%AF%BE%E8%B1%A1%E3%82%B5%E3%82%A4%E3%82%BA%3A%0A-+%E7%8F%BE%E5%9C%A8%E8%A1%A8%E7%A4%BA%E3%81%95%E3%82%8C%E3%81%A6%E3%81%84%E3%82%8B%E5%80%A4%3A%0A-+%E6%AD%A3%E3%81%97%E3%81%84%E3%81%A8%E6%80%9D%E3%81%86%E5%80%A4%3A%0A%0A%23%23+%E6%A0%B9%E6%8B%A0%0A%0A%E8%AB%96%E6%96%87%E4%B8%AD%E3%81%AE%E3%83%9A%E3%83%BC%E3%82%B8%E3%80%81%E8%A1%A8%E3%80%81%E5%BC%8F%E3%80%81%E3%81%BE%E3%81%9F%E3%81%AF%E8%A3%9C%E8%B6%B3%E8%AA%AC%E6%98%8E%E3%81%B8%E3%81%AE%E3%83%AA%E3%83%B3%E3%82%AF%E3%82%92%E8%B2%BC%E3%81%A3%E3%81%A6%E3%81%8F%E3%81%A0%E3%81%95%E3%81%84%E3%80%82%0A%0A%23%23+%E8%A3%9C%E8%B6%B3%0A%0A%E5%BF%85%E8%A6%81%E3%81%AA%E3%82%89%E8%87%AA%E7%94%B1%E3%81%AB%E8%BF%BD%E8%A8%98%E3%81%97%E3%81%A6%E3%81%8F%E3%81%A0%E3%81%95%E3%81%84%E3%80%82%0A" target="_blank" rel="noopener">下書き入りのGitHub Issue</a> からお願いします。</p>
    </aside>
  </div>
  <p class="footer-note">注: このグラフは論文間の大まかな位置関係を見るためのものです。読みやすさのため、論理量子ビット数が1e6を超える点は表示範囲外にしています。換算方法や報告値に含まれる前提が異なる点に注意してください。</p>
</main>
<div class="tooltip" role="tooltip"></div>
{script}
</body>
</html>
"""


def markdown_table(header: list[str], rows: list[list[str]], align: list[str] | None = None) -> str:
    if align is None:
        align = ["---"] * len(header)
    if len(align) != len(header):
        raise ValueError("alignment length does not match header")
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join(align) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(lines)


def build_markdown(base: Path, main_header: list[str], main_rows: list[list[str]]) -> str:
    preamble = read_text(base / "content" / "preamble.md")
    between = read_text(base / "content" / "between_tables.md")
    after = read_text(base / "content" / "after_calibration_table.md")
    cal_header, cal_rows = read_tsv(base / "data" / "physical_conversion_calibration.tsv")
    validate_numeric_only_columns(cal_header, cal_rows)
    validate_numeric_semantics(cal_header, cal_rows)

    parts = [
        preamble,
        markdown_table(main_header, main_rows, MAIN_ALIGN),
        between,
        markdown_table(cal_header, cal_rows),
        after,
    ]
    return "\n\n".join(part for part in parts if part) + "\n"


def inline_markdown(s: str) -> str:
    placeholders: list[str] = []

    def code_repl(match: re.Match[str]) -> str:
        placeholders.append("<code>" + html.escape(match.group(1)) + "</code>")
        return f"@@CODE{len(placeholders) - 1}@@"

    s = re.sub(r"`([^`]+)`", code_repl, s)
    out: list[str] = []
    pos = 0
    for match in re.finditer(r"\[([^\]]+)\]\(([^)]+)\)", s):
        out.append(html.escape(s[pos : match.start()]))
        raw_label = match.group(1)
        label = html.escape(raw_label)
        href = html.escape(match.group(2), quote=True)
        preview_href = preview_href_for_link(match.group(2), raw_label)
        for i, value in enumerate(placeholders):
            label = label.replace(f"@@CODE{i}@@", value)
        if preview_href:
            preview = html.escape(preview_href, quote=True)
            out.append(f'<a href="{href}" data-preview-src="{preview}">{label}</a>')
        else:
            out.append(f'<a href="{href}">{label}</a>')
        pos = match.end()
    out.append(html.escape(s[pos:]))
    rendered = "".join(out)
    for i, value in enumerate(placeholders):
        rendered = rendered.replace(f"@@CODE{i}@@", value)
    return rendered


def column_class(name: str) -> str:
    if name in {"発表日（初出）"}:
        return "col-date"
    if name in {"解ける問題", "論文", "対象サイズ", "見積もりの種類", "デバイス", "誤り訂正符号", "物理量子ビット種"}:
        return "col-text"
    if name in POPOVER_COLUMNS:
        return "col-long"
    return "col-num"


def table_cell(column: str, cell: str) -> str:
    rendered = inline_markdown(cell)
    classes = ["cell", column_class(column)]
    if column in POPOVER_COLUMNS and cell != "NA":
        return (
            f'<td class="{" ".join(classes)} has-popover" tabindex="0">'
            f'<div class="cell-preview">{rendered}</div>'
            f'<div class="cell-popover" role="tooltip">{rendered}</div>'
            "</td>"
        )
    return f'<td class="{" ".join(classes)}">{rendered}</td>'


def flush_table(lines: list[str], body: list[str]) -> None:
    if not lines:
        return
    header = [cell.strip() for cell in lines[0].strip("|").split("|")]
    colgroup = "<colgroup>" + "".join(f'<col class="{column_class(cell)}">' for cell in header) + "</colgroup>"
    head_cells = "".join(f'<th class="{column_class(cell)}">{inline_markdown(cell)}</th>' for cell in header)
    body.append(
        '<div class="table-shell">'
        '<div class="table-head-wrap" aria-hidden="true"><table class="table-head">'
        + colgroup
        + "<thead><tr>"
        + head_cells
        + "</tr></thead></table></div>"
        '<div class="table-wrap"><table class="table-body">'
        + colgroup
        + "<tbody>"
    )
    for row in lines[2:]:
        if not row.strip().startswith("|"):
            continue
        cells = [cell.strip() for cell in row.strip("|").split("|")]
        body.append("<tr>" + "".join(table_cell(column, cell) for column, cell in zip(header, cells)) + "</tr>")
    body.append("</tbody></table></div></div>")


def markdown_to_html(markdown: str) -> str:
    body: list[str] = []
    table_lines: list[str] = []
    in_ul = False

    def close_ul() -> None:
        nonlocal in_ul
        if in_ul:
            body.append("</ul>")
            in_ul = False

    for line in markdown.splitlines():
        if line.startswith("|"):
            close_ul()
            table_lines.append(line)
            continue
        if table_lines:
            flush_table(table_lines, body)
            table_lines = []
        if not line.strip():
            close_ul()
            continue
        if line.startswith("# "):
            close_ul()
            body.append(f"<h1>{inline_markdown(line[2:].strip())}</h1>")
            continue
        if line.startswith("## "):
            close_ul()
            body.append(f"<h2>{inline_markdown(line[3:].strip())}</h2>")
            continue
        if line.startswith("### "):
            close_ul()
            body.append(f"<h3>{inline_markdown(line[4:].strip())}</h3>")
            continue
        if line.startswith("- "):
            if not in_ul:
                body.append("<ul>")
                in_ul = True
            body.append(f"<li>{inline_markdown(line[2:].strip())}</li>")
            continue
        close_ul()
        cls = ' class="meta"' if line.startswith(("作成日:", "対象:", "方針:")) else ""
        body.append(f"<p{cls}>{inline_markdown(line.strip())}</p>")
    if table_lines:
        flush_table(table_lines, body)
    close_ul()

    css = """.resource-estimates{--paper:#fff;--muted:#5d687a;--line:#d9deea;--head:#eef3f8;--accent:#0b6b74;--accent-soft:#e4f4f2;line-height:1.55}.resource-estimates h1{margin:0 0 8px;font-size:28px;letter-spacing:0}.resource-estimates h2{margin:22px 0 10px;font-size:20px}.resource-estimates h3{margin:18px 0 6px;font-size:16px}.resource-estimates .meta{margin:2px 0;color:var(--muted);font-size:14px}.resource-estimates .table-shell{background:var(--paper);border:1px solid var(--line);border-radius:8px;margin:14px 0;max-width:100%;position:relative}.resource-estimates .table-head-wrap{position:sticky;top:0;z-index:50;overflow:hidden;background:var(--head);border-bottom:1px solid var(--line);border-radius:8px 8px 0 0}.resource-estimates .table-wrap{overflow-x:auto;overflow-y:visible;max-width:100%;position:relative}.resource-estimates .table-head{transform-origin:left top;will-change:transform}.resource-estimates table{border-collapse:collapse;min-width:1240px;width:100%;table-layout:fixed;font-size:12px}.resource-estimates th,.resource-estimates td{border-bottom:1px solid var(--line);border-right:1px solid var(--line);padding:7px 6px;vertical-align:top;overflow-wrap:anywhere}.resource-estimates th{background:var(--head);text-align:left;font-weight:700;line-height:1.25}.resource-estimates .table-body tr:last-child td{border-bottom:0}.resource-estimates td:last-child,.resource-estimates th:last-child{border-right:0}.resource-estimates .col-date{width:7ch}.resource-estimates .col-num{width:7.5ch;text-align:right}.resource-estimates td.col-num{white-space:nowrap;overflow-wrap:normal}.resource-estimates .col-text{width:8.5ch}.resource-estimates .col-long{width:9ch}.resource-estimates a{color:var(--accent);text-decoration-thickness:1px;text-underline-offset:2px}.resource-estimates ul{margin:8px 0 0;padding-left:20px}.resource-estimates li{margin:5px 0}.resource-estimates code{background:#f1f3f7;border:1px solid #e3e6ef;border-radius:4px;padding:1px 4px}.resource-estimates .note{background:var(--accent-soft);border:1px solid #b9dfdb;border-radius:8px;padding:12px 14px;margin:18px 0}.resource-estimates .cell-preview{display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:3;line-clamp:3;overflow:hidden;max-height:4.8em}.resource-estimates .has-popover{cursor:help}.resource-estimates .has-popover:focus{outline:2px solid var(--accent);outline-offset:-2px}.resource-estimates .cell-popover{display:none}.pdf-preview-layer{box-sizing:border-box;display:none;position:fixed;z-index:100000;right:18px;top:84px;width:min(720px,calc(100vw - 36px));max-height:min(760px,calc(100vh - 108px));overflow:auto;padding:10px;background:#fff;border:1px solid #aeb8c8;border-radius:8px;box-shadow:0 18px 48px rgba(20,31,50,.24)}.pdf-preview-layer.is-open{display:block}.pdf-preview-layer img{display:block;width:100%;height:auto}.pdf-preview-caption{margin:0 0 8px;color:#5d687a;font-size:12px}.resource-popover-layer{box-sizing:border-box;display:none;position:fixed;z-index:99999;left:50%;top:84px;transform:translateX(-50%);width:min(720px,calc(100vw - 32px));max-height:min(420px,60vh);overflow:auto;padding:12px 14px;background:#fff;border:1px solid #aeb8c8;border-radius:8px;box-shadow:0 16px 42px rgba(20,31,50,.22);text-align:left;line-height:1.5}.resource-popover-layer.is-open{display:block}.resource-popover-layer a{color:#0b6b74;text-decoration-thickness:1px;text-underline-offset:2px}@media(max-width:700px){.resource-estimates h1{font-size:24px}.resource-estimates .table-shell{border-radius:6px}.resource-estimates .table-head-wrap{border-radius:6px 6px 0 0}.resource-estimates table{min-width:1120px;font-size:11px}.resource-estimates th,.resource-estimates td{padding:6px 5px}.resource-popover-layer{left:12px;right:12px;top:auto;bottom:16px;transform:none;width:auto;max-height:45vh}.pdf-preview-layer{left:10px;right:10px;top:10px;bottom:10px;width:auto;max-height:none}}"""
    script = """<script>
(function(){
  var layer;
  var hideTimer;
  function ensureLayer(){
    if(layer){ return layer; }
    layer = document.createElement('div');
    layer.className = 'resource-popover-layer';
    layer.setAttribute('role', 'tooltip');
    document.body.appendChild(layer);
    layer.addEventListener('mouseenter', function(){ clearTimeout(hideTimer); });
    layer.addEventListener('mouseleave', scheduleHide);
    return layer;
  }
  function showFromCell(cell){
    var source = cell.querySelector('.cell-popover');
    if(!source){ return; }
    var popup = ensureLayer();
    clearTimeout(hideTimer);
    popup.innerHTML = source.innerHTML;
    popup.classList.add('is-open');
  }
  function scheduleHide(){
    clearTimeout(hideTimer);
    hideTimer = setTimeout(function(){
      if(layer){ layer.classList.remove('is-open'); }
    }, 120);
  }
  document.querySelectorAll('.has-popover').forEach(function(cell){
    cell.addEventListener('mouseenter', function(){ showFromCell(cell); });
    cell.addEventListener('mouseleave', scheduleHide);
    cell.addEventListener('focusin', function(){ showFromCell(cell); });
    cell.addEventListener('focusout', scheduleHide);
  });
  var previewLayer;
  var previewHideTimer;
  function ensurePreviewLayer(){
    if(previewLayer){ return previewLayer; }
    previewLayer = document.createElement('div');
    previewLayer.className = 'pdf-preview-layer';
    document.body.appendChild(previewLayer);
    previewLayer.addEventListener('mouseenter', function(){ clearTimeout(previewHideTimer); });
    previewLayer.addEventListener('mouseleave', hidePreviewSoon);
    return previewLayer;
  }
  function showPreview(link){
    var src = link.getAttribute('data-preview-src');
    if(!src){ return; }
    var preview = ensurePreviewLayer();
    clearTimeout(previewHideTimer);
    preview.innerHTML = '<p class="pdf-preview-caption">確認済みソース画像。クリックするとPDFを開きます。</p><img alt="source preview" src="' + src + '">';
    preview.classList.add('is-open');
  }
  function hidePreviewSoon(){
    clearTimeout(previewHideTimer);
    previewHideTimer = setTimeout(function(){
      if(previewLayer){ previewLayer.classList.remove('is-open'); }
    }, 140);
  }
  document.addEventListener('mouseover', function(event){
    var link = event.target.closest && event.target.closest('a[data-preview-src]');
    if(link){ showPreview(link); }
  });
  document.addEventListener('mouseout', function(event){
    var link = event.target.closest && event.target.closest('a[data-preview-src]');
    if(link){ hidePreviewSoon(); }
  });
  document.addEventListener('focusin', function(event){
    var link = event.target.closest && event.target.closest('a[data-preview-src]');
    if(link){ showPreview(link); }
  });
  document.addEventListener('focusout', function(event){
    var link = event.target.closest && event.target.closest('a[data-preview-src]');
    if(link){ hidePreviewSoon(); }
  });
  document.querySelectorAll('.table-shell').forEach(function(shell){
    var wrap = shell.querySelector('.table-wrap');
    var head = shell.querySelector('.table-head');
    if(!wrap || !head){ return; }
    function syncHead(){
      head.style.transform = 'translateX(' + (-wrap.scrollLeft) + 'px)';
    }
    wrap.addEventListener('scroll', syncHead, { passive: true });
    window.addEventListener('resize', syncHead);
    syncHead();
  });
  document.addEventListener('keydown', function(event){
    if(event.key === 'Escape' && layer){ layer.classList.remove('is-open'); }
    if(event.key === 'Escape' && previewLayer){ previewLayer.classList.remove('is-open'); }
  });
  document.addEventListener('scroll', function(){
    if(layer){ layer.classList.remove('is-open'); }
    if(previewLayer){ previewLayer.classList.remove('is-open'); }
  }, true);
})();
</script>"""
    return (
        "---\n"
        "layout: page\n"
        "title: 量子リソース見積もりメモ\n"
        "permalink: /resource-estimates/\n"
        "---\n"
        f"<style>{css}</style>\n"
        f'<div class="resource-estimates" data-numeric-json="data/{NUMERIC_JSON_NAME}">\n'
        '<p class="note">表中リンクはPDFの該当ページを開く形式です。PDFビューアによってはページ指定が効かない場合があります。</p>\n'
        + "\n".join(body)
        + "\n</div>\n"
        + script
        + "\n"
    )


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.tr = 0
        self.th = 0
        self.td = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            self.links.append(dict(attrs).get("href") or "")
        elif tag == "tr":
            self.tr += 1
        elif tag == "th":
            self.th += 1
        elif tag == "td":
            self.td += 1


def validate_html(base: Path, rendered: str) -> None:
    parser = LinkParser()
    parser.feed(rendered)
    missing = []
    for href in parser.links:
        if href.startswith("references/"):
            local = base / href.split("#", 1)[0]
            if not local.exists():
                missing.append(href)
    if missing:
        raise FileNotFoundError("missing reference links: " + ", ".join(missing[:10]))
    if parser.tr == 0 or parser.td == 0:
        raise ValueError("rendered HTML appears to contain no table rows")


def english_public_graph_html(html_text: str) -> str:
    replacements = [
        ('<html lang="ja">', '<html lang="en">'),
        (AI_EXTRACTION_NOTICE, AI_EXTRACTION_NOTICE_EN),
        ("量子リソース見積もりグラフ", "Quantum Resource Estimate Graph"),
        ("量子・古典計算時間比と生デバイス性能指標", "Quantum-Classical Runtime Ratio and Raw Device Performance"),
        (
            "横軸は報告論理量子ビット数、縦軸はToffoli換算ゲート数または論文が報告した論理ゲート数。どちらも対数軸で、論理量子ビット数は1e9以下を表示しています。",
            "The x-axis shows reported logical qubits, and the y-axis shows Toffoli-equivalent gates or reported logical gate counts. Both axes are logarithmic, and entries with at most 1e9 logical qubits are shown.",
        ),
        (
            "横軸は物理量子ビット数 / 物理エラー率、縦軸は古典計算時間 / 量子計算時間です。RSA系の古典時間はGNFS主項をRSA-250実績に合わせて外挿しています。",
            "The x-axis shows physical qubits divided by physical error rate, and the y-axis shows classical runtime divided by quantum runtime. RSA classical runtimes are extrapolated from the GNFS leading term normalized to RSA-250.",
        ),
        ("SVG保存", "Save SVG"),
        ("PNG保存", "Save PNG"),
        ("TSV保存", "Save TSV"),
        ("Tゲート換算", "T-gate conversion"),
        ("量子化学・量子シミュレーション", "Quantum chemistry and simulation"),
        ("素因数分解・暗号系", "Factoring and cryptography"),
        ("その他", "Other"),
        ("サブルーチンのみ", "Subroutine only"),
        ("実験実現あり", "Experiment performed"),
        ("表示できる点がありません。", "No points to display."),
        ("このグラフの読み方", "How to Read This Graph"),
        (
            "横軸は各論文が報告した論理量子ビット数、縦軸は原則としてToffoli換算ゲート数です。Toffoli/T/CCZのいずれも報告されていない場合は、論文が報告した論理ゲート数を換算せずに表示します。論理量子ビット数が報告されていない見積もりと、論理量子ビット数が1e6を超える見積もりは表示していません。",
            "The x-axis is the number of logical qubits reported by each paper. The y-axis is generally a Toffoli-equivalent gate count. If no Toffoli, T, or CCZ count is reported, the reported logical gate count is plotted without conversion. Estimates without reported logical qubits and estimates above 1e6 logical qubits are not shown in this view.",
        ),
        (
            "この図は、論文が報告した論理リソース見積もりを比較しやすく配置したものです。各点は量子計算が古典計算より速いことや、実用的な量子加速が得られることを示すものではありません。量子加速の有無は、問題設定、入出力、精度、状態準備、読み出し、古典アルゴリズム、ハードウェア仮定などを含めて別途評価する必要があります。",
            "This figure is intended to make reported logical resource estimates easier to compare. A point on the graph does not imply that the quantum computation is faster than a classical computation, nor that practical quantum speedup is achieved. Quantum speedup must be evaluated separately, including the problem setting, input/output model, precision, state preparation, readout, classical algorithms, and hardware assumptions.",
        ),
        ("Toffoli数がある場合は、その値をそのまま使います。", "If a Toffoli count is available, it is used directly."),
        ("Toffoli数がなくTゲート数がある場合は、既定ではT/4でToffoli換算します。この換算は", "If no Toffoli count is available but a T-gate count is, the default conversion is T/4. This convention follows descriptions in"),
        ("の記述に沿ったものです。", "."),
        ("T/2は", "T/2 is included as an alternative view closer to surface-code cost assumptions such as"),
        ("のようなsurface-codeコスト寄りの見方を確認するための参考表示です。", "."),
        ("CCZ数が明示されている場合は、1 CCZを1 Toffoli相当として扱っています。", "If a CCZ count is explicitly reported, 1 CCZ is treated as 1 Toffoli equivalent."),
        ("中抜きの菱形は、block-encodingやQSVTなどのサブルーチン単体の資源見積もりで、問題全体のend-to-end資源ではない点です。", "Open diamonds mark subroutine-only resource estimates, such as block-encoding or QSVT subroutines, rather than end-to-end resources for the full problem."),
        ("Pauli rotation数、RZZ数、その他の論理ゲート数しか報告されていない行は、換算せずに報告値をそのまま縦軸に置いています。", "Rows that only report Pauli rotations, RZZ gates, or other logical gate counts are plotted as reported without conversion."),
        ("論理量子ビット数は論文内の報告値です。レジスタ、ancilla、layout、routing、factoryなどの含まれ方は論文により異なります。", "Logical qubit counts are the values reported in the papers. What is included, such as registers, ancillae, layout, routing, or factories, differs by paper."),
        ("上部のToffoli/usに処理レートを入れると、各点の縦軸値をそのレートで割った概算時間を右軸と詳細表示に表示します。換算なしの報告論理ゲート数に対する時間表示は参考値です。", "Enter a processing rate in Toffoli/us to show an approximate runtime on the right axis and in the point details. Runtime labels for unconverted reported logical gate counts are only rough references."),
        ("点にマウスを合わせると詳細を表示し、クリックすると表示を固定できます。固定表示は×ボタンで閉じられます。", "Hover over a point to show details. Click a point to pin the details, and close the pinned panel with the × button."),
        ("誤りや追加情報の報告は ", "Please report corrections or additional information via "),
        (" からお願いします。", "."),
        ("下書き入りのGitHub Issue", "this prefilled GitHub Issue"),
        ("注: このグラフは論文間の大まかな位置関係を見るためのものです。読みやすさのため、論理量子ビット数が1e6を超える点は表示範囲外にしています。換算方法や報告値に含まれる前提が異なる点に注意してください。", "Note: this graph is meant to show broad relationships across papers. For readability, points above 1e6 logical qubits are outside the displayed range. Conversion rules and reporting assumptions differ across papers."),
        ("RSA古典時間の概算", "RSA Classical Runtime Estimate"),
        ("RSA系の古典計算時間は、General Number Field Sieve (GNFS) の主項を使って概算しています。RSA modulusのbit長を b とし、N ≃ 2^b と近似します。", "Classical runtimes for RSA entries are estimated using the leading term of the General Number Field Sieve (GNFS). The RSA modulus bit length is b, with N approximated as 2^b."),
        ("基準点は ", "The reference point is "),
        ("です。RSA-250 は250 decimal digits、約829 bitsで、公開報告の約2700 core-yearsを T_829 として使います。", ". RSA-250 has 250 decimal digits, about 829 bits, and the public report of about 2700 core-years is used as T_829."),
        ("グラフの古典計算時間は、このcore-year値を100万 coreで並列実行した壁時計時間として秒へ換算しています。実際の古典実行時間は実装、ハードウェア、並列化、メモリ、線形代数部の扱いで変わります。", "The graph converts this core-year estimate to wall-clock seconds assuming parallel execution on one million cores. Actual classical runtimes depend on implementation, hardware, parallelism, memory, and the treatment of the linear-algebra stage."),
        ("参考値", "Reference Values"),
        ("bit長", "bits"),
        ("100万 core 秒換算", "seconds at 1M cores"),
        ("表示する点", "Displayed Points"),
        ("量子計算時間、物理量子ビット数、物理エラー率がある行だけを表示します。", "Only rows with quantum runtime, physical qubits, and physical error rate are shown."),
        ("RSA系は上記GNFS外挿で古典時間を生成します。", "For RSA entries, classical runtimes are generated using the GNFS extrapolation above."),
        ("RSA以外は、元データに古典計算時間または古典/量子時間比がある場合だけ表示します。", "For non-RSA entries, rows are shown only when the source data includes a classical runtime or a classical/quantum runtime ratio."),
        ("黒い太枠で強調した点は、元論文で実際に実験として実施されたエントリです。", "Points with a thick black outline are entries actually performed as experiments in the source paper."),
        ("横軸は誤り訂正前の生デバイス性能を粗く表す補助指標として、物理量子ビット数を物理エラー率で割った値を使っています。誤り訂正なしのランダム量子回路サンプリング実験では、論文記載の代表的な同時2量子ビットゲートエラーを物理エラー率として使っています。点にマウスを合わせると詳細を表示し、クリックすると表示を固定できます。固定表示は×ボタンで閉じられます。", "The x-axis uses physical qubits divided by physical error rate as a rough auxiliary indicator of raw, pre-error-correction device performance. For random-circuit-sampling experiments without error correction, the representative simultaneous two-qubit gate error reported in the paper is used as the physical error rate. Hover over a point to show details. Click a point to pin the details, and close the pinned panel with the × button."),
        ("注: この図は古典/量子の大まかな速度比を見るための補助図です。RSAの古典時間は論文記載値ではなく、GNFS漸近主項をRSA-250実績に正規化した概算です。縦軸は10^25で表示を打ち切り、これを超える点は非表示にしています。縦軸の下限は表示対象データに合わせて自動で決まります。", "Note: this figure is an auxiliary view of rough classical/quantum speed ratios. RSA classical runtimes are not paper-reported values; they are estimates from the GNFS asymptotic leading term normalized to RSA-250. The y-axis is capped at 10^25, and points above this value are hidden. The lower y-axis bound is chosen automatically from the displayed data."),
        ("報告論理量子ビット数", "Reported logical qubits"),
        ("Toffoli換算または報告論理ゲート数", "Toffoli-equivalent or reported logical gates"),
        ("概算時間", "Approx. runtime"),
        ("物理量子ビット数 / 物理エラー率", "Physical qubits / physical error rate"),
        ("古典計算時間 / 量子計算時間", "Classical runtime / quantum runtime"),
        ("物理量子ビット数/物理エラー率と古典計算時間/量子計算時間比の散布図", "Scatter plot of physical qubits divided by physical error rate and classical/quantum runtime ratio"),
        ("論理量子ビット数と論理ゲート数の散布図", "Scatter plot of logical qubits and logical gate counts"),
        ("古典=量子", "classical = quantum"),
        ("分類", "Category"),
        ("問題", "Problem"),
        ("対象", "Target"),
        ("見積もり", "Estimate"),
        ("実験実施", "Experiment"),
        ("論理量子ビット", "Logical qubits"),
        ("縦軸値", "Y-axis value"),
        ("レート換算時間", "Runtime from rate"),
        ("物理量子ビット/物理エラー率", "Physical qubits / physical error rate"),
        ("物理量子ビット", "Physical qubits"),
        ("量子計算時間", "Quantum runtime"),
        ("古典計算時間", "Classical runtime"),
        ("古典/量子比", "Classical/quantum ratio"),
        ("古典時間の扱い", "Classical runtime treatment"),
        ("物理エラー率", "Physical error rate"),
        ("cycle/測定時間", "cycle/measurement time"),
        ("実行時間(s)", "Runtime (s)"),
        ("デバイス", "Device"),
        ("誤り訂正符号", "Error-correction code"),
        ("物理量子ビット種", "Physical qubit type"),
        ("Toffoli数", "Toffoli count"),
        ("Tゲート数から換算", "Converted from T-gate count"),
        ("Tゲート数", "T-gate count"),
        ("CCZ数", "CCZ count"),
        ("報告論理ゲート数（換算なし）", "Reported logical gates (unconverted)"),
        ("元データ/論文記載", "source data / paper-reported"),
        ("GNFS外挿", "GNFS extrapolation"),
        ("RSA-250 の分解実績", "RSA-250 factorization record"),
        ("</a>、<a", "</a>, <a"),
        ("</a> .", "</a>."),
        (
            '<a href="https://arxiv.org/pdf/2605.30967#page=4">Abe et al. 2026</a> のPauli/RZ rotation数とRZ layer depthは、<a href="https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/pull/2">HIROMU1015 PR #2</a> のBETA=1.56、target error=CA/10、DECOMPO_NUM、PF_RZ_LAYER、alpha cacheに基づく再計算値を使っています。T-gate countは <a href="https://arxiv.org/abs/1403.2975">Ross-Selinger 2014</a> のancillaなしClifford+TによるRz合成を仮定し、epsilon=1e-10で平均99.6578428466209 T/Rzとして換算しています。',
            '<a href="https://arxiv.org/pdf/2605.30967#page=4">Abe et al. 2026</a>\'s Pauli/RZ rotation counts and RZ layer depth use recalculated values from <a href="https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/pull/2">HIROMU1015 PR #2</a>, with BETA=1.56, target error=CA/10, DECOMPO_NUM, PF_RZ_LAYER, and alpha cache. T-gate counts assume <a href="https://arxiv.org/abs/1403.2975">Ross-Selinger 2014</a>\'s ancilla-free Clifford+T Rz synthesis, using an average 99.6578428466209 T gates per Rz at epsilon=1e-10.',
        ),
        (
            "Pauli rotation数、RZZ数、Otherの論理ゲート数しか報告されていない行は、換算せずに報告値をそのまま縦軸に置いています。",
            "Rows that only report Pauli rotations, RZZ gates, or other logical gate counts are plotted as reported without conversion.",
        ),
        ('label.replace("・量子シミュレーション", "")', 'label.replace(" and simulation", "")'),
        ('d.isExperiment ? "あり" : "なし"', 'd.isExperiment ? "yes" : "no"'),
    ]
    for old, new in replacements:
        html_text = html_text.replace(old, new)
    return html_text


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    base = args.base.resolve()

    main_header, main_rows = load_main_rows(base)
    markdown = build_markdown(base, main_header, main_rows)
    write_numeric_json(base, main_header, main_rows)
    html_text = markdown_to_html(markdown)
    graph_html = build_graph_html(base, main_header, main_rows)
    physical_graph_html = build_physical_graph_html(base, main_header, main_rows)
    speedup_graph_html = build_speedup_graph_html(base, main_header, main_rows)
    graph_html_en = english_public_graph_html(graph_html)
    speedup_graph_html_en = english_public_graph_html(speedup_graph_html)
    validate_html(base, html_text)

    (base / "quantum_resource_estimates.html").write_text(html_text, encoding="utf-8")
    (base / GRAPH_HTML_NAME).write_text(graph_html, encoding="utf-8")
    (base / GRAPH_HTML_EN_NAME).write_text(graph_html_en, encoding="utf-8")
    (base / PHYSICAL_GRAPH_HTML_NAME).write_text(physical_graph_html, encoding="utf-8")
    (base / SPEEDUP_GRAPH_HTML_NAME).write_text(speedup_graph_html, encoding="utf-8")
    (base / SPEEDUP_GRAPH_HTML_EN_NAME).write_text(speedup_graph_html_en, encoding="utf-8")
    print(f"read {base / 'data' / ROWS_JSON_NAME}")
    print(f"wrote {base / 'data' / 'resource_estimates.tsv'}")
    print(f"wrote {base / 'data' / NUMERIC_JSON_NAME}")
    print(f"wrote {base / 'quantum_resource_estimates.html'}")
    print(f"wrote {base / GRAPH_HTML_NAME}")
    print(f"wrote {base / GRAPH_HTML_EN_NAME}")
    print(f"wrote {base / PHYSICAL_GRAPH_HTML_NAME}")
    print(f"wrote {base / SPEEDUP_GRAPH_HTML_NAME}")
    print(f"wrote {base / SPEEDUP_GRAPH_HTML_EN_NAME}")


if __name__ == "__main__":
    main()
