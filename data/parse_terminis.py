"""Parse 'Pestanya 3. Terminis' Excel files → terminis_<grau>.csv.

Uses Mitjana P90 — mean excluding the 10% slowest cases.
Chosen because means are additive (sub-phases sum to the total), while
medians are not.
"""
import pandas as pd
from pathlib import Path

SRC = Path.home() / "Desktop" / "Pestanya 3. Terminis" / "Mitjana P90"
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
    for key, fname in FILES.items():
        df = parse(SRC / fname)
        out = OUT / f"terminis_{key}.csv"
        df.to_csv(out, index=False)
        print(f"✓ {out.name} ({len(df)} rows, latest: {df['fecha'].max().date()})")
