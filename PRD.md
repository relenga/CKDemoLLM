# Product Requirements Document (PRD)

## Card Kingdom ("CK") Buylist Processing Application

**Version:** 2.0  
**Date:** October 30, 2025  
**Status:** Phase 2 Complete - Core Functionality + CSV Upload Delivered

---

## Executive Summary

A full-stack web application that imports two sets of parts, determines how to match the parts and then calculates what parts should be purchased to maximize profits, given the available capital for purchases. 

### Data Import

fetches, processes, manages and loads two main files into Pandas Dataframes:

- CK BuyList from a JSONP file located at a URL with 140k+ records. 
- Vendor SellList that uploaded from csv spreadsheets that the user will select on the UI. Users will upload a single CSV file for each purhasing run.  Simple file dialog boxes will work. 

Both files contain information about trading cards that the two organizations have or want to buy. 

- CK BuyList list contains identifying part numbers, card descriptions, quantities and pricing that CK would like to buy the cards for. 

- Vendor SellList contains a different part number scheme, card descriptions, available quantities and pricing information that the vendor would like to sell. 

### Part Number Matching

A critical issue is that the two imported part files use different part number schemes, so we need a component that can match the different items based on description information about the cards and potentially pricing for the cards.

This to-be-defined component will use the two Dataframes, and potentially a mapping table from prior runs, to match the parts in each file.  [QUESTION: What algorithm will be used for matching? Fuzzy string matching? ML-based?] When the program runs, it will generate:

1. A mapping table (or dataframe) that links the part numbers between the two Dataframes (e.g. BuyList.BuyProductId and SellList.TCGPlayerId) along with any matching probability. [QUESTION: What's the minimum matching probability threshold? A: TBD]

2. An Error report that lists any errors found in mapping

3. Matching statistics that can be displayed for the user in the Web UI.

4. Potentially Human-in-the-loop functionality to validate any part matching, particularly matching where the application is not sure. [QUESTION: What UI will be used for human validation? Table view with approve/reject buttons?  A: TBD]

5. Potentially an AI agent that reviews the mapping for potential errors and that either sends the problem back for refinement or decides that the mapping is correct and moves on to the Purchasing Advice functions. [QUESTION: Which AI service/model will be used? OpenAI, local LLM? A: Local LLM]

## Purchase Advice Function

This part of the application will take the mapping data to determine the optimal purchase decision (what cards to buy and how many) that maximize profits for the budgeted purchase amount.  [QUESTION: What optimization algorithm will be used? Linear programming? Greedy algorithm? A: TBD] This function will use:

1. BuyList quantity/pricing data

2. SellList quantity/pricing data

3. Discount offered by the vendor, including:
   
   Order value discounts:
   
   $2500  - 10% 
   
   $5,000 – 12%
   
   $10,000 - 15% 
   
   $20,000 - 20% 
   
   $40,000 – 25% 
   
   Additional Discounts:
   
   "Take All" discount - 1% discount if buy takes all available items for a part

This part of the application will have a UI component that allows the user to enter a planned and maximum budget.  

The system will generate one or more alternative purchase plans that will maximize the gross profit achievable for the order. [QUESTION: How many alternative plans should be generated? Top 3? Top 5? A: TBD]  It may have options to allow the user to modify the order, if so it will calculate the new budget and gross profit for that order. 

When the user is satisfied with the purchase plan, the system will generate a JSON Purchase Order that contains the Vendor's part number, description along with the Buyer's Part number and description, quantities and pricing.  It will display all applicable discounts for each line and for the order as a whole. [QUESTION: Should we also support PDF or Excel export formats? A: Probablyl Excel]

## Product Overview

### Vision

Create a reliable, high-performance system for processing large-scale data with a modern web interface and robust backend infrastructure.  It will import two sets of parts, match them and calculate the optimal purchase quantities/parts to maximize gross profitability. 

### Current State (Phase 2 Complete)

- ✅ Fully functional React + FastAPI application
- ✅ Real-time processing of 140,664 records in ~1.8 seconds
- ✅ CSV and Excel file upload and processing with filtering rules
- ✅ Dual data source support (API + CSV uploads)
- ✅ Pandas dataframe storage with memory efficiency monitoring
- ✅ Professional error handling and monitoring
- ✅ Stable development environment established

---

## Technical Architecture

### Frontend

- **Technology:** React 18 + TypeScript + Material-UI
- **Port:** http://localhost:3001
- **Features:** 
  - Upload interface with progress feedback
  - Real-time processing status
  - Formatted number display (140,664 records)
  - Error handling and user feedback

### Backend

- **Technology:** FastAPI + Python + pandas
- **Port:** http://localhost:8002
- **Architecture:** Unified processing core (`fileUpload_core.py`)
- **Performance:** 140K+ records in 1.8 seconds (API), 24K Excel records in 1.3 seconds
- **Memory:** Efficient dataframe storage with monitoring
- **Features:**
  - Async data processing with timeout handling
  - Memory monitoring and reporting
  - JSONP parsing and data transformation
  - CSV and Excel file upload with encoding detection  
  - Smart filtering rules for vendor data
  - Comprehensive JSON serialization for complex datasets
  - Dual dataframe storage (buylist + selllist)
  - Automatic dataframe clearing
  - CORS middleware for frontend integration

### Data Processing

#### Buylist Processing (Card Kingdom API)
- **Source:** Card Kingdom JSONP API (https://www.cardkingdom.com/json/buylist.jsonp)
- **Volume:** 27MB+ raw data → 140,664 processed records
- **Storage:** In-memory pandas dataframe
- **Columns:** BuyProductId, BuyCardName, BuyEdition, BuyRarity, BuyFoil, BuyPrice, BuyQty, BuyImage

#### Selllist Processing (CSV/Excel Upload)
- **Source:** User-uploaded CSV (.csv) or Excel (.xlsx, .xls) files
- **Processing:** Column mapping, filtering, validation, NaN handling
- **Storage:** In-memory pandas dataframe
- **Performance:** 24K records processed in 1.3 seconds
- **Filtering Rules:**
  - Remove rows with empty TCGplayer IDs
  - Keep only products containing "Magic" in Product Line
- **Columns:** TCGplayerId, SellProductLine, SellSetName, SellProductName, SellNumber, SellRarity, SellCondition, SellMarketPrice, SellLowPrice, SellQuantity

---

## Current Feature Set

### Core Features ✅

1. **Data Upload & Processing**
   
   - Card Kingdom Buylist Import
     - Fetch data from Card Kingdom API
     - JSONP wrapper cleaning
     - Data transformation and validation
     - Pandas dataframe storage
   - Vendor SellList Import
     - Import Data from CSV and Excel files (.csv, .xlsx, .xls)
     - Clean, filter and transform data with NaN handling
     - Panda dataframe storage
   - Vendor SellList Import Instructions
     - File formats supported: CSV (.csv) and Excel (.xlsx, .xls)
     
     - We want to load only the first 10 columns, which are listed below (csv column-alias name):
       
       * TCGplayer Id -TCGplayerId
       
       * Product Line-SellProductLine
       
       * Set Name-SellSetName
       
       * Product Name-SellProductName
       
       * Number-SellNumber
       
       * Rarity-SellRarity
       
       * Condition-SellCondition
       
       * TCG Market Price-SellMarketPrice
       
       * TCG Low Price-SellLowPrice
       
       * Total Quantity-SellQuantity
     
     - Any rows that do not have a value in the first column (TCGplayer Id) should be ignored.
     
     - Any rows that do not contain "Magic" in the second column (Product Line) should be ignored

2. **Part Matching** 
   
   1. Import BuyList and SellList Dataframes 
   2. Potentially - Import existing Match Table 
   3. For each SellList item, determine the matching item in the BuyList using existing Match Table or descriptive text in BuyList and SellList Dataframes 
   4. Verify that there is a 1:1 relationship between BuyList and SellList items [QUESTION: What happens with 1:many or many:1 relationships? A: TBD, but that will probably cause an error.]
   5. Potentially - Add Human-In-The-Loop functionality to fix errors
   6. Potentially - Add LLM Agent to verify results and fix errors 
   7. Save the Match Table as Dataframe (and potentially a persistent storage method).
   8. Report any matching errors (e.g. missing items, multiple matches, etc.)
   9. Report statistics about the matching run (e.g., how many items matched, errors, etc.)

3. **Purchase Advice Function** 
   
   1. Import Matching Dataframe (and potentially the BuyList and SellList dataframes) 
   2. Get purchase budget, or range, from the User [QUESTION: Should we support budget ranges or just single amounts? A: TBD, probably ranges]
   3. Calculate the optimal buy: the purchase items and quantities that generate the maximum profit, given the purchase amount, calculated using the BuyList.BuyPrice, The SellList.SellPrice, any item discounts and order discounts. 
   4. Get Human-in-the-loop approval [QUESTION: What approval workflow? Simple approve/reject or detailed review? A: probably simple approval]
   5. Generate a Purchase order for the user in JSON format. [QUESTION: Should we also generate human-readable formats like PDF? A: TBD]

4. **Performance Monitoring**
   
   - Processing time tracking
   - Memory usage monitoring
   - Request/response metrics
   - Debug information logging

5. **Data Access APIs**
   
   **Buylist Endpoints:**
   - `/api/buylist/upload` - Process Card Kingdom API data
   - `/api/buylist/stats` - Get buylist dataframe statistics
   - `/api/buylist/sample` - View buylist sample records
   
   **Selllist Endpoints:**
   - `/api/selllist/upload` - Process CSV file uploads
   - `/api/selllist/stats` - Get selllist dataframe statistics
   - `/api/selllist/sample` - View selllist sample records
   - `/api/selllist/clear` - Clear selllist dataframe
   
   **System:**
   - `/health` - System health check

6. **User Interface**
   
   - Clean Material-UI design
   - Upload button with status feedback
   - Processing time display
   - Error handling with user messages

### Technical Features ✅

1. **Reliability**
   
   - Async processing with 60-second timeout
   - Error handling and recovery
   - Automatic memory management
   - Stable server operation

2. **Performance**
   
   - Thread pool execution for non-blocking operations
   - Memory monitoring (before/after tracking)
   - Efficient pandas operations
   - Fast JSON serialization

3. **Development Environment**
   
   - VS Code integration (Command Prompt terminals)
   - Hot reload for frontend changes
   - Comprehensive logging
   - CORS configuration for local development

---

## Technical Constraints & Decisions

### Environment Requirements

- **VS Code Development:** Command Prompt terminals (PowerShell causes server shutdown issues)
- **Python Virtual Environment:** Required for dependency isolation
- **Node.js:** Required for React development server
- **Memory:** ~300MB peak usage during processing

### Architecture Decisions Made

1. **FastAPI over Flask:** Better async support and automatic documentation
2. **Pandas over raw Python:** Efficient large dataset handling
3. **In-memory storage:** Fast access, suitable for current scale
4. **JSONP parsing:** Handle Card Kingdom's specific API format
5. **Thread pool execution:** Prevent blocking the async event loop

### Known Technical Debt

1. **Data Persistence:** Currently in-memory only (lost on restart)
2. **VS Code PowerShell Issue:** Root cause unknown, workaround implemented
3. **Error Recovery:** Limited retry mechanisms for API failures
4. **Scalability:** Single-instance design, no horizontal scaling

---

## Performance Benchmarks

### Current Performance (Achieved)

- **Data Fetch:** ~1.4 seconds for 27MB
- **Data Processing:** ~0.4 seconds for 140K records
- **Total Processing:** ~1.8 seconds end-to-end
- **Memory Usage:** 65.28 MB for processed dataframe
- **Memory Efficiency:** Automatic clearing between uploads

### Performance Targets (Met/Exceeded)

- ✅ Process 100K+ records in <3 seconds
- ✅ Handle 25MB+ data files
- ✅ Memory usage <100MB for processed data
- ✅ Server stability during repeated operations

---

## User Stories (Completed)

### Primary User: Data Analyst/Developer

1. ✅ **As a user, I want to upload buylist and SellList data** so that I can analyze current market prices
2. ✅ **As a user, I want to see processing progress** so that I know the system is working
3. ✅ **As a user, I want formatted numbers** so that large record counts are readable
4. ✅ **As a user, I want error messages** so that I understand when something goes wrong
5. **As a user, I want the system to match parts** so that I can focus on optimizing my purchase decision 
6. **As a user, I want the system to optimize purchase decision** so that I can maximize the profit margin from the purchase 

### Secondary User: Developer/Maintainer

1. ✅ **As a developer, I want comprehensive logging** so that I can debug issues

2. ✅ **As a developer, I want memory monitoring** so that I can optimize performance

3. ✅ **As a developer, I want stable server operation** so that development is predictable

4. ✅ **As a developer, I want clean APIs** so that I can extend functionality

---

## Testing & Quality Assurance

### Manual Testing Completed ✅

- Multiple upload operations (verified stability)
- Large dataset processing (140K+ records buylist, 24K+ records selllist)
- Real-world Excel file processing (2.1MB files with NaN values)
- Error condition handling and JSON serialization fixes
- Frontend-backend integration
- Memory usage monitoring  
- Cross-terminal compatibility testing
- Dual dataframe coexistence validation

### Performance Testing ✅

- Repeated upload operations without degradation
- Memory leak testing (automatic clearing verified)
- Server stability under load
- Response time consistency

---

## Dependencies & Infrastructure

### Backend Dependencies

```
fastapi==0.104.1
uvicorn==0.24.0
aiohttp==3.9.1
pandas==2.1.4
psutil==7.1.2
```

### Frontend Dependencies

```
react==18.2.0
@mui/material==5.14.20
@mui/x-data-grid==6.18.2
axios==1.6.2
typescript==4.9.5
```

### Development Environment

- Python 3.11+ with virtual environment
- Node.js 16+ with npm
- VS Code with Command Prompt terminals
- Git for version control

---

## Technical Implementation

### Backend File Structure

```
backend/
├── main.py                 # FastAPI server with all endpoints
├── fileUpload_core.py      # Unified processing core for both data sources
├── test_selllist.csv       # Sample CSV data for testing
└── test_endpoints.py       # API endpoint test suite
```

### Core Processing Architecture

**`fileUpload_core.py`** - Unified processing module containing:

**Buylist Functions:**
- `process_buylist_data()` - JSONP parsing and transformation
- `get_buylist_stats()` - Dataframe statistics and memory usage
- `get_buylist_sample()` - Sample data for validation
- `clear_buylist_dataframe()` - Memory management

**Selllist Functions:**
- `process_selllist_file()` - CSV and Excel parsing, mapping, and filtering
- `process_selllist_csv()` - Legacy CSV-only function (backward compatibility)
- `get_selllist_stats()` - Dataframe statistics and memory usage  
- `get_selllist_sample()` - Sample data for validation
- `clear_selllist_dataframe()` - Memory management

**Shared Components:**
- Global dataframe storage (`_buylist_dataframe`, `_selllist_dataframe`)
- Column mapping constants (`COLUMN_MAPPING`, `CSV_COLUMN_MAPPING`)
- Logging and error handling utilities

### API Endpoint Architecture

**FastAPI Server (`main.py`)** provides RESTful endpoints:
- **File Upload Support:** `UploadFile` handling with encoding detection
- **Async Processing:** Thread pool execution for blocking operations
- **Memory Monitoring:** Real-time memory usage tracking
- **Error Handling:** Comprehensive exception handling with user-friendly messages
- **CORS Configuration:** Frontend integration support

---

## Security Considerations

### Current Security Measures

- CORS configuration for local development
- Input validation on API endpoints
- Error message sanitization
- No sensitive data storage

### Security Limitations

- Local development configuration only
- No authentication/authorization
- No data encryption at rest
- No audit logging

---

## Deployment & Operations

### Current Deployment

- Local development only
- Manual startup process
- In-memory data storage
- No persistence between restarts

### Operational Procedures

1. Start backend: `python main.py` in Command Prompt
2. Start frontend: `npm start` in separate terminal
3. Access application: http://localhost:3001
4. Monitor logs in terminal outputs

---

## Success Metrics (Achieved)

### Technical Metrics ✅

- **Uptime:** 100% during development sessions
- **Processing Speed:** 1.8s average for 140K records
- **Memory Efficiency:** 65.28 MB for processed data
- **Error Rate:** <1% during testing
- **API Response Time:** <100ms for non-processing endpoints

### Business Metrics ✅

- **Data Volume:** Successfully processes Card Kingdom's full buylist
- **User Experience:** Clean, responsive interface
- **Developer Experience:** Stable development environment
- **Reliability:** Consistent performance across multiple test sessions

---

## Next Phase Considerations

### Potential Enhancements (To Be Prioritized)

1. **Data Persistence:** Database integration for permanent storage
2. **Advanced Analytics:** Data filtering, sorting, search capabilities
3. **Performance Optimization:** Caching, incremental updates
4. **Production Deployment:** Docker, cloud hosting, CI/CD
5. **Additional Data Sources:** Other card market APIs
6. **User Management:** Authentication, user preferences
7. **Real-time Updates:** WebSocket integration for live data
8. **Data Export:** CSV, Excel export functionality
9. **Visualization:** Charts, graphs, trend analysis
10. **API Documentation:** Swagger/OpenAPI integration

### Technical Debt to Address

1. **VS Code PowerShell Issue:** Root cause analysis and fix
2. **Error Handling:** More robust retry mechanisms
3. **Testing:** Automated test suite implementation
4. **Documentation:** API documentation and code comments
5. **Configuration Management:** Environment-based settings

---

## Lessons Learned

### What Worked Well

- FastAPI provided excellent async capabilities
- Pandas handled large datasets efficiently
- React + Material-UI created clean user interface
- Command Prompt terminals resolved stability issues
- Incremental development approach allowed for rapid iteration

### Challenges Overcome

- VS Code PowerShell terminal causing server shutdowns
- JSON serialization issues with numpy data types
- AsyncIO event loop management in FastAPI
- Large dataset processing without blocking
- Frontend-backend integration and CORS configuration

### Best Practices Established

- Use Command Prompt terminals in VS Code for Python servers
- Implement comprehensive logging for debugging
- Monitor memory usage during large data operations
- Use async processing for non-blocking operations
- Format large numbers for better user experience

---

## Conclusion

Phase 2 has successfully delivered a comprehensive dual-source data processing application. The system now supports both Card Kingdom API data and CSV file uploads with a unified processing architecture. The application demonstrates industrial-strength capabilities with excellent performance metrics, robust error handling, and a stable development environment.

**Key Achievements:**
- **Phase 1:** Card Kingdom API processing (140K+ records in 1.8 seconds)
- **Phase 2:** CSV/Excel upload functionality with smart filtering and validation
- **Architecture:** Unified processing core supporting both data sources
- **Performance:** Efficient memory management and real-time monitoring
- **Real-world Validation:** Successfully processed actual vendor data (24K records, 2.1MB Excel file)
- **Robust Error Handling:** Comprehensive JSON serialization for complex datasets with NaN values

The foundation is solid for the next phase: part matching and purchase optimization algorithms.

---

*Document prepared based on development session completed October 30, 2025*