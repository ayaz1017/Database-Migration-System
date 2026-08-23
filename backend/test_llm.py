import asyncio
import os

from dotenv import load_dotenv

load_dotenv()

from openai import AsyncOpenAI


async def test():
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))

    prompt = """
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
    print(f"Using model: {model}")
    print("Calling API...")
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=4096,
        )
        print("--- RAW RESPONSE ---")
        print(repr(response))
        print("--- CONTENT ---")
        print(response.choices[0].message.content)
    except Exception as e:
        print(f"Exception: {e}")


asyncio.run(test())
