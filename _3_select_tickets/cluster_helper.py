"""
Helper functions for subclustering and ranking FAQ candidates from ticket embeddings.

Author: Christina Joslin
Date: 7/2/2025
Purpose:
    - Compute optimal number of subclusters (k) using silhouette score
    - Apply KMeans clustering to embeddings
    - Rank ticket summaries within subclusters using cosine similarity
    - Compute cohesion and separation metrics for scoring
    - Assign weighted scores to subclusters for global ranking
    - Save final subcluster rankings and contents for FAQ generation

"""

# -------------------- Load Libraries --------------------
import numpy as np
import warnings
warnings.filterwarnings("ignore")

# Embedding and similarity
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler, normalize

# Clustering
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

# Utility
import csv

# -------------------- Optimal k Selection --------------------
def compute_best_k(X, total):
    """
    Computes the optimal number of subclusters (k) using silhouette score,
    filtering out imbalanced or overly small clusters.
    """
    candidate_scores = [] # Keeps track of the best k and its corresponding silhouette score

    for k in range(2, 5): # Iterates through k values from 2 to 4 (found to be the best balance between over- and underfitting due to the parent cluster sizes (~90 tickets))
          labels = KMeans(n_clusters=k, random_state=42, n_init=50).fit(X).labels_ # Number of times k-means runs with different centroid seeds (n_init=50) to ensure robustness to high-dimensionality
          unique, counts = np.unique(labels, return_counts=True)

          max_prop = counts.max() / total

          # Skip if any subcluster has fewer than 5 tickets or is overly imbalanced
          if np.any(counts < 5) or max_prop > 0.85:
            continue

          # Compute Silhouette Score
          silo_score = silhouette_score(X, labels)

          candidate_scores.append((k, silo_score))

    # Select best k based on the highest Silhouette Score
    if candidate_scores:  # Check if the list is not empty
        candidate_scores.sort(key=lambda x: -x[1])  # Sort in Descending Order (Highest Silhouette is the best)
        best_k = candidate_scores[0][0]
    else:
        best_k = 1  # Return 1 if no suitable k is found

    return best_k

# -------------------- KMeans Subclustering --------------------
def subcluster_embeddings_kmeans(embeddings, k):
    """
    Applies KMeans clustering to group high-dimensional sentence embeddings into subclusters.
    Returns both the predicted labels and centroids.
    """
    kmeans = KMeans(
        n_clusters=k,
        random_state=42,
        n_init=50
    )

    # Fit the model and predict cluster labels
    labels = kmeans.fit_predict(embeddings)

    # Extract the cluster centroids for downstream use (e.g., visualization, scoring)
    centroids = kmeans.cluster_centers_

    return labels, centroids

# -------------------- Rank Entries by Centroid --------------------
def get_top_entries_by_centroid(embeddings, centroid, df):
  """
  Returns ticket issue summaries and resolutions sorted by similarity to subcluster centroid.
  Used for selecting most representative examples for FAQ generation.
  """
  # Ensure inputs are 2D
  centroid = centroid.reshape(1,-1)

  # Normalize both embeddings and centroid since we are using cosine similarity
  norm_embeddings = normalize(embeddings)
  norm_centroid = normalize(centroid)

  # Compute cosine similarities
  similarities = cosine_similarity(norm_embeddings, norm_centroid).flatten()

  # Sort by most similar indices
  top_indices = similarities.argsort()[::-1]

  # Extract text
  top_summaries = df.loc[top_indices, 'issue_summary'].tolist()
  top_resolutions = df.loc[top_indices, 'resolution'].dropna().tolist()

  return top_summaries, top_resolutions


# -------------------- Cohesion & Separation Metrics --------------------
def compute_cohesion(embeddings):
    """
    Measures intra-subcluster similarity by computing the average pairwise cosine similarity
    between all vectors in a subcluster. This gives a proxy for how "tight" or cohesive a group is.

    Closer to 1 = more cohesive and tighter clusters
    Closer to 0 = less cohesive and more scattered clusters

    """
    # Re-normalize again since we are using cosine similarity
    embeddings = normalize(embeddings)

    # Get number of embedding vectors
    n_samples = embeddings.shape[0]

    # Compute cosine similarity matrix (n_samples x n_samples)
    sim_matrix = cosine_similarity(embeddings)

    # Compute total sum of similarities
    total_sim = np.sum(sim_matrix)

    # Subtract self-similarity
    diagonal = np.trace(sim_matrix)

    # Normalize by number of unique pairwise comparisons
    return (total_sim - diagonal) / (n_samples * (n_samples - 1))


def compute_separation(embeddings_a, embeddings_b):
    """
    Measures inter-subcluster dissimilarity by computing the average pairwise cosine distance
    between vectors from different subclusters. This provides an indication of how distinct or
    well-separated the groups are from each other.

    Return the complement of the separation score to have high values be ideal.

    The equation used is the average linkage clustering formula
    """

    # Re-normalize again since we are using cosine similarity
    embeddings_a = normalize(embeddings_a)
    embeddings_b = normalize(embeddings_b)

    # Calculate cross-cluster similarity matrix
    sim_matrix = cosine_similarity(embeddings_a, embeddings_b)

    # Sum all pairwise similarities
    total_sim = np.sum(sim_matrix)

    # Normalize by number of cross-cluster comparisons
    n_comparisons = embeddings_a.shape[0] * embeddings_b.shape[0]

    # Return the complement of the separation score
    return 1 - (total_sim / n_comparisons)


# -------------------- Subcluster Ranking --------------------
def compute_ranked_scores(subclusters, size_weight, cohesion_weight, separation_weight):
    """
    Assigns a global score to each subcluster across all parent clusters based on:
      - Size: number of items in the subcluster (percentile rank)
      - Cohesion: tightness of the subcluster (z-score; higher = better)
      - Separation: distinctiveness of the subcluster (z-score; higher = better)

    The final score is a weighted combination of all three metrics.
    """

    # Extract raw metrics
    sizes = np.array([s["size"] for s in subclusters])
    cohesions = np.array([s["cohesion"] for s in subclusters])
    separations = np.array([s["separation"] for s in subclusters])

    # Normalize size metric only
    scaler = MinMaxScaler()
    normalized_sizes = scaler.fit_transform(sizes.reshape(-1, 1)).flatten()


    # Assign final score to each subcluster
    for i, s in enumerate(subclusters):
        score = (
            size_weight * normalized_sizes[i] +
            cohesion_weight * cohesions[i] +
            separation_weight * separations[i]
        )

        # Store rank/z details
        s["normalized_size"] = normalized_sizes[i]
        s["score"] = score

        # print(f"Parent Cluster {s['cluster']} → "
        #       f"Subcluster {s['subcluster_id']} → "
        #       f"size: {normalized_sizes[i]:.2f}, "
        #       f"cohesion: {cohesions[i]:.2f}, "
        #       f"separation: {separations[i]:.2f}, "
        #       f"final score: {score:.2f}")

    return subclusters

# -------------------- Save Ranked Subclusters --------------------
def save_subclusters(top_faq_subclusters, ticket_src):
    """
    Saves subcluster summaries and basic metadata to CSV for review or FAQ generation.
    """
    file_path = f"{ticket_src}_top_faq_candidates.csv"
    
    with open(file_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)

        # Header
        writer.writerow([
            "Cluster", "Subcluster_ID", "Num_Summaries",
            "Num_Resolutions", "All_Summaries", "All_Resolutions"
        ])

        for s in top_faq_subclusters:
            summaries_str = " ||| ".join(s["summaries"])
            resolutions_str = " ||| ".join(s["resolutions"]) if s["resolutions"] else ""

            writer.writerow([
                s["cluster"],
                s["subcluster_id"],
                len(s["summaries"]),
                len(s["resolutions"]),
                summaries_str,
                resolutions_str
            ])