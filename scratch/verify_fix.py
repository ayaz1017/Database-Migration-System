import sqlite3, json

DB_FILE = 'migrations.db'
JOB_ID = 'mig_1782888879177'

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

cursor.execute("SELECT full_payload FROM migration_jobs WHERE id = ?", (JOB_ID,))
row = cursor.fetchone()
payload = json.loads(row[0])

translations = payload['object_translations']

print("=== Verification: checking for ecom_sample in all translated_definitions ===\n")
all_clean = True
for t in translations:
    name = t['object_name']
    td = t.get('translated_definition', '')
    has_prefix = 'ecom_sample' in td
    if has_prefix:
        # Check if it's only in a comment
        lines = td.split('\n')
        in_sql = any('ecom_sample' in line for line in lines if not line.strip().startswith('--'))
        status = "STILL HAS ecom_sample IN SQL!" if in_sql else "only in comment (OK)"
        if in_sql:
            all_clean = False
    else:
        status = "CLEAN"
    print(f"  {name}: {status}")

print(f"\nAll objects clean: {all_clean}")

# Show the v_product_sales_stats translated_definition
print("\n--- v_product_sales_stats translated_definition ---")
for t in translations:
    if t['object_name'] == 'v_product_sales_stats':
        print(t['translated_definition'])

# Show v_customer_order_summary too
print("\n--- v_customer_order_summary translated_definition ---")
for t in translations:
    if t['object_name'] == 'v_customer_order_summary':
        print(t['translated_definition'])

conn.close()
