"""
Script to generate structured FAQs from ticket subclusters using a finetuned LLM.

Author: Christina Joslin  
Date: 7/6/2025  
Purpose:
    - Load subclustered support ticket summaries and resolutions.
    - Generate exactly one FAQ per subcluster using an LLM (Phi-4).
    - Enforce strict FAQ formatting and content policies.
    - Perform a post-processing pass to remove wrap-ups and consolidate similar entries.
    - Save final cleaned and formatted FAQs in Markdown for downstream publishing.
"""
# -------------------- Load Libraries --------------------
import pandas as pd                      # DataFrame operations
import requests                          # API calls to GenAI endpoint
import re                                # Regular expressions for Q&A parsing
from dotenv import load_dotenv           # Load API key from environment
import os                                # For accessing environment variables

# -------------------- Initial Config --------------------
# Load environment variables
load_dotenv()
GENAI_API_KEY = os.getenv("GENAI_API_KEY")
GENAI_MODEL = "phi4:latest" 
GENAI_API_URL = "https://genai.rcac.purdue.edu/api/chat/completions"
TICKET_SRC = "tdx" # Change to 'anvil' if needed

# -------------------- Load Input Data --------------------
df_tickets = pd.read_csv(f"_3_select_tickets/{TICKET_SRC}_top_faq_candidates.csv")

# Parse summaries and resolutions into lists 
df_tickets['All_Summaries'] = df_tickets['All_Summaries'].apply(lambda x: [s.strip() for s in x.split('|||') if s.strip()])
df_tickets['All_Resolutions'] = df_tickets['All_Resolutions'].apply(lambda x: [r.strip() for r in x.split('|||') if r.strip()])


# -------------------- Prompt Builder --------------------
# Builds a structure prompt for FAQ generation per subcluster
def build_faq_prompt(summaries, resolutions, word_limit=2000):
  header = """
**Role**
You are an expert assistant tasked with generating FAQs for High-Performance Computing (HPC) systems. You possess deep knowledge of HPC architectures, technical challenges, and troubleshooting methods. Your goal is to create **ONE CONCISE, INFORMATIVE, AND ACTIONABLE FAQ** based on real support scenarios. This FAQ will help users resolve common issues **WITHOUT** submitting a support ticket.

**Your Task**
Given a list of issue summaries and their corresponding resolutions, identify the **MOST COMMON ISSUE** and write **EXACTLY ONE FAQ ENTRY** in the format described below. **AVOID RARE OR USER-SPECIFIC PROBLEMS**.
- If the issue affects **ALL OR MOST RCAC CLUSTERS**, write a **GENERAL FAQ** (DO NOT mention any specific cluster).
- If the issue is **UNIQUE TO A SPECIFIC CLUSTER**, include that cluster name (from the allowed list below).

**CONTENT RULES (VERY STRICT!)**
- **GENERATE ONLY ONE Q&A PAIR.**
- Keep the response BRIEF and FOCUSED, as the target audience needs quick, general guidance -- not detailed walkthroughs or edge-case explanations.
- **REMOVE OR OMIT ALL PERSONAL OR GROUP IDENTIFIERS**, including:
    - Usernames (e.g., `jdoe123`) → replace with `your-username`
    - Department names
    - Ticket IDs
    - Lab- or project-specific queue names (e.g., `CHEMML-h`, `astro-f`)
    - Job titles (e.g., PhD student, Professor)
- **YOU MAY INCLUDE COMPUTING CLUSTER NAMES** from the following list **ONLY** (NSF is NOT a COMPUTING CLUSTER):
    Bell, Gilbreth, Weber, Scholar, Hammer, Negishi, Geddes, Anvil, Gautschi
- **DO NOT INCLUDE CLOSING PHRASES** such as “By following these steps…” or “This should resolve your issue.”
- DO NOT mention CONTACTING SUPPORT 

**FAQ FORMAT (VERY STRICT!)**
Q: [question based on the **MOST COMMON ISSUE**]
A: [answer based on BOTH the question AND resolutions]

**Examples (CORRECT FORMAT)**

**General FAQ Example (DO NOT COPY)**
Q: What should I do if my SSH connection hangs?
A: If your terminal hangs while connecting via SSH, try the following steps:

1. **Check your network connection**, especially if you're on Wi-Fi. A weak or unstable connection can cause SSH to hang.
2. **Retry the connection.** Sometimes, a login node may be temporarily overloaded. Attempt reconnecting after a short wait.
3. **Switch to a different front-end node** if available. File system issues on the current node (e.g., home, scratch, or depot) may cause the terminal to freeze.

**Cluster-Specific FAQ Example (Bell) (DO NOT COPY)**
Q: Does the Bell cluster share the same home directory as other RCAC clusters?
A: No. The Bell clusters uses as **separate home directory**, which is only accessible from Bell's front-end and compute nodes. This directory is **not shared** with other RCAC systems.

To access files from your main RCAC home directory:
- **Manually copy files** using tools like `rsync` or `scp` from other cluster account to Bell.
- If you plan to use `hsi` or `htar` for accessing the Fortress tape archive from Bell, refer to the **keytab generation** FAQ for a temporary workaround due to a known integration issue.

Limit your respone to **NO MORE THAN 200 WORDS** 
**Begin your response with `Q:` and write exactly one FAQ entry. DO NOT INCLUDE ANYTHING ELSE.**

**Input Data**
"""
  current_word_count = len(header.split())
  body_lines = []

  # Append each issue/resoultion pair to the prompt body until word limit is reached
  for i, (summary, resolution) in enumerate(zip(summaries, resolutions)):
      issue_text = f"Issue Summary {i+1}: {summary}"
      resolution_text = f"Resolution {i+1}: {resolution}"
      entry_word_count = len(issue_text.split()) + len(resolution_text.split())


      if current_word_count + entry_word_count > word_limit:
          break # Stop adding if the word limit is exceeded

      body_lines.append(issue_text)
      body_lines.append(resolution_text)
      body_lines.append("")  # add space between each issue and summary pair
      current_word_count += entry_word_count

  return f"{header}\n" + "\n".join(body_lines)

# -------------------- Post-Processing --------------------
def clean_faq_answer(text):
    """ 
    Additional postprocessing that acts as a safeguard against any username leaks & removes excess wrap-up phrases
    """
    # Remove wrap-up phrases
    wrapup_patterns = [
        r"(?i)by following these steps.*?[.!]$",
        r"(?i)this should (fix|resolve).*?[.!]$",
    ]
    for pattern in wrapup_patterns:
        text = re.sub(pattern, "", text).strip()

    # Mask usernames
    text = re.sub(r"\b[a-z]{1,10}[0-9]{1,5}\b", "your-username", text)

    return text

# ------------------ FAQ Merge Prompt ----------------------
# Sends 5 FAQ entries to the LLM and returns a merged, cleaned FAQ entry 
def merge_faq_candidates(faq_candidates):
    """
    Merge 5 candidate FAQ entries into one concise FAQ entry using an LLM.
    """
    merge_prompt = """
**Role**
You are an expert FAQ editor for HPC support. You are given 5 candidate FAQ entries that are expected to describe the SAME TECHNICAL ISSUE. These candidates were generated automatically and may include unrelated or off-topic entries.

**Your Task**
- MERGE the 5 FAQ candidates into ONE concise FAQ focused on the most common technical issue discussed.
- IGNORE off-topic or minority issues. Focus only on the **MAJORITY PROBLEM** and its solution.
- ELIMINATE any redundant phrases, inconsistencies, or extra details.
- DO NOT combine unrelated failure types.
- Keep the response BRIEF and FOCUSED, as the target audience needs quick, general guidance -- not detailed walkthroughs or edge-case explanations.

**CONTENT RULES (VERY STRICT!)**
- DO NOT INCLUDE closing phrases such as “By following these steps...” or “This should resolve the issue.”
- DO NOT INCLUDE usernames or group-specific identifiers. REPLACE ALL SUCH TEXT WITH your-username.
- DO NOT WRITE a question or answer that is user-specific, overly personalized, or tailored to one individual's setup or project.
  The final FAQ must address a general technical issue that applies across multiple users or scenarios.

**Output Format**:
Q: [merged question]
A: [merged answer]

**RESPONSE LIMITS (VERY STRICT!)**
- Your response must be NO MORE THAN 200 WORDS
- KEEP your response BRIEF
- DO NOT mention CONTACTING SUPPORT 

**Candidate FAQs to merge:**
""" + "\n\n".join(faq_candidates).strip()

    headers = {
        "Authorization": f"Bearer " + GENAI_API_KEY,
        "Content-Type": "application/json"
    }
    body = {
        "model": GENAI_MODEL,
        "messages": [{"role": "user", "content": merge_prompt}],
        "temperature": 0.2,
        "max_tokens": 250,
        "stream": False,
    }

    r = requests.post(GENAI_API_URL, headers=headers, json=body)

    if r.status_code == 200:
        content = r.json()["choices"][0]["message"]["content"]
        print("====== MERGED RESPONSE ======")
        print(content)

        # Pattern to extract questions
        entries = re.findall(
        r"\*{0,2}Q[:\.]\*{0,2}\s*(.*?)(?=\n\*{0,2}A[:\.]\*{0,2})",
        content,
        re.DOTALL
        )

        # Pattern to extract answers
        answers = re.findall(
        r"\*{0,2}A[:\.]\*{0,2}\s*(.*?)(?=\n\*{0,2}Q[:\.]\*{0,2}|\Z)",
        content,
        re.DOTALL
        )

        if entries and answers:
            question = entries[0].strip()
            answer = answers[0].strip()
            answer_cleaned = clean_faq_answer(answer)
            return f"Q: {question}\nA: {answer_cleaned}\n"
        else:
            print("⚠️ Could not extract Q/A from merged content.")
            return None
    else:
        print("❌ Merge Request Failed")
        print(f"Status Code: {r.status_code}")
        print(f"Response: {r.text}")
        return None

# ----------------------- FAQ Generation Loop ------------------------------
faq_entries = []
num = min(15, len(df_tickets)) # Only generate up to 15 FAQs

for i in range(num):
    candidate_faqs = []
    for _ in range(5):  # Generate 5 candidate FAQs per subcluster 
        prompt = build_faq_prompt(df_tickets['All_Summaries'][i], df_tickets['All_Resolutions'][i])
        headers = {
        "Authorization": f"Bearer {GENAI_API_KEY}",
        "Content-Type": "application/json"
        }
        body = {
            "model": GENAI_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,  
            "max_tokens": 250, 
            "stream": False
        }
        r = requests.post(GENAI_API_URL, headers=headers, json=body)
        if r.status_code == 200:
            content = r.json()["choices"][0]["message"]["content"]
            match = re.search(r"Q:\s?.*?\nA:\s?.*?(?=\nQ:|\Z)", content, re.DOTALL)
            if match:
                candidate_faqs.append(match.group(0).strip())
        else: 
            print("❌ Invalid Request")
            print(r.status_code)
    #print("======== Candidate FAQs ========")  
    #print(candidate_faqs) 
    if candidate_faqs:
        merged_faq = merge_faq_candidates(candidate_faqs)
        if merged_faq:
            faq_entries.append(merged_faq)

# -------------------- Output Markdown File --------------------
# Converts raw Q&A pairs into markdown format. 
def markdownify_faq(raw_text):
    lines = raw_text.strip().split("\n")
    markdown_lines = []

    for line in lines:
        if line.startswith("Q:"):
            markdown_lines.append(f"**Q: {line[2:].strip()}**\n")
        elif line.startswith("A:"):
            markdown_lines.append(f"**A:** {line[2:].strip()}\n")
        else:
            markdown_lines.append(line)

    return "\n".join(markdown_lines)

#print(f"Found {len(faq_entries)} cleaned FAQs") Debugging 

# Save to Markdown 
output_path = f"{TICKET_SRC}_clean_parsed_faqs.md"
with open(output_path, "w", encoding="utf-8") as f:
    for faq in faq_entries:
        formatted_faq = markdownify_faq(faq)
        f.write(formatted_faq.strip() + "\n\n")
