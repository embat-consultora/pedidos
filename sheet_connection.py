import logging
import streamlit as st
from streamlit_gsheets import GSheetsConnection
import gspread
logging.basicConfig(level=logging.DEBUG)

def get_google_sheet(connection, sheet_id):
    """
    Connects to a Google Sheet using service account credentials and returns the sheet.
    """
    try:
        url=f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit?usp=sharing"
        conn = st.connection(connection, type=GSheetsConnection)
        df = conn.read(spreadsheet=url,ttl=0)
        if df is not None and not df.empty:
             return df
        else:
            return None

    except FileNotFoundError as e:
        logging.error(f"Service account file not found: {e}")
        return None
    except gspread.exceptions.APIError as e:
        logging.error(f"Google Sheets API error: {e}")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return None

@st.cache_data(ttl=3600)   # Cache the result to avoid reloading each time
def get_sheets(connection, worksheetNames):
    try:
        dfs=[]
        conn = st.connection(connection, type=GSheetsConnection)
        for worksheet_name in worksheetNames:
            df = conn.read(worksheet=worksheet_name)
            if df is not None and not df.empty:
                dfs.append(df)  
            else:
                logging.warning(f"No data found for worksheet: {worksheet_name}")
                dfs.append(None) 
        return dfs

    except FileNotFoundError as e:
        logging.error(f"Service account file not found: {e}")
        return None
    except gspread.exceptions.APIError as e:
        logging.error(f"Google Sheets API error: {e}")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return None
    

def update_google_sheet(connection, sheet_id, worksheet, dataframe):
    conn = st.connection(connection, type=GSheetsConnection)
    conn.update(worksheet=worksheet, data=dataframe)

@st.cache_data(ttl=3600)
def get_all_worksheets(connection):
    try:
        conn = st.connection(connection, type=GSheetsConnection)
        return conn

    except FileNotFoundError as e:
        logging.error(f"Service account file not found: {e}")
        return None
    except gspread.exceptions.APIError as e:
        logging.error(f"Google Sheets API error: {e}")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return None
