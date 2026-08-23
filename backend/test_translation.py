import asyncio

from dotenv import load_dotenv

load_dotenv()

from backend.agents.object_translation_agent import ObjectTranslationAgent
from backend.models import MigratableObject


async def test():
    trigger_obj = MigratableObject(
        name="before_insert_order_items",
        object_type="trigger",
        complexity_estimate="low",
        source_definition="""
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
        """,
    )

    agent = ObjectTranslationAgent()
    print("Testing translation of a Trigger...")
    result = await agent.translate_procedure_or_trigger(trigger_obj, "mssql", "postgres")

    print("\n--- Final TranslationResult ---")
    print(f"Success: {result.translated_definition is not None}")
    print(f"Error: {result.translation_error}")
    print(f"Translated Definition snippet: {str(result.translated_definition)[:100]}")


asyncio.run(test())
