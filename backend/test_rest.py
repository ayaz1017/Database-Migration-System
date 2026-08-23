import json
import os
import urllib.request

from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get("GOOGLE_API_KEY")
MODEL = "gemini-2.0-flash"

url = (
    f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"
)

payload = {
    "contents": [
        {
            "parts": [
                {
                    "text": """
You are an expert database migration engineer. Your task is to translate a database object from mssql to postgres.

Object Type: trigger
Object Name: before_insert_order_items

Source Definition:
CREATE TRIGGER before_insert_order_items
ON order_items
FOR INSERT
AS
BEGIN
    UPDATE order_items
    SET created_at = GETDATE()
    FROM inserted
    WHERE order_items.id = inserted.id;
END;

Output ONLY the translated SQL/DDL statement(s). Do not include markdown blocks like ```sql or ``` or any explanations outside the code.
"""
                }
            ]
        }
    ],
    "generationConfig": {
        "temperature": 0.1,
        "maxOutputTokens": 4096,
    },
}

req = urllib.request.Request(
    url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}
)

print(f"Calling Gemini API (Model: {MODEL})...")
try:
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode("utf-8"))
        print("--- RAW API JSON RESPONSE ---")
        print(json.dumps(result, indent=2))
except urllib.error.HTTPError as e:
    print(f"HTTP Error {e.code}: {e.read().decode('utf-8')}")
except Exception as e:
    print(f"Error: {e}")
