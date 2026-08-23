from backend.services.llm_service import LLMService
from structlog import get_logger

logger = get_logger()

SQL_PROMPT_TEMPLATE = """
You are an expert SQL Developer. 
Translate the following SQL code (stored procedure, view, function, or trigger) from {source_db} to {target_db}.
Use best practices and optimal functions for {target_db}.

For example, if translating MSSQL to PostgreSQL:
- ISNULL() becomes COALESCE()
- GETDATE() becomes CURRENT_TIMESTAMP or NOW()
- TOP N becomes LIMIT N

Source SQL:
{source_sql}

Output ONLY the raw SQL for the target database. Do not include markdown formatting or explanations.
"""


class SQLAgent:
    def __init__(self) -> None:
        self.llm = LLMService()

    async def translate_sql(self, source_db: str, target_db: str, source_sql: str) -> str:
        logger.info(f"SQLAgent translating SQL from {source_db} to {target_db}")
        prompt = SQL_PROMPT_TEMPLATE.format(
            source_db=source_db, target_db=target_db, source_sql=source_sql
        )
        result = await self.llm.generate_response(prompt)
        return result.replace("```sql", "").replace("```", "").strip()


sql_agent = SQLAgent()
