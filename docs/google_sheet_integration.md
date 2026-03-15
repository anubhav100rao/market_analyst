Google Sheets Integration — Export Analysis Results
Integrate the Market Analyst workflow with Google Sheets to automatically populate analysis results into the user's spreadsheet.

Target Sheet: Google Sheet

User Setup Required (Before Code Runs)
IMPORTANT

You need to create a Google Cloud Service Account and share the spreadsheet with it. Follow these steps once:

Step 1: Create a GCP Service Account
Go to Google Cloud Console
Create a new project (or use an existing one)
Enable Google Sheets API and Google Drive API:
Go to APIs & Services → Library
Search for "Google Sheets API" → Enable
Search for "Google Drive API" → Enable
Go to APIs & Services → Credentials → Create Credentials → Service Account
Name it (e.g. market-analyst-sheets)
Click Done (no roles needed at this step)
Step 2: Download the JSON Key
Click on the newly created service account
Go to the Keys tab → Add Key → Create new key → JSON
Download the JSON file
Save it as credentials/google_sheets_creds.json in the project root
Step 3: Share the Google Sheet
Open the service account JSON file — find the client_email field (looks like xyz@project.iam.gserviceaccount.com)
Open your Google Sheet
Click Share → paste the service account email → give Editor access
Step 4: Update 
.env
GOOGLE_SHEETS_CREDS_FILE=credentials/google_sheets_creds.json
GOOGLE_SHEETS_SPREADSHEET_ID=1NOoxP4gPv_4fsE8u6VD55UeL2D6lzJz3GwDbvdT6jIA
Proposed Changes
Google Sheets Tool
[NEW] 
google_sheets_tool.py
A GoogleSheetsTool class using gspread + service account auth:

export_analysis() — writes full analysis results as a new row
export_comparison() — writes comparison as side-by-side rows
Headers: Timestamp, Stock, Fundamental Score, Technical Score, Sentiment Score, Trend, Recommendation, Reasoning
Workflow Integration
[MODIFY] 
market_graph.py
Add a new sheets_export_node after the aggregator:

Graph becomes: intent → [fundamental, technical, sentiment] → aggregator → sheets_export → END
Node reads the final state and calls GoogleSheetsTool.export_analysis()
Export is best-effort — if it fails, the analysis still returns normally
API Integration
[MODIFY] 
fastapi_server.py
No changes needed — the sheets export happens inside the graph, so all endpoints automatically export.

Tests
[NEW] 
test_google_sheets.py
Mocked tests (no real Google API calls):

Test export_analysis with mocked gspread client
Test export_comparison with mocked gspread client
Test graceful failure when credentials missing
Test sheet header creation
Dependencies & Config
[MODIFY] 
requirements.txt
Add: gspread, google-auth

[MODIFY] 
config.py
Add: GOOGLE_SHEETS_CREDS_FILE, GOOGLE_SHEETS_SPREADSHEET_ID env vars

[MODIFY] 
.gitignore
Add: credentials/ directory

Verification Plan
Automated Tests
bash
source venv/bin/activate && python -m pytest tests/ -v
All tests must pass, including the new test_google_sheets.py (fully mocked).

Manual Verification
After completing the user setup steps above:

Start the backend: uvicorn backend.api.fastapi_server:app --port 8000
Start the frontend: streamlit run frontend/streamlit_app.py
Run a single stock analysis from the Streamlit UI
Check the Google Sheet — a new row should appear with the analysis data
