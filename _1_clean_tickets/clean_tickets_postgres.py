"""
Script for the initial cleaning and separation of tickets for the postgres database

Author: David Burns
Date: 6/4/2025 
Purpose: 
    - Remove all elements from messages that are not the acutal content
    - Remove names and contact information from ticket messages
    - Separate tickets into their individual messages if needed
"""
import pandas as pd 
from sqlalchemy import create_engine
import datetime
import warnings
import os
import sys
import clean_tickets_tdx as cln_tkts
warnings.simplefilter(action='ignore', category=Warning)


# Resulting data destination
dd = os.path.join(r"_1_clean_tickets\init_postgres_cln_tkts.csv")


# Separate the tickets by message
def sep_tickets(df: pd.DataFrame, separate: bool) -> pd.DataFrame:

    # Split the messages into different rows
    if separate:
        df['customernote'] = df['customernote'].str.split(r'\n\n')
        df = df.explode('customernote')
    
    # Separate the messages in each row
    else:
        df['customernote'] = df['customernote'].str.replace(r'\n\n', ' ; ')

    return df


# Remove generated formatting 
def strip_formatting(df: pd.DataFrame) -> pd.DataFrame:

    df['customernote'] = df['customernote'].replace(cln_tkts.remove_clutter(), regex=True)
    df = df[~df['customernote'].str.match(r'^\s*$')]

    return df


if __name__ == "__main__":

    # Decide whether to print or not
    print_var = True
    if len(sys.argv) > 1:
        print_var = sys.argv[1] != 'False'

    #---------------------- Data Retrieval ------------------------------
    with open("db_creds.txt", "r") as f:
        creds = f.read()
    db_pw = creds.strip()
    try:
        engine = create_engine(f'postgresql+psycopg2://postgres:{db_pw}@archivaltickets.srodenb.geddes.rcac.purdue.edu:5432/postgres')
        if print_var: print("Engine created.")
    except Exception as e:
        print(f"Engine creation failed for database postgres: {e}")
        exit()

    query = f"""
    SELECT 
        *
    FROM tickets
    ;"""

    #-------------------------- Initial Data Cleaning ---------------------
    df_tickets = pd.read_sql(query, engine)

    df_tickets = cln_tkts.filter_date(df_tickets)
    df_tickets = sep_tickets(df_tickets, False)
    df_tickets = strip_formatting(df_tickets)
    df_tickets = cln_tkts.remove_names(df_tickets)

    if print_var: print(df_tickets.head())

    df_tickets.to_csv(dd, index=False)
