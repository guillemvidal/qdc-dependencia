#!/usr/bin/env python3
"""
Parse IMSERSO SAAD monthly Excel files and extract key indicators by CCAA.
Outputs three CSVs:
  - imserso_temps.csv: processing times by CCAA and month
  - imserso_pendents.csv: pending cases by CCAA and month
  - imserso_solicituds.csv: applications, resolutions, beneficiaries by CCAA and month
"""

import os
import glob
import re
from datetime import datetime
import openpyxl
import csv

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
IMSERSO_DIR = os.path.join(DATA_DIR, "imserso")
OUTPUT_DIR = DATA_DIR

# Standard CCAA names for normalization
CCAA_NAMES = [
    "Andalucía",
    "Aragón",
    "Asturias, Principado de",
    "Balears, Illes",
    "Canarias",
    "Cantabria",
    "Castilla y León",
    "Castilla - La Mancha",
    "Cataluña",
    "Comunitat Valenciana",
    "Extremadura",
    "Galicia",
    "Madrid, Comunidad de",
    "Murcia, Región de",
    "Navarra, Comunidad Foral de",
    "País Vasco",
    "Rioja, La",
    "Ceuta y Melilla",
]

# Some files use slightly different names (with asterisks, etc.)
def normalize_ccaa(name):
    """Normalize CCAA name by stripping asterisks and extra whitespace."""
    if name is None:
        return None
    name = str(name).strip().rstrip("*").strip()
    # Map known variants
    variants = {
        "Ceuta": "Ceuta y Melilla",
        "Melilla": "Ceuta y Melilla",
        "Castilla y León*": "Castilla y León",
        "Madrid, Comunidad de*": "Madrid, Comunidad de",
        "País Vasco*": "País Vasco",
    }
    return variants.get(name, name)


def get_file_date(filepath):
    """Extract date from filename like estsisaad_20260331.xlsx -> 2026-03-31"""
    m = re.search(r'estsisaad_(\d{8})\.xlsx', os.path.basename(filepath))
    if m:
        d = m.group(1)
        return f"{d[:4]}-{d[4:6]}-{d[6:8]}"
    return None


def read_sheet_rows(wb, sheet_name, max_rows=40):
    """Read rows from a sheet, returning list of lists with values."""
    ws = wb[sheet_name]
    rows = []
    for row in ws.iter_rows(min_row=1, max_row=max_rows, values_only=True):
        rows.append(list(row))
    return rows


def find_ccaa_rows(rows, ccaa_col=1, start_row=0):
    """Find rows containing CCAA data. Returns dict of {ccaa_name: row_values}."""
    result = {}
    for row in rows[start_row:]:
        if row and len(row) > ccaa_col:
            name = normalize_ccaa(row[ccaa_col])
            if name in CCAA_NAMES:
                if name not in result:  # Take first occurrence only
                    result[name] = row
    return result


def safe_float(val):
    """Convert value to float, return None if not possible."""
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def safe_int(val):
    """Convert value to int, return None if not possible."""
    if val is None:
        return None
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None


def parse_temps(wb, file_date):
    """Parse sheet 9TiempoEspera: processing times by CCAA."""
    rows = read_sheet_rows(wb, "9TiempoEspera", max_rows=40)
    ccaa_data = find_ccaa_rows(rows, ccaa_col=1)

    records = []
    for ccaa_name in CCAA_NAMES:
        if ccaa_name not in ccaa_data:
            continue
        row = ccaa_data[ccaa_name]
        records.append({
            "fecha": file_date,
            "ccaa": ccaa_name,
            "n_resol_grado": safe_int(row[3]) if len(row) > 3 else None,
            "tiempo_sol_a_grado_dias": safe_float(row[4]) if len(row) > 4 else None,
            "n_resol_pia": safe_int(row[6]) if len(row) > 6 else None,
            "tiempo_grado_a_pia_dias": safe_float(row[7]) if len(row) > 7 else None,
            "n_resol_pia_total": safe_int(row[9]) if len(row) > 9 else None,
            "tiempo_sol_a_pia_dias": safe_float(row[10]) if len(row) > 10 else None,
        })

    # TOTAL row
    for row in rows:
        if row and len(row) > 1 and row[1] is not None and "TOTAL" in str(row[1]):
            records.append({
                "fecha": file_date,
                "ccaa": "TOTAL",
                "n_resol_grado": safe_int(row[3]) if len(row) > 3 else None,
                "tiempo_sol_a_grado_dias": safe_float(row[4]) if len(row) > 4 else None,
                "n_resol_pia": safe_int(row[6]) if len(row) > 6 else None,
                "tiempo_grado_a_pia_dias": safe_float(row[7]) if len(row) > 7 else None,
                "n_resol_pia_total": safe_int(row[9]) if len(row) > 9 else None,
                "tiempo_sol_a_pia_dias": safe_float(row[10]) if len(row) > 10 else None,
            })
            break

    return records


def parse_pendents(wb, file_date):
    """Parse sheets 10pendResol, 10pendPrest, and 10pend."""
    records = []

    # 10pend has the combined view: solicitudes, pend_resol_grado, pend_pia, total pend
    rows = read_sheet_rows(wb, "10pend", max_rows=40)
    ccaa_data = find_ccaa_rows(rows, ccaa_col=1)

    for ccaa_name in CCAA_NAMES:
        if ccaa_name not in ccaa_data:
            continue
        row = ccaa_data[ccaa_name]
        rec = {
            "fecha": file_date,
            "ccaa": ccaa_name,
            "solicitudes": safe_int(row[3]) if len(row) > 3 else None,
            "pend_resol_grado": safe_int(row[4]) if len(row) > 4 else None,
            "pct_pend_resol_grado": safe_float(row[5]) if len(row) > 5 else None,
            "pend_pia": safe_int(row[7]) if len(row) > 7 else None,
            "pct_pend_pia_sobre_pend": safe_float(row[8]) if len(row) > 8 else None,
            "total_pendents": safe_int(row[10]) if len(row) > 10 else None,
            "pct_total_pendents": safe_float(row[11]) if len(row) > 11 else None,
        }
        records.append(rec)

    # TOTAL row
    for row in rows:
        if row and len(row) > 1 and row[1] is not None and "TOTAL" in str(row[1]):
            records.append({
                "fecha": file_date,
                "ccaa": "TOTAL",
                "solicitudes": safe_int(row[3]) if len(row) > 3 else None,
                "pend_resol_grado": safe_int(row[4]) if len(row) > 4 else None,
                "pct_pend_resol_grado": safe_float(row[5]) if len(row) > 5 else None,
                "pend_pia": safe_int(row[7]) if len(row) > 7 else None,
                "pct_pend_pia_sobre_pend": safe_float(row[8]) if len(row) > 8 else None,
                "total_pendents": safe_int(row[10]) if len(row) > 10 else None,
                "pct_total_pendents": safe_float(row[11]) if len(row) > 11 else None,
            })
            break

    return records


def parse_solicituds(wb, file_date):
    """Parse sheets 21solsaad (solicitudes) and 31dictsaad (resoluciones)."""
    records = []

    # Solicitudes from 21solsaad
    sol_rows = read_sheet_rows(wb, "21solsaad", max_rows=40)
    sol_data = find_ccaa_rows(sol_rows, ccaa_col=1)

    # Resoluciones from 31dictsaad
    dict_rows = read_sheet_rows(wb, "31dictsaad", max_rows=40)
    dict_data = find_ccaa_rows(dict_rows, ccaa_col=1)

    # Beneficiarios with prestación from 41benpresaad
    ben_rows = read_sheet_rows(wb, "41benpresaad", max_rows=40)
    ben_data = find_ccaa_rows(ben_rows, ccaa_col=1)

    for ccaa_name in CCAA_NAMES:
        rec = {
            "fecha": file_date,
            "ccaa": ccaa_name,
            "solicitudes": None,
            "resoluciones_grado": None,
            "grado_III": None,
            "grado_II": None,
            "grado_I": None,
            "beneficiarios_con_derecho": None,
            "sin_grado": None,
            "personas_con_pia": None,
            "total_prestaciones": None,
        }

        if ccaa_name in sol_data:
            row = sol_data[ccaa_name]
            rec["solicitudes"] = safe_int(row[3]) if len(row) > 3 else None

        if ccaa_name in dict_data:
            row = dict_data[ccaa_name]
            rec["resoluciones_grado"] = safe_int(row[7]) if len(row) > 7 else None
            rec["grado_III"] = safe_int(row[10]) if len(row) > 10 else None
            rec["grado_II"] = safe_int(row[13]) if len(row) > 13 else None
            rec["grado_I"] = safe_int(row[16]) if len(row) > 16 else None
            rec["beneficiarios_con_derecho"] = safe_int(row[19]) if len(row) > 19 else None
            rec["sin_grado"] = safe_int(row[22]) if len(row) > 22 else None

        if ccaa_name in ben_data:
            row = ben_data[ccaa_name]
            rec["personas_con_pia"] = safe_int(row[3]) if len(row) > 3 else None
            rec["total_prestaciones"] = safe_int(row[21]) if len(row) > 21 else None

        records.append(rec)

    # TOTAL rows
    total_rec = {
        "fecha": file_date,
        "ccaa": "TOTAL",
        "solicitudes": None,
        "resoluciones_grado": None,
        "grado_III": None,
        "grado_II": None,
        "grado_I": None,
        "beneficiarios_con_derecho": None,
        "sin_grado": None,
        "personas_con_pia": None,
        "total_prestaciones": None,
    }
    for row in sol_rows:
        if row and len(row) > 1 and row[1] is not None and "TOTAL" in str(row[1]):
            total_rec["solicitudes"] = safe_int(row[3]) if len(row) > 3 else None
            break
    for row in dict_rows:
        if row and len(row) > 1 and row[1] is not None and "TOTAL" in str(row[1]):
            total_rec["resoluciones_grado"] = safe_int(row[7]) if len(row) > 7 else None
            total_rec["grado_III"] = safe_int(row[10]) if len(row) > 10 else None
            total_rec["grado_II"] = safe_int(row[13]) if len(row) > 13 else None
            total_rec["grado_I"] = safe_int(row[16]) if len(row) > 16 else None
            total_rec["beneficiarios_con_derecho"] = safe_int(row[19]) if len(row) > 19 else None
            total_rec["sin_grado"] = safe_int(row[22]) if len(row) > 22 else None
            break
    for row in ben_rows:
        if row and len(row) > 1 and row[1] is not None and "TOTAL" in str(row[1]):
            total_rec["personas_con_pia"] = safe_int(row[3]) if len(row) > 3 else None
            total_rec["total_prestaciones"] = safe_int(row[21]) if len(row) > 21 else None
            break
    records.append(total_rec)

    return records


def write_csv(filepath, records, fieldnames):
    """Write records to CSV."""
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    print(f"  Written: {filepath} ({len(records)} rows)")


def main():
    files = sorted(glob.glob(os.path.join(IMSERSO_DIR, "estsisaad_*.xlsx")))
    print(f"Found {len(files)} Excel files to process")

    all_temps = []
    all_pendents = []
    all_solicituds = []

    for filepath in files:
        file_date = get_file_date(filepath)
        print(f"\nProcessing {os.path.basename(filepath)} ({file_date})...")

        wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)

        try:
            temps = parse_temps(wb, file_date)
            all_temps.extend(temps)
            print(f"  Temps: {len(temps)} records")
        except Exception as e:
            print(f"  ERROR parsing temps: {e}")

        try:
            pendents = parse_pendents(wb, file_date)
            all_pendents.extend(pendents)
            print(f"  Pendents: {len(pendents)} records")
        except Exception as e:
            print(f"  ERROR parsing pendents: {e}")

        try:
            solicituds = parse_solicituds(wb, file_date)
            all_solicituds.extend(solicituds)
            print(f"  Solicituds: {len(solicituds)} records")
        except Exception as e:
            print(f"  ERROR parsing solicituds: {e}")

        wb.close()

    # Write CSVs
    print("\n--- Writing CSVs ---")

    write_csv(
        os.path.join(OUTPUT_DIR, "imserso_temps.csv"),
        all_temps,
        ["fecha", "ccaa", "n_resol_grado", "tiempo_sol_a_grado_dias",
         "n_resol_pia", "tiempo_grado_a_pia_dias", "n_resol_pia_total",
         "tiempo_sol_a_pia_dias"]
    )

    write_csv(
        os.path.join(OUTPUT_DIR, "imserso_pendents.csv"),
        all_pendents,
        ["fecha", "ccaa", "solicitudes", "pend_resol_grado", "pct_pend_resol_grado",
         "pend_pia", "pct_pend_pia_sobre_pend", "total_pendents", "pct_total_pendents"]
    )

    write_csv(
        os.path.join(OUTPUT_DIR, "imserso_solicituds.csv"),
        all_solicituds,
        ["fecha", "ccaa", "solicitudes", "resoluciones_grado", "grado_III",
         "grado_II", "grado_I", "beneficiarios_con_derecho", "sin_grado",
         "personas_con_pia", "total_prestaciones"]
    )

    print("\nDone!")


if __name__ == "__main__":
    main()
