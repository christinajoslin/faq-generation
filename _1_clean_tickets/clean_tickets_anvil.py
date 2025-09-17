"""
Script for the initial cleaning and separation of tickets for the anvil database

Author: David Burns
Date: 6/4/2025 
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
import clean_tickets_tdx as cln_tkts
from markdownify import markdownify as md


warnings.simplefilter(action='ignore', category=Warning)


# Resulting data destination
dd = os.path.join(r"_1_clean_tickets\init_anvil_cln_tkts.csv")


def strip_jira_formatting(df: pd.DataFrame) -> pd.DataFrame:

    # Remove tickets with no content
    df = df[~df['customernote'].fillna('').str.match(r'^\s*$')]

    # Change to markdown for easier parsing
    df['customernote'] = df['customernote'].apply(md)

    # Revove new lines
    df['customernote'] = df['customernote'].str.replace(r'\n+', ' ', regex=True)

    # Remove links [text|url] or [url]
    df['customernote'] = df['customernote'].str.replace(r'\[(.*?)\|(.*?)\]', r'\1: \2', regex=True, case=False)
    df['customernote'] = df['customernote'].str.replace(r'\[(.*?)\]', r'\1', regex=True, case=False)

    # Remove signitures
    df['customernote'] = df['customernote'].str.replace(r'\{adf.*?\}.*?\{adf\}', '', regex=True, case=False) 

    # Remove other formatting
    df['customernote'] = df['customernote'].str.replace(r'\{(color|quote|code|noformat).*?\}', '', regex=True, case=False)

    # Remove images/attachments
    df['customernote'] = df['customernote'].str.replace(r'\!.*?\..{2,4}(?:|[a-z \,\=\d]+?)?\!', '', regex=True, case=False)

    # Remove extra whitespace
    df['customernote'] = df['customernote'].str.replace(r'\s+', ' ', regex=True, case=False)
    
    # Remove misc elements
    df['customernote'] = df['customernote'].replace(cln_tkts.remove_clutter(), regex=True)

    # Remove leading and ending whitespace
    df['customernote'] = df['customernote'].str.replace(r'^[\"\s]*', '', regex=True)
    df['customernote'] = df['customernote'].str.replace(r'[\"\s]*$', '', regex=True)

    df = df[~df['customernote'].fillna('').str.match(r'^\s*$')]

    return df


if __name__ == "__main__":

    # Decide whether to print or not
    print_var = True
    if len(sys.argv) > 1:
        print_var = sys.argv[1] != 'False'

    #-------------------------- Initial Data Cleaning ---------------------
    df_tickets = find_top_tickets('anvil')

    df_tickets = strip_jira_formatting(df_tickets)
    df_tickets = cln_tkts.remove_names(df_tickets)
    df_tickets = cln_tkts.sep_tickets(df_tickets, False)
    df_tickets = strip_jira_formatting(df_tickets) # it must be done twice

    if print_var: print(df_tickets.head())

    df_tickets.to_csv(dd, index=False)

