import pandas as pd

def parse_number(val) -> float:
    """
    Parses Indonesian numeric and currency format strings to standard float.
    Handles 'Rp' prefixes, thousand separators (dots), decimal separators (commas), and missing placeholders.
    """
    if pd.isna(val) or val is None:
        return 0.0

    string_value = str(val).strip()
    if not string_value or string_value.lower() in ("no data", "-", "nan", "null"):
        return 0.0

    cleaned_string = string_value.replace("Rp", "").replace("rp", "").strip()

    if "." in cleaned_string and "," in cleaned_string:
        cleaned_string = cleaned_string.replace(".", "").replace(",", ".")
    elif "," in cleaned_string:
        cleaned_string = cleaned_string.replace(",", ".")
    elif "." in cleaned_string:
        dot_segments = cleaned_string.split(".")
        if len(dot_segments) > 1 and all(len(segment) == 3 for segment in dot_segments[1:]):
            cleaned_string = cleaned_string.replace(".", "")

    try:
        return float(cleaned_string)
    except ValueError:
        return 0.0
