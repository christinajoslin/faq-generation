"""
Script to generate and score subclusters from clustered support ticket embeddings.

Author: Christina Joslin  
Date: 7/2/2025  
Purpose:
    - Load ticket summaries and initial parent cluster assignments
    - Embed and reduce ticket summaries within each cluster
    - Apply KMeans to create subclusters
    - Compute cohesion and separation for each subcluster
    - Rank subclusters based on weighted scoring metrics
    - Return top subclusters for downstream FAQ generation
"""
# -------------------- Load Libraries --------------------
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings("ignore")

# Embedding and similarity
from sklearn.decomposition import PCA

# SQL
from sqlalchemy import create_engine

# Helper functions
import cluster_helper as helper
import select_subclusters as gb_vars

# -------------------- Subcluster Generation --------------------
def generate_subclusters(ticket_src, model):
    """
    Generates subclusters for each parent cluster using PCA-reduced sentence embeddings
    and KMeans clustering. Computes cohesion and separation metrics for each subcluster.
    Returns a list of subcluster metadata dictionaries.
    """
    # Load ticket summaries
    df_tickets = pd.read_csv(f'../_2_summarize_tickets/{ticket_src}_ticket_summaries.csv')

    # Load parent cluster assignments from SQL database
    with open("db_creds.txt", "r") as f:
        db_pw = f.read().strip()
    
    engine = create_engine(f'postgresql+psycopg2://postgres:{db_pw}@archivaltickets.srodenb.geddes.rcac.purdue.edu:5432/{ticket_src}tickets')
    cluster_query = "SELECT * FROM clusters"
    df_clusters = pd.read_sql(cluster_query, engine)

    # Save locally if needed
    #df_clusters.to_csv(f"{ticket_src}_clusters.csv", index=False)

    # Merge datasets
    df_merged = pd.merge(df_clusters, df_tickets, on='issuenumber', how='inner')
    df_merged.drop(['title', 'titlenostopwords'], axis=1, inplace=True)

    # Count entries per cluster
    cluster_counts = df_merged['cluster'].value_counts()


    # Store metadata for every subcluster
    global_subcluster_stats = []

    # Iterate through parent clusters
    for cluster_id, total in cluster_counts.items():

        # Retrieve the issue summaries associated with the given parent cluster
        cluster_df = df_merged[df_merged['cluster'] == cluster_id].reset_index(drop=True)
        summaries_all = cluster_df['issue_summary'].tolist()

        # Generate embeddings and reduce dimensionality
        embeddings = model.encode(summaries_all, batch_size=16, normalize_embeddings=True)
        pca = PCA(n_components=10, random_state=42)
        embeddings = pca.fit_transform(embeddings)

        # Subcluster with KMeans
        k = helper.compute_best_k(embeddings, len(cluster_df))

        # Edge Case: If no optimal subclustering is found, then skip this parent cluster 
        if k == 1: 
            continue 

        labels, centroids = helper.subcluster_embeddings_kmeans(embeddings, k=k)

        # print(f"Cluster '{cluster_id}' → KMeans selected k = {k}")

        # For visualization across all subclusters
        all_sub_embeddings = []
        all_sub_labels = []

        # First pass: process all subclusters
        subclusters = []

        for sub_id in range(k):
            # Retrieve the entries and embeddings associated with a given subcluster
            mask = (labels == sub_id)
            sub_df = cluster_df[mask].reset_index(drop=True)
            sub_embeddings = embeddings[mask]

            # Append these embeddings and their subcluster label for visualization purposes
            all_sub_embeddings.append(sub_embeddings)
            all_sub_labels.extend([sub_id] * len(sub_embeddings))

            # Save data for scoring in second pass
            subclusters.append({
                'sub_id': sub_id,
                'df': sub_df,
                'embeddings': sub_embeddings,
            })

        # Second pass: compute cohesion and separation
        for subcluster in subclusters:
            sub_id = subcluster['sub_id']
            sub_df = subcluster['df']
            embeddings_a = subcluster['embeddings']

            size = len(sub_df)
            cohesion = helper.compute_cohesion(embeddings_a)

            # Compute separation from all other subclusters
            separations = []
            for other in subclusters:
                if other['sub_id'] == sub_id:
                    continue
                embeddings_b = other['embeddings']
                sep_score = helper.compute_separation(embeddings_a, embeddings_b)
                separations.append(sep_score)

            # Compute the mean separation
            separation = np.mean(separations) if separations else 0.0

            # Sort issue summary and resolutions per entry by similarity/dissimilarity of issue summary with the centroid
            centroid = centroids[sub_id]
            top_summaries, top_resolutions = helper.get_top_entries_by_centroid(
            embeddings=embeddings_a,
            centroid=centroid,
            df=sub_df)

            # Store stats
            global_subcluster_stats.append({
                'cluster': cluster_id,
                'subcluster_id': sub_id,
                'summaries': sub_df['issue_summary'].tolist(),
                'resolutions': sub_df['resolution'].dropna().tolist(),
                'size': size,
                'cohesion': cohesion,
                'separation': separation,
                'embeddings': embeddings_a,
            })
    
    return global_subcluster_stats


# -------------------- Subcluster Selection --------------------
def select_top_subclusters(global_subcluster_stats):
    """
    Ranks and filters subclusters based on size, cohesion, and separation.
    Returns a shortlist of top subclusters for FAQ generation.
    """

    # Score and normalize
    updated_subclusters = helper.compute_ranked_scores(
        global_subcluster_stats,
        size_weight=0.4,
        cohesion_weight=1.2,
        separation_weight=0.2
    )

    # Filter based on size thresholds
    filtered = [
        s for s in updated_subclusters
        if (s.get("normalized_size", 0) > gb_vars.MIN_SIZE + gb_vars.EPSILON) and
        (s.get("normalized_size", 0) < gb_vars.MAX_SIZE - gb_vars.EPSILON)
    ]

    # Sort by score
    ranked = sorted(filtered, key=lambda x: x["score"], reverse=True)

    # Select top 10 for FAQ generation
    top_faq_subclusters = ranked[:gb_vars.NUM_FAQs]

    return top_faq_subclusters
