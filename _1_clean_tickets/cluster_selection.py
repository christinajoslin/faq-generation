"""
Script to extract and filter anomaly and cluster data for high-frequency clusters.

Author: Christina Joslin
Date: 5/30/2025 
Purpose:  
    - Identify top 30% of clusters based on anomaly frequency over the past 90 days.  
    - Then filter to retain tickets from the past 2 years for FAQ generation. 

"""

import pandas as pd
from sqlalchemy import create_engine

def find_top_tickets(db_name = 'tdx'):
    # Read database password from file
    with open("db_creds.txt", "r") as f:
        db_pw = f.read().strip()

    # Create SQLAlchemy engine for PostgreSQL connection
    engine = create_engine(f'postgresql+psycopg2://postgres:{db_pw}@archivaltickets.srodenb.geddes.rcac.purdue.edu:5432/{db_name}tickets')

    # ---------------------------------- Load Data -----------------------------------------------------

    # Load data
    ticket_query = "SELECT * FROM tickets;"
    cluster_query = "SELECT * FROM clusters;"
    anomaly_query = "SELECT * FROM anomaly;"
    df_tickets = pd.read_sql(ticket_query, engine)
    df_clusters = pd.read_sql(cluster_query, engine)
    df_anomaly = pd.read_sql(anomaly_query, engine)

    #df_clusters = pd.read_csv(f'../../databases/geddes/{db_name}db/clusters.csv') # backup in case the clusters table is down 

    # -------------------------- Find Top Clusters Based on Last 90 Days --------------------------------

    today = pd.Timestamp.today() 
    last_90_days = today - pd.Timedelta(days=90)
    df_anomaly['datesubmitted'] = pd.to_datetime(df_anomaly['datesubmitted'])
    df_recent_90 = df_anomaly[df_anomaly['datesubmitted'] >= last_90_days]

    # Keep only true anomalies
    df_true_anomalies_90 = df_recent_90[df_recent_90['anomaly'] == 'Yes']

    # Group by cluster and count anomalies
    cluster_counts_90 = df_true_anomalies_90.groupby('cluster')['anomaly'].count() 

    # Identify the top 30% clusters (yields about 10-20 clusters)
    threshold = cluster_counts_90.quantile(0.70) 
    top_clusters = cluster_counts_90[cluster_counts_90 >= threshold]
    top_cluster_ids = top_clusters.index.tolist() 
    
    #print(f"Total Clusters: {len(top_cluster_ids)}")

    # ---------------------------- Filter Tickets from the Last 2 Years -------------------------------------

    two_year_cutoff = today - pd.Timedelta(days=365*2)
    df_tickets['datesubmitted'] = pd.to_datetime(df_tickets['datesubmitted'])
    df_tickets_recent = df_tickets[df_tickets['datesubmitted'] >= two_year_cutoff]

    # Filter clusters and tickets for top anomaly clusters
    df_top_clusters = df_clusters[df_clusters['cluster'].isin(top_cluster_ids)]
    df_top_tickets = df_tickets_recent[df_tickets_recent['issuenumber'].isin(df_top_clusters['issuenumber'])]

    #print(f"Number of entries in the final dataset {len(df_top_tickets)}")

    return df_top_tickets
