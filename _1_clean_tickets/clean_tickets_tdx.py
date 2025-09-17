"""
Script for the initial cleaning and separation of tickets for the tdx database

Author: David Burns
Date: 6/3/2025 
Purpose: 
    - Remove all elements from messages that are not the acutal content
    - Remove names and contact information from ticket messages
    - Separate tickets into their individual messages if needed
"""
import pandas as pd 
from sqlalchemy import create_engine
from cluster_selection import find_top_tickets
import warnings
import os
import sys
from bs4 import BeautifulSoup 


warnings.simplefilter(action='ignore', category=Warning)


# Resulting data destination
dd = os.path.join(r"_1_clean_tickets\init_tdx_cln_tkts.csv")


# Strip HTML tags 
def strip_html(text: str) -> str:

    soup = BeautifulSoup(text or "", 'lxml')

    return soup.get_text(separator=" ", strip=True)


# Separate the tickets by message
def sep_tickets(df: pd.DataFrame, split: bool = True, separate: bool = True) -> pd.DataFrame:

    # Split the messages into different rows
    if split:  
        df['customernote'] = df['customernote'].str.split(r'-{30,}')
        df = df.explode('customernote')
    
    # Separate the messages in each row
    elif separate:
        df['customernote'] = df['customernote'].str.replace(r'\-{10}[^a-z]+\-{10}', "; ", regex=True, case=False)

    return df


# remove msc elements
def remove_clutter():

    return {
       
        # Email addresses 
        r'(?:(?:\< )|\<)?\b[\w\.-]+@[\w\.-]+\.\w+\b(?:(?: \>)|\>)?\;?': "",

        # Phone numbers
        r'\b(?:\+?1[\s.-]?)?(?:\(?\d{3}\)?[\s.-]?)\d{3}[\s.-]?\d{4}\b': "",

        # IDs
        r'(?<=id\:)\s*\w*': "id",

        # Msc characters
        r'‘|’': "'",
        r'–': '-',
        r'\u00a0| ': ' ',
        r'﻿|\u200B|​|￼|­|\u200c| ': '',
        r'“|”||': '"',
        r'：': ': ',

        # Redundant whitespace
        r' +': " ",
        r'\n+': "",
        r'(?:\\n)+': "",
        r'^[\"\s]+': "",
        r'[\"\s]+$': "",

        # Remove repeating special characters
        r'\s*(\,|\_)\s*(?=\1)': "",

    }


# Remove anything that isn't the core message
def clean_tickets(df: pd.DataFrame) -> pd.DataFrame:
    
    to_remove = remove_clutter()
    
    # Remove automatically generated elements
    with open(os.path.join(r"_1_clean_tickets\auto_gen_rep.txt"), "r") as f:
        for line in f.readlines():
            to_remove[line.strip()] = ""
    
    # Apply regex cleaning and others
    df['customernote'] = df['customernote'].replace(to_remove, regex=True)
    df['customernote'] = df['customernote'].replace(to_remove, regex=True) # some elements are generated recursively, so this must be done twice to remove everything unwanted

    df['customernote'] = df['customernote'].str.strip(r'\"\. ')
    df = df[~df['customernote'].str.match(r'^\s*$')]

    return df 


# Remove names from customer note
def remove_names(df: pd.DataFrame) -> pd.DataFrame:

    # Replace unique names with name
    users = pd.read_parquet(os.path.join(r"_1_clean_tickets\names.parquet"))
    re_users = r"(?<![a-z\d])(?:" + "|".join(users['name']) + r")(?![a-z\d])"
    df['customernote'] = df['customernote'].str.replace(re_users, "name", case=False, regex=True)

    df['customernote'] = df['customernote'].str.replace("(?<=name)(?:[^a-z;]*?name)", "", regex=True) # remove sequential instances of name

    return df


if __name__ == "__main__":

    # Decide whether to print or not
    print_var = True
    if len(sys.argv) > 1:
        print_var = sys.argv[1] != 'False'

    #-------------------------- Initial Data Cleaning ---------------------
    df_tickets = find_top_tickets('tdx')

    # Remove the first 3 demo tickets
    df_tickets = df_tickets.iloc[3:].reset_index(drop=True)


    df_tickets['customernote'] = df_tickets['customernote'].apply(strip_html)
    df_tickets = clean_tickets(df_tickets)
    df_tickets = remove_names(df_tickets)
    df_tickets = sep_tickets(df_tickets, split=False)

    if print_var: print(df_tickets.head())

    # Save dataframe
    df_tickets.to_csv(dd, index=False)

