"""
Script to extract, clean, and post-process ticket resolution data using a finetuned LLM.

Author: Christina Joslin  
Date: 6/21/2025  
Purpose:
    - Load support ticket data from TDX or Anvil.
    - Generate issue summaries and resolutions using a finetuned Mistral model through API calls from Purdue GenAI Studio 
    - Post-process outputs to extract structured fields.
    - Remove boilerplate closure/filler text from the resolution for better downstream semantic analysis.
    - Save a cleaned version of the dataset for FAQ generation or clustering.
"""
# -------------------- Load Libraries --------------------
import re                       # Regular expressions for text extraction
import pandas as pd            # DataFrame operations
from tqdm import tqdm          # Progress bar for loops
import requests                # HTTP requests to the GenAI API
from torch.utils.data import DataLoader, Dataset  # Batch management for API calls
from transformers import AutoTokenizer            # Tokenizer to measure prompt length
import time                    # Timing for retries
from nltk import sent_tokenize # Sentence splitting
from dotenv import load_dotenv # Load API key from environment
import random                  # Add randomness to retry delay
import nltk
import os

# Extend NLTK’s search path to look in the local folder for tokenizer data
nltk.data.path.append(os.path.join(os.getcwd(), '_2_summarize_tickets'))

# Manually verify that NLTK’s Punkt tokenizer is available (raises error if not found)
nltk.data.find('tokenizers/punkt_tab')

# -------------------- Initial Config -------------------------------
GENAI_API_URL = "https://genai.rcac.purdue.edu/api/chat/completions"

# Load your GenAI API key from .env file (must exist in project root)
load_dotenv() 
GENAI_API_KEY = os.getenv("GENAI_API_KEY")   

# This is the tag used for the finetuned Mistral model container
GENAI_MODEL = "cjoslin22/Finetuned_Mistral-7.2B-Q8_0:latest"

# Number of prompts sent per API call (tune for performance/memory)
BATCH_SIZE = 2

# Truncation safeguard: drop prompts longer than this
MAX_PROMPT_LENGTH = 1621 # 10% data loss

# Toggle between TDX or Anvil data
TICKET_SRC = "tdx"  
# -------------------- Load Tokenizer ---------------------------------
# Load the tokenizer used when fine-tuning, from local directory
tokenizer = AutoTokenizer.from_pretrained("_2_summarize_tickets/tokenizer_filter", local_files_only=True)

# -------------------- Read Ticket Data ----------------------------------
# Load the cleaned ticket file for the current source (e.g., anvil or tdx)
df_tickets = pd.read_csv(f"_1_clean_tickets/init_{TICKET_SRC}_cln_tkts.csv")

# -------------------- Build Prompts ------------------------------------
# Function to wrap a ticket message in a clean prompt format for the LLM
def build_prompt(note):
    return (
        "You are an expert HPC support assistant. Your job is to extract key information from HPC support ticket messages for documentation purposes. "
        "Your output will be used to generate FAQs and help users resolve issues independently.\n\n"
        "Your task:\n"
        "Extract and clearly report the *Issue Summary* and *Resolution* from the ticket message. Follow this format **exactly**, and ensure the response includes any specific technical details mentioned "
        "(e.g., command-line examples, module names, tool names, documentation URLs, file paths) **whenever present**.\n\n"
        "**Do NOT** include:\n"
        "- Bullet points\n"
        "- Extra commentary\n"
        "- Any names, titles, greetings, or sign-offs\n"
        "- References to the original message\n"
        "- Any mention of ticket status (e.g., resolved, closed, reopened)\n"
        "- Any suggestion to follow up or reopen the ticket\n\n"
        "**Output Format:**\n\n"
        "1. Issue Summary:  [Insert brief issue description]\n\n"
        "2. Resolution:  [Insert detailed resolution, including any commands, links, or configuration details]\n\n"
        "The full ticket message appears below. Do NOT copy or summarize it.\n"
        f"{note}"
    )

# Apply the prompt builder to each customer note
df_tickets["prompt"] = df_tickets["customernote"].apply(build_prompt)

# ---------------------- Length Filter -----------------------------------
# Define a helper to compute the number of tokens in each prompt
def prompt_length(prompt):
    return len(tokenizer(prompt.strip(), truncation=False)["input_ids"])

# Filter out prompts that exceed model context length
df_tickets["token_length"] = df_tickets["prompt"].apply(prompt_length)
df_tickets = df_tickets[df_tickets["token_length"] <= MAX_PROMPT_LENGTH].reset_index(drop=True)

# ---------------------- Prep for API Call -------------------------------
# Define a minimal PyTorch Dataset to allow DataLoader batching
class PromptDataset(Dataset):
    def __init__(self, prompts): self.prompts = prompts
    def __len__(self):      return len(self.prompts)
    def __getitem__(self, i): return self.prompts[i]

# Strip whitespace and create a batched DataLoader
formatted_prompts = [p.strip() for p in df_tickets["prompt"]]
dataset = PromptDataset(formatted_prompts)
dataloader = DataLoader(dataset, batch_size=BATCH_SIZE)


# ---------------------- Helper Functions ---------------------------------
def call_genai_api(prompts, retries = 7):
    responses = []

    for i, prompt in enumerate(prompts):

        # Clean up the prompt: remove trailing semicolon/quotes/extra whitespace 
        prompt = re.sub(r'["\']?\s*;\s*$', '', prompt.strip())  # remove trailing semicolon junk
        prompt = prompt.rstrip("\n\t ")  # remove any whitespace left

        # Prepare HTTP headers and request body for GenAI API    
        headers = {
        "Authorization": f"Bearer {GENAI_API_KEY}",
        "Content-Type": "application/json"
        }
        body = {
        "model": GENAI_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False
        }

         # Attempt request with up to `retries` retries
        for attempt in range(retries):
            try:
                r = requests.post(GENAI_API_URL, headers=headers, json=body)
                # Success: parse and store output 
                if r.status_code == 200:
                    print(f"✅ Valid Request after {attempt + 1} attempt(s)")
                    data = r.json()
                    content = data["choices"][0]["message"]["content"]
                    responses.append(content)
                    break
                # Model not found - unrecoverable 
                elif r.status_code == 404:  # TODO: Train a backup finetuned model 
                    print(f"⚠️[Prompt {i}] Model not found (404). Not retrying.")
                    responses.append("")
                    break
                # Other errors - retry with delay  
                else:
                    print(f"❌[Prompt {i}] {r.status_code} on attempt {attempt+1} retrying..")
                    time.sleep(0.3*(attempt + 1) + random.uniform(0,0.2))  # light exponential delay based on retry attempt number
            # Handle connection or network issues (e.g., timeout, connection error)
            except requests.exceptions.RequestException as e:  
                print(f"⚠️[Prompt {i}] Request failed: {e}")
                responses.append("")
                break
        else:
            # All retry attempts failed 
            print("⚠️<UNABLE TO GENERATE>")
            responses.append("")

    return responses

def extract_issue_resolution(text):
    """
    Extracts content of Issue Summary and Resolution (Handles cases with or without markdown (** **) around headings just in case a rare adjustment in output formatting occurs)
    """
    issue = re.search(r"\*?\*?\s*1[.)]?\s*Issue Summary:?\s*\*?\*?\s*(.*?)\s*\*?\*?\s*2[.)]?\s*Resolution:?\s*\*?\*?", text, re.DOTALL | re.IGNORECASE)
    resolution = re.search(r"\*?\*?\s*2[.)]?\s*Resolution:?\s*\*?\*?\s*(.*)", text, re.DOTALL | re.IGNORECASE)
    return (
        issue.group(1).strip() if issue else None,
        resolution.group(1).strip() if resolution else None
    )

# -------------------- Generate & Parse --------------------
results = [] # List of generated summaries 
prompts = [] # List of sent prompts (in same order as results)

# Batch process all prompts using DataLoader 
for batch in tqdm(dataloader, desc="Calling GenAI API"): 
    outputs = call_genai_api(batch)

    for prompt, output in zip(batch, outputs):
        norm_p = "".join(prompt.split())
        norm_o = "".join(output.strip().split())
        
        # Clean regurgitated prompt from output if present 
        if norm_o.startswith(norm_p): 
            output = output[len(prompt):].strip()
        results.append(output)
        prompts.append(prompt)

print("Retrying failed prompts...")
max_retries = 5
num_prompts = 0 # Track how many prompts required retry 
for i, (prompt, result) in enumerate(zip(prompts, results)):
    if result.strip() == "":
        num_prompts += 1
        for attempt in range(max_retries):
            retry = call_genai_api([prompt])[0]
            if retry.strip():
                # Remove regurgitated prompt again if necessary 
                norm_p = "".join(prompt.split())
                norm_o = "".join(retry.strip().split())

                if norm_o.startswith(norm_p):  
                    retry = retry[len(prompt):].strip()

                results[i] = retry
                print(f"✅ Retry success at index {i} (attempt {attempt+1})")
                break
            else:
                print(f"❌ Retry failed at index {i} (attempt {attempt+1})")
                time.sleep(0.3*(attempt + 1) + random.uniform(0,0.2))  # light exponential delay based on retry attempt number
    
print(f"{num_prompts} prompts had to be retried")

# Store final LLM outputs 
df_tickets["ticket_summary"] = results

# Backup: Drop rows where the model produced no output  
df_tickets = df_tickets[df_tickets["ticket_summary"].str.strip().astype(bool)]

# Extract issue and resolution into separate columns 
df_tickets[["issue_summary", "resolution"]] = df_tickets["ticket_summary"].apply(
    lambda txt: pd.Series(extract_issue_resolution(txt), index=["issue_summary", "resolution"])
)

# -------------------- Postprocessing ---------------------------
# Retain only relevant columns
df_tickets = df_tickets[['issuenumber', 'title', 'issue_summary', 'resolution']]

# Clean closure phrases in resolutions
def remove_generic_closure_sentences(text):
    """
    Removes generic or boilerplate phrases from LLM-generated resolutions that are:
    - Repetitive across many tickets
    - Uninformative (e.g., 'The ticket was closed')
    - Hallucinated (e.g., 'Feel free to follow up')

    This improves semantic clarity for downstream tasks like:
    - Embedding & clustering
    - FAQ generation
    - User-facing documentation

    Strategy:
    - Split the resolution into individual sentences.
    - Use regex patterns to match and exclude non-essential content.
    - Keep only informative, technical content.
    """

    sentences = sent_tokenize(text) # Break resolution into individual sentences 
    cleaned = []

    for s in map(str.strip, sentences):
        
        # Skip empty lines or artifacts such as random punctuation 
        if s == "" or re.fullmatch(r"[\"';\s]+", s): continue
        if re.search(r"^[;\"'\s]{2,}$", s): continue

        # Reopen and follow-up language
        if re.search(r"(?i)re[-\s]?open( the)? ticket", s): continue
        if re.search(r"(?i)(reply|respond|contact).*?(within|in|next).*?\d+\s*(days?|hours?)", s): continue
        if re.search(r"(?i)ticket (remains|will remain) open", s): continue
        if re.search(r"(?i)ticket (will|may)?\s*(be\s*)?(close[sd]?|closed)", s): continue
        if re.search(r"(?i)reopen the current ticket.*?open a new one", s): continue

        # Resolution confirmation or closure
        if re.search(r"(?i)(ticket|issue).*?marked\s*(as\s*)?resolved", s): continue
        if re.search(r"(?i)(ticket|issue).*?(was|is|has been)?\s*(closed|considered resolved)", s): continue
        if re.search(r"(?i)(the )?ticket was resolved", s): continue
        if re.search(r"(?i)mark(ed|ing)? (the )?ticket as resolved", s): continue
        if re.search(r"(?i)(resolving this|closing ticket|ticket'?s closure)", s): continue

        # New ticket creation
        if re.search(r"(?i)(create|submit|open).*?a new (support )?ticket", s): continue
        if re.search(r"(?i)a new ticket.*?(can|may|would|should).*?(be created|required|submitted)", s): continue
        if re.search(r"(?i)a new ticket", s): continue # covers all remaining cases of "a new ticket" mentioned

        # Gratitude and acknowledgments
        if re.search(r"(?i)(expressed|indicated).*?(gratitude|thanks|appreciation|satisfaction)", s): continue
        if re.search(r"(?i)appreciated the assistance", s): continue

        # Encouragement to follow up or contact
        if re.search(r"(?i)(feel free|don’t hesitate|you can).*?(contact|reach out)", s): continue
        if re.search(r"(?i)user was advised to contact.*?(support|help)", s): continue
        if re.search(r"(?i)further assistance.*?(is|was)?\s*(available|provided|needed)", s): continue

        # Lack of response or no action required
        if re.search(r"(?i)no further action.*?(is|was)?\s*required", s): continue
        if re.search(r"(?i)(no further response|no response).*?(from the user)?", s): continue
        if re.search(r"(?i)ticket.*?resolved.*?no response", s): continue
        if re.search(r"(?i)no further issues were reported", s): continue

        # Model regurgitation / footers
        if re.search(r"(?i)^please note", s): continue
        if re.search(r"(?i)(bullet points|commentary|names|greetings|sign[- ]?offs|references).*?(removed|excluded|not included|stripped)", s): continue
        if re.search(r"(?i)suggestion(s)? to (follow[- ]?up|re[- ]?open).*?(excluded|omitted|removed)", s): continue

        # Signature lines or affiliations
        if re.search(r"(?i)(Regards|Sincerely|Thank you).*\n.*(Ph\.?D|University|Department of)", s): continue

        # If none of the rules match, keep the sentence
        cleaned.append(s)

    return " ".join(cleaned)

# Apply cleaning to the resolution column
df_tickets["resolution"] = df_tickets["resolution"].apply(remove_generic_closure_sentences)

# -------------------- Save Cleaned Data --------------------
df_tickets.to_csv(f"_2_summarize_tickets/{TICKET_SRC}_ticket_summaries.csv", index=False) 

