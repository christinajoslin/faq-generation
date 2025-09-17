# Initial Ticket Cleaning

This folder contains code designed to preprocess the ticket content (labeled as `customernote`) associated with each HPC support ticket. All formatting within the `customernote` field is removed, and individual messages are separated by semicolons for downstream processing. 
This project builds on the original dataset and metrics introduced in **TicketHub**, a system developed to support actionable analysis of support tickets using NLP methods [1](#references). 

--- 

## Databases
The data is sourced from three ticket databases, all of which were integrated and analyzed in the original TicketHub application: 

### tdx
- **Displayed as:** "Purdue Team Dynamix" in TicketHub
- **Tickets:** 6,300+ tickets from 7/11/2023 to present 
### anvil
- **Displayed as:** "Anvil Jira" in TicketHub
- **Tickets:** 1,800+ tickets from 3/24/2023 to present
### postgres
- **Displayed as:** "Purdue Footprints" in TicketHub
- **Tickets:** 19,714 tickets from 8/29/2016 to 8/3/2023
- *Note:* This database is no longer being updated, as all new tickets have migrated to Anvil. As a result, the pipeline for `postgres` is no longer used. 

All databases are hosted on **Geddes**, Purdue's high-performance computing system. 

--- 

## Initial Ticket Filtering 

Ticket filtering was performed in two stages: anomaly detection and recency filtering. Both stages align with methodologies developed in TicketHub for surfacing evolving or recurring support issues  [1](#references).

### Stage 1 - Anomaly Filtering (90-Day Window)
To identify high-priority clusters, we first applied anomaly detection over a 90-day window of recent ticket activity. This step enhances the relevance of generated FAQs by focusing on clusters with a surge in user demand.
- **Daily aggregation** of ticket counts
- **Temporal features:** day of week, week of month, month, and year 
- **Z-scores** computed again historical averages within each category 
- **Isolation Forest** applied to z-score vectors to detect anomalies and yield a score between -1 and 1 
- **Scoring range:**
    - **No anomaly:** $$\text{score} > 0$$
    - **Borderline anomaly:** $$-0.05 < \text{score} \le 0$$
    - **Confirmed anomaly:** $$\text{score} \le -0.05$$

Days that were considered confirmed anomalies were **aggregated by cluster** to produce a time series reflecting evolving trends. Clusters in the **top 30% (above the 70th percentile)** in anomaly counts were retained for further processing. 

### Stage 2 - Recency Filtering (2-Year Window)
After anomaly-based filtering, we constrained the dataset to only tickets from the past 2 years to ensure recency. This two-stage filtering approach resulted in ~10-20 clusters and ~900-2,000 tickets per dataset, optimized for generating high-utility, up-to-date FAQs.  

--- 

## Data Layout & Formatting Notes
In addition to ticket records, each database contains multiple tables. However, **only the ticket table** contains the `customernote` field with the actual ticket messages. All ticket messages undergo the following filtering: 
- Tickets older than **2 years** are removed 
- Tickets outside the **top 30% of anomaly-ranked clusters** are excluded 

### tdx 
- **Source:** RCAC/ITaP integration
- **Format:** HTML 
- Messages include status updates interleaved with user content 

### anvil
- **Source:** Presumed from ACCESS Anvil support
- **Format:** Custom Jira-style markup 
- Messages include inline metadata 

### postgres
- **Source:** Presumed from web scraping 
- **Format:** TicketHub separate entries using double line breaks

--- 

## Database-Specific Cleaning Steps 
Due to inconsistent formatting across three sources, the cleaning steps differ slightly by database. 

### Common Cleaning for All Databases
- Names, emails, phone numbers, ID numbers
- Redundant whitespace, empty entries
- Repeating special characters
- Leading/trailing whitespace 

--- 

### Additional Cleaning by Source 
#### tdx 
- HTML tags
- Status change logs
- Filler text 

#### anvil 
- Jira formatting 
- Signatures
- Image placeholders

#### postgres 
- No additional modifications beyond common steps 

--- 

## Folder Contents
- `clean_tickets_anvil.py`: Cleans tickets from the Anvil Jira dataset.
- `clean_tickets_postgres.py`: Cleans tickets from the Purdue Footprints (Postgres) dataset.
- `clean_tickets_tdx.py`: Cleans tickets from the Purdue Team Dynamix (TDX) dataset.
- `cluster_selection.py`: Performs initial cluster selection and anomaly filtering.
- `init_anvil_cln_tkts.csv`: Output file containing cleaned Anvil tickets.
- `init_postgres_cln_tkts.csv`: Output file containing cleaned Postgres tickets.
- `init_tdx_cln_tkts.csv`: Output file containing cleaned TDX tickets.
- `names.parquet`: List of common staff member names to be anonymized or replaced. (*Note:* Parquet is a columnar storage format used for efficient data processing.)
- `auto_gen_rep.txt`: Text file listing frequently observed auto-generated ticket elements.
- `clean_all_tickets.sh`: Bash script used to run all ticket-cleaning scripts.

--- 

## Dependencies 

### Standard Libraries
- `datetime` (working with date and time objects)  
- `os` (environment and path management)  
- `sys` (system-level operations and argument access) 

### Third-Party Libraries
Install via `pip install -r requirements.txt` or individually:
- `pandas` (data manipulation and analysis)  
- `sqlalchemy` (SQL database interaction and ORM support)  
- `markdownify` (converting HTML to Markdown)  
- `beautifulsoup4` (parsing HTML/XML with `BeautifulSoup`)

--- 

## References 
1. Rodenbeck, S., & Suk Uhr, Y. (2023). TicketHub: Enabling Actionable Analysis of Support Requests With NLP. In *Practice and Experience in Advanced Research Computing 2023: Computing for the Common Good* (pp. 109–116). https://doi.org/10.1145/3569951.3604397

--- 

## Authors 
**Christina Joslin** & David Burns
Student Interns, June 2025 

