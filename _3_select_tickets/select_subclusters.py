"""
Script that sorts subclusters

Author: David Burns
Date: 7/2/2025
Purpose:
    - Central script to run during production
"""


# Define global configuration variables
TICKET_SRC:str = "tdx"  # Set to "tdx" or "anvil" depending on data source
MODEL_DEVICE:str = "gpu" # e.g. gpu, cpu

# Define global variables for ranking subclusters
MIN_SIZE = 0.05     # Too small = too specific
MAX_SIZE = 0.80     # Too big = overly broad
EPSILON = 1e-3 # epsilon threshold to overcome floating point approximation
NUM_FAQs = 20  # number of subclusters to save to a CSV for LLM input


# Import libraries
import cluster_helper as helper
import generate_subclusters as gen_subc
from sentence_transformers import SentenceTransformer
import torch


# Load sentence embedding model
def get_model(model_device:str="cuda") -> SentenceTransformer:
    
    # Standardize gpu to work with multiple brands (Nvidia, Intel)
    if model_device == "gpu":
        if torch.cuda.is_available(): 
            model_device = "cuda"
        elif torch.xpu.is_available():
            model_device = "xpu"
        else:
            model_device = "cpu"

    model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2', device=model_device, trust_remote_code=True)

    return model


if __name__ == "__main__":

    model = get_model(model_device=MODEL_DEVICE)
    print("Model Loaded")

    subclusters_stats = gen_subc.generate_subclusters(ticket_src=TICKET_SRC, model=model)
    print("Subclusters generated")

    ranked_subclusters = gen_subc.select_top_subclusters(global_subcluster_stats=subclusters_stats)
    print("Subclusters sorted")

    helper.save_subclusters(top_faq_subclusters=ranked_subclusters, ticket_src=TICKET_SRC)
    print("Subclusters saved")
