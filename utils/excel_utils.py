import pandas as pd

def load_all_sheets(db_path):
    try:
        xls = pd.ExcelFile(db_path)
        return {
            name: pd.read_excel(db_path, sheet_name=name, dtype=str)
            for name in xls.sheet_names
        }
    except:
        return {}

def safe_write(db_path, updated_sheets: dict):
    all_sheets = load_all_sheets(db_path)

    for sheet, df in updated_sheets.items():
        all_sheets[sheet] = df

    with pd.ExcelWriter(db_path, engine="openpyxl", mode="w") as writer:
        for sheet, df in all_sheets.items():
            df.to_excel(writer, sheet_name=sheet, index=False)
