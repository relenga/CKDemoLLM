# Product Requirements Document (PRD)

## Card Kingdom ("CK") Buylist Processing Application

**Version:** 3.0  
**Date:** October 31, 2025  
**Status:** Phase 3 In Progress – Matching Engine Design Added

---

## Executive Summary

A full-stack web application that imports two sets of parts, determines how to match the parts and then calculates what parts should be purchased to maximize profits, given the available capital for purchases. 

### Data Import

Fetches, processes, manages and loads two main files into Pandas Dataframes:

- CK BuyList from a JSONP file located at a URL with 140k+ records.
- Vendor SellList uploaded from CSV spreadsheets that the user selects via the UI. Users will upload a single CSV file for each purchasing run.

Both files contain information about trading cards that the two organizations have or want to buy. 

- CK BuyList contains identifying part numbers, card descriptions, quantities, and pricing that CK would like to buy.
- Vendor SellList contains a different part number scheme, card descriptions, available quantities, and pricing information that the vendor would like to sell.

---

## Part Matching (OLD)

A critical issue is that the two imported part files use different part number schemes, so we need a component that can match the different items based on description information about the cards and potentially pricing for the cards.

This to-be-defined component will use the two Dataframes, and potentially a mapping table from prior runs, to match the parts in each file. When the program runs, it will generate:

1. A mapping table (or dataframe) that links the part numbers between the two Dataframes (e.g., BuyList.BuyProductId and SellList.TCGPlayerId) along with any matching probability. [QUESTION: What's the minimum matching probability threshold? A: TBD]
2. An Error report that lists any errors found in mapping
3. Matching statistics that can be displayed for the user in the Web UI.
4. Potentially Human-in-the-loop functionality to validate any part matching, particularly where the application is not sure. [QUESTION: What UI will be used for human validation? Table view with approve/reject buttons? A: TBD]
5. Potentially an AI agent that reviews the mapping for potential errors and that either sends the problem back for refinement or decides that the mapping is correct and moves on to the Purchasing Advice functions. [QUESTION: Which AI service/model will be used? OpenAI, local LLM? A: Local LLM]

---

## Part Matching Engine (Phase 3 Design)

**Version:** 3.0  
**Date:** October 31, 2025  
**Status:** Design Stage – Architecture and Algorithm Defined

---

### Executive Summary

This phase introduces a scalable and intelligent **Part Matching Engine** that replaces the legacy text-matching placeholder logic. The new system matches vendor SellList records (~14K) against Card Kingdom's BuyList (~1.4M) using a hybrid of **vectorized text similarity (TF-IDF + cosine similarity)** and **optional LLM-assisted review** for ambiguous cases.

The goal is to provide accurate, explainable, and fast part matching across large datasets, with the flexibility to incorporate human validation or machine learning refinement in future iterations.

---

### System Overview

**Objective:** Automatically link Vendor and CK card listings that refer to the same item, despite using different naming schemes and inconsistent text formats.

**Core Components:**

1. **Preprocessing Module** – Cleans and normalizes text fields, combines key attributes (name, set, rarity, foil, etc.) into composite match strings.
2. **Vectorization Module** – Converts text into numeric TF-IDF vectors for fast similarity scoring.
3. **Candidate Search Engine** – Uses cosine similarity to retrieve top-N BuyList candidates for each SellList record.
4. **Confidence Classifier** – Assigns confidence scores and separates clear matches from uncertain ones.
5. **LLM Review Layer (optional)** – Invokes a local or API-based LLM to resolve uncertain matches.
6. **Reporting Layer** – Outputs matched pairs, confidence statistics, and error reports.

---

### Functional Flow

1. **Input:**
   
   - `buy_df` (BuyList) and `sell_df` (SellList) as pandas DataFrames.
   - Each includes name, set, rarity, foil, and pricing fields.

2. **Preprocessing:**
   
   - Normalize case and punctuation.
   - Create a new `composite` column combining multiple descriptive fields.
   - Example composite: `"saruman of many colors the lord of the rings m foil:false"`

3. **Vectorization:**
   
   - Use `scikit-learn`'s `TfidfVectorizer` to transform text into vectors.
   - Store both BuyList and SellList vectors in memory for similarity scoring.

4. **Candidate Search:**
   
   - Compute cosine similarity between Sell and Buy vectors.
   - Retrieve top-5 most similar BuyList candidates per Sell record.
   - Save candidate pairs with scores to a new DataFrame (`candidate_df`).

5. **Confidence Classification:**
   
   - Apply a configurable threshold (default: 0.85).
   - Split results into:
     - **Confident Matches** (≥ threshold)
     - **Uncertain Matches** (< threshold)

6. **LLM Review (Optional):**
   
   - Send uncertain matches to an LLM agent that compares Sell and Buy records.
   - Prompt asks model to decide: `MATCH`, `NO MATCH`, or `UNSURE`.
   - Integrate local LLMs (e.g., Llama 3, Mistral) or API-based models.

7. **Output and Reporting:**
   
   - `match_df` – final confident matches.
   - `uncertain_df` – low-confidence or multi-candidate matches.
   - `error_report.csv` – unmatched or conflicting results.
   - Summary statistics for accuracy and performance.

---

### Technical Architecture

#### Folder Structure

```
matcher/
├── __init__.py
├── preprocess.py          # Text normalization & composite generation
├── vectorizer.py          # TF-IDF vectorization and cosine similarity
├── matcher_core.py        # Confidence classification and result merging
├── llm_review.py          # Optional LLM agent for uncertain matches
└── run_matcher.py         # Orchestrator script for end-to-end processing
```

#### Libraries

- **pandas** – DataFrame handling  
- **numpy** – numeric computation  
- **scikit-learn** – TF-IDF vectorizer and cosine similarity  
- **langchain / openai (optional)** – for LLM-based review  

---

### Data Flow Summary

1. **Preprocessing:** `preprocess_dataframe()` → adds composite text field.  
2. **Vectorization:** `build_tfidf_vectors()` → returns vectorized Buy/Sell matrices.  
3. **Similarity Search:** `find_top_candidates()` → produces candidate pairs with scores.  
4. **Filtering:** `select_best_matches()` → keeps top match per Sell record.  
5. **LLM Review (optional):** `review_uncertain_rows()` → reviews low-confidence matches.  
6. **Output:** final DataFrames and CSVs.

---

### Outputs

1. **Matched Results** – Each Sell part linked to a Buy part with confidence score.
2. **Uncertain List** – Items requiring review or manual intervention.
3. **Error Report** – Missing, duplicate, or invalid matches.
4. **Match Statistics** – Summary of match counts, average confidence, and processing time.

---

### Performance Targets

- Process 14K Sell records vs. 1.4M Buy records in < 2 minutes using TF-IDF.  
- > 95% accuracy for confident matches (threshold ≥ 0.85).  
- Memory footprint < 500MB for in-memory vectors.  
- Optional LLM review limited to ≤5% of total records.

---

### Future Enhancements

1. **Persistent Match Cache** – Store confirmed matches for reuse across runs.
2. **Approximate Nearest Neighbor (FAISS/HNSW)** – Speed up vector search for 1.4M+ records.
3. **Incremental Learning** – Fine-tune thresholds using human corrections.
4. **UI Integration** – Add match review table with accept/reject buttons.
5. **Semantic Embeddings** – Replace TF-IDF with transformer-based embeddings.

---

### Open Questions

- [QUESTION: Should threshold be configurable via UI? A: TBD] 
- [QUESTION: Should LLM review run automatically or only on user approval? A: TBD] 
- [QUESTION: Should we persist intermediate match tables? A: Probably yes for Phase 4] 

---

### Summary

The new Part Matching Engine provides a scalable, explainable, and extensible foundation for automatic part number alignment between BuyList and SellList datasets. It replaces brute-force fuzzy matching with a hybrid vectorized approach that supports optional AI-assisted reasoning for ambiguous cases.  

This design sets the stage for downstream **Purchase Optimization** and **Automated Order Generation** features in later phases.

---

## Purchase Advice Function

This part of the application will take the mapping data to determine the optimal purchase decision (what cards to buy and how many) that maximize profits for the budgeted purchase amount. [QUESTION: What optimization algorithm will be used? Linear programming? Greedy algorithm? A: TBD]


## Prototype todos
1. Refactor Selllist to SellList

