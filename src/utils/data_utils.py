import pandas as pd

def clean_number_col(series: pd.Series) -> pd.Series:
    """
    Membersihkan format mata uang / angka Indonesia (misal 'Rp 1.000.000,00' atau '12.34%')
    dan mengonversinya ke nilai numerik (float).
    """
    return (
        series.astype(str)
        .str.replace(r'[Rp%\s]', '', regex=True)
        .str.replace('.', '', regex=False)
        .str.replace(',', '.', regex=False)
        .pipe(pd.to_numeric, errors='coerce')
        .fillna(0)
    )
