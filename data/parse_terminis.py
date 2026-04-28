"""Parse 'Pestanya 3. Terminis' Excel files → terminis_<grau>[_mediana].csv.

Generates two parallel sets:
  - Mitjana P90 → terminis_<grau>.csv         (additive: sub-phases sum to total)
  - Mediana inicials → terminis_<grau>_mediana.csv  (robust to outliers, non-additive)

The dashboard uses mediana for the headline total KPI and Mitjana P90 for
the phase-by-phase breakdown.
"""
import pandas as pd
from pathlib import Path

BASE = Path.home() / "Desktop" / "Pestanya 3. Terminis"
SOURCES = {
    "": BASE / "Mitjana P90",
    "_mediana": BASE / "Mediana inicials",
}
OUT = Path(__file__).parent

MONTH_MAP = {
    "gener": 1, "febrer": 2, "març": 3, "abril": 4, "maig": 5, "juny": 6,
    "juliol": 7, "agost": 8, "setembre": 9, "octubre": 10, "novembre": 11, "desembre": 12,
}

COLS = [
    "any", "mes", "n_resolts", "total",
    "valoracio", "sol_grau", "tram_grau", "val_grau",
    "pia", "capecon", "creacio_pia", "res_pia",
]

FILES = {
    "total": "Total (tots els graus).xlsx",
    "g1": "Grau I.xlsx",
    "g2": "Grau II.xlsx",
    "g3": "Grau III.xlsx",
}


def parse(fp):
    df = pd.read_excel(fp, header=None, skiprows=3)
    df = df.iloc[:, :12]
    df.columns = COLS
    df = df.dropna(subset=["any", "mes"]).copy()
    df["any"] = df["any"].astype(int)
    df["month_num"] = df["mes"].map(MONTH_MAP)
    df["fecha"] = pd.to_datetime(
        df["any"].astype(str) + "-" + df["month_num"].astype(str).str.zfill(2) + "-01"
    )
    df = df.sort_values("fecha")
    for c in COLS[2:]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df[["fecha", "any", "mes", "n_resolts", "total",
               "valoracio", "sol_grau", "tram_grau", "val_grau",
               "pia", "capecon", "creacio_pia", "res_pia"]]


if __name__ == "__main__":
    for suffix, src in SOURCES.items():
        if not src.exists():
            print(f"⚠ skipping {src} (not found)")
            continue
        for key, fname in FILES.items():
            df = parse(src / fname)
            out = OUT / f"terminis_{key}{suffix}.csv"
            df.to_csv(out, index=False)
            print(f"✓ {out.name} ({len(df)} rows, latest: {df['fecha'].max().date()})")
