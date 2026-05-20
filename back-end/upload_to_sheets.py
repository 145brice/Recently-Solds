import gspread
from oauth2client.service_account import ServiceAccountCredentials
import csv

# Authenticate
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

# Open the sheet (use the ID from your URL: 1ms790piO6FOTULEii39DFTqUHXvo27okePbuSqoinyk)
sheet = client.open_by_key("1ms790piO6FOTULEii39DFTqUHXvo27okePbuSqoinyk").sheet1

# Read CSV and append rows
with open("nashville_cash_leads_clean.csv", "r") as f:
    reader = csv.reader(f)
    next(reader)  # Skip header if needed
    for row in reader:
        sheet.append_row(row)

print("Uploaded to Google Sheets!")