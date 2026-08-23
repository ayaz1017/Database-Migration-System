import sqlite3
import json

DB_FILE = "migrations.db"

def fix_translations():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, full_payload FROM migration_jobs")
    rows = cursor.fetchall()
    
    objects_to_fix = {
        "v_product_sales_stats",
        "CreateOrder",
        "UpdateProductPrice",
        "before_insert_order_items",
        "after_insert_order_items"
    }

    for job_id, payload_str in rows:
        if not payload_str:
            continue
            
        payload = json.loads(payload_str)
        translations = payload.get("object_translations", [])
        
        updated = False
        for obj in translations:
            if obj.get("object_name") in objects_to_fix and obj.get("needs_human_review"):
                translated_def = obj.get("translated_definition", "")
                if "ecom_sample." in translated_def:
                    new_def = translated_def.replace("ecom_sample.", "")
                    obj["translated_definition"] = new_def
                    print(f"Fixed {obj['object_name']} in job {job_id}")
                    updated = True
        
        if updated:
            cursor.execute("UPDATE migration_jobs SET full_payload = ? WHERE id = ?", (json.dumps(payload), job_id))
            print(f"Updated job {job_id}")
            
    conn.commit()
    conn.close()

if __name__ == "__main__":
    fix_translations()
