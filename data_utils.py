
import re 
def filter_dataframe(df, filters):
    for column, value in filters.items():
        df = df[df[column].isin(value)]
    return df

def filter_dataframeToUpper(df, filters):
    for column, value in filters.items():
        df = df[df[column].str.upper().isin(value)]
    return df

def getColumns(df, columns):
        missing_columns = [col for col in columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Columns not found in DataFrame: {missing_columns}")
        
        return df[columns]

def is_valid_email(email):
    # Simple regex for validating an email
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(email_regex, email) is not None

