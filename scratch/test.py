import re
def strip(sql_text):
    sql_text = re.sub(r'[^]+\s*\.\s*([^]+)', r'\1', sql_text)
    sql_text = re.sub(r'[^]+\s*\.\s*', '', sql_text)
    sql_text = re.sub(r'\b[a-zA-Z_][a-zA-Z0-9_]*\s*\.\s*(?=[a-zA-Z_][a-zA-Z0-9_]*)', '', sql_text)
    return sql_text
print(strip('select db.customers.id AS id from db.customers c left join db.orders o on (c.id = o.customer_id) where (db.customers.is_active = true)'))
