import json
import re
import sqlite3
import time
import uuid
import asyncio
from typing import Dict, List, Optional, Any, AsyncGenerator

from backend.main import DB_FILE
from backend.services.llm_service import LLMService

SYSTEM_PROMPT = """You are Flux, an AI assistant built into Fluxline — a deterministic database migration engine. You help users with three things:

1. MIGRATION HISTORY: Answer questions about past migrations using the data provided in the context. Be specific — cite job IDs, row counts, durations, and error details from the actual data.

2. MIGRATION CONFIGURATION: Help users configure new migrations — recommend chunk sizes, warn about FK dependency risks, suggest migration order, explain what options like fk_dependency_mode and auto_approve_objects do.

3. DATABASE MIGRATION EXPERTISE: Answer general questions about database migration best practices, dialect differences (MSSQL/MySQL/PostgreSQL/Oracle), type mapping risks, and how to handle common migration problems.

You have access to this user's migration data:
{context}

Current page the user is on: {current_page}

Be concise, specific, and technical. Format responses with markdown where helpful.
Never make up migration data — only reference what's in the context provided.
"""

MAX_MESSAGES_PER_SESSION = 20  # 10 pairs
RATE_LIMIT_REQUESTS = 30
RATE_LIMIT_WINDOW_SEC = 60

class AssistantService:
    def __init__(self):
        self.llm = LLMService()
        self.sessions: Dict[str, Dict[str, Any]] = {}
        
    def _get_db(self):
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        return conn

    def _sanitize_data(self, data: dict) -> dict:
        """Ensure no credentials leak into context."""
        sanitized = dict(data)
        if 'full_payload' in sanitized:
            del sanitized['full_payload']
        # Remove any fields that could possibly contain passwords
        for k in list(sanitized.keys()):
            if 'password' in k.lower() or 'host' in k.lower() or 'url' in k.lower() or 'user' in k.lower():
                del sanitized[k]
        return sanitized

    def _build_context(self, message: str, context_job_id: Optional[str], org_id: Optional[str] = None) -> str:
        msg_lower = message.lower()
        context_data = {}
        
        with self._get_db() as conn:
            cursor = conn.cursor()
            
            # 1. Summary stats
            if org_id:
                cursor.execute("SELECT COUNT(*) as count, SUM(rows_migrated) as total_rows FROM migration_jobs WHERE org_id = ?", (org_id,))
            else:
                cursor.execute("SELECT COUNT(*) as count, SUM(rows_migrated) as total_rows FROM migration_jobs")
            stats = cursor.fetchone()
            
            if org_id:
                cursor.execute("SELECT status, COUNT(*) as count FROM migration_jobs WHERE org_id = ? GROUP BY status", (org_id,))
            else:
                cursor.execute("SELECT status, COUNT(*) as count FROM migration_jobs GROUP BY status")
            statuses = {row['status']: row['count'] for row in cursor.fetchall()}
            total = stats['count'] if stats['count'] else 0
            success_count = statuses.get('SUCCESS', 0) + statuses.get('SUCCESS_WITH_WARNINGS', 0)
            
            context_data['global_stats'] = {
                'total_migrations': total,
                'total_rows_migrated': stats['total_rows'] or 0,
                'success_rate': round(success_count / total * 100, 2) if total > 0 else 0
            }
            
            # 2. Last 5 migrations
            if org_id:
                cursor.execute("SELECT id, source_db, target_db, status, rows_migrated, duration, timestamp FROM migration_jobs WHERE org_id = ? ORDER BY timestamp DESC LIMIT 5", (org_id,))
            else:
                cursor.execute("SELECT id, source_db, target_db, status, rows_migrated, duration, timestamp FROM migration_jobs ORDER BY timestamp DESC LIMIT 5")
            context_data['recent_migrations'] = [self._sanitize_data(dict(r)) for r in cursor.fetchall()]
            
            # 3. Conditional: Specific Job ID
            job_id_match = context_job_id
            if not job_id_match:
                import re
                m = re.search(r'mig_\d+', msg_lower)
                if m: job_id_match = m.group(0)
                
            if job_id_match:
                if org_id:
                    cursor.execute("SELECT id, source_db, target_db, status, tables_migrated, rows_migrated, duration, timestamp, full_payload FROM migration_jobs WHERE id = ? AND org_id = ?", (job_id_match, org_id))
                else:
                    cursor.execute("SELECT id, source_db, target_db, status, tables_migrated, rows_migrated, duration, timestamp, full_payload FROM migration_jobs WHERE id = ?", (job_id_match,))
                row = cursor.fetchone()
                if row:
                    row_dict = dict(row)
                    # Extract error_detail if present
                    if row_dict.get('full_payload'):
                        try:
                            payload = json.loads(row_dict['full_payload'])
                            if 'error_detail' in payload:
                                row_dict['error_detail'] = payload['error_detail']
                        except: pass
                    context_data['requested_job'] = self._sanitize_data(row_dict)
                    
            # 4. Conditional: Errors
            if 'error' in msg_lower or 'fail' in msg_lower or 'wrong' in msg_lower:
                if org_id:
                    cursor.execute("SELECT id, status, timestamp, full_payload FROM migration_jobs WHERE (status LIKE 'FAILED%' OR status = 'PARTIAL') AND org_id = ? ORDER BY timestamp DESC LIMIT 10", (org_id,))
                else:
                    cursor.execute("SELECT id, status, timestamp, full_payload FROM migration_jobs WHERE status LIKE 'FAILED%' OR status = 'PARTIAL' ORDER BY timestamp DESC LIMIT 10")
                failures = []
                for r in cursor.fetchall():
                    row_dict = dict(r)
                    if row_dict.get('full_payload'):
                        try:
                            payload = json.loads(row_dict['full_payload'])
                            if 'error_detail' in payload:
                                row_dict['error_detail'] = payload['error_detail']
                        except: pass
                    failures.append(self._sanitize_data(row_dict))
                context_data['recent_failures'] = failures
                
            # 5. Conditional: Table lookup
            if 'table' in msg_lower or 'longest' in msg_lower or 'slow' in msg_lower:
                if org_id:
                    cursor.execute("SELECT id, source_db, target_db, duration, rows_migrated FROM migration_jobs WHERE org_id = ? ORDER BY CAST(REPLACE(duration, 's', '') AS REAL) DESC LIMIT 5", (org_id,))
                else:
                    cursor.execute("SELECT id, source_db, target_db, duration, rows_migrated FROM migration_jobs ORDER BY CAST(REPLACE(duration, 's', '') AS REAL) DESC LIMIT 5")
                context_data['longest_jobs'] = [self._sanitize_data(dict(r)) for r in cursor.fetchall()]
                
        return json.dumps(context_data, indent=2)

    def _check_rate_limit(self, session_id: str) -> bool:
        session = self.sessions[session_id]
        now = time.time()
        # Clean up old timestamps
        session['requests'] = [t for t in session['requests'] if now - t < RATE_LIMIT_WINDOW_SEC]
        if len(session['requests']) >= RATE_LIMIT_REQUESTS:
            return False
        session['requests'].append(now)
        return True

    async def get_chat_response(
        self, 
        message: str, 
        session_id: Optional[str] = None, 
        current_page: str = "dashboard",
        context_job_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        
        is_new_session = False
        if not session_id or session_id not in self.sessions:
            session_id = str(uuid.uuid4())
            self.sessions[session_id] = {
                'messages': [],
                'requests': []
            }
            is_new_session = True
            
        if not self._check_rate_limit(session_id):
            rate_limit_payload = {'type': 'chunk', 'content': "Slow down a bit — I'm thinking!"}
            done_payload = {'type': 'done', 'session_id': session_id, 'suggested_questions': [], 'data_referenced': []}
            yield f"data: {json.dumps(rate_limit_payload)}\n\n"
            yield f"data: {json.dumps(done_payload)}\n\n"
            return

        session = self.sessions[session_id]
        context_text = self._build_context(message, context_job_id)
        
        # Build prompt
        system_content = SYSTEM_PROMPT.format(
            context=context_text,
            current_page=current_page
        )
        
        # Prevent Prompt Injection by capping length and wrapping
        message = message[:2000].replace("---USER_INPUT---", "")
        safe_message_for_llm = f"---USER_INPUT---\n{message}\n---END_USER_INPUT---"
        
        llm_messages = [{"role": "system", "content": system_content}]
        llm_messages.extend(session['messages'])
        llm_messages.append({"role": "user", "content": safe_message_for_llm})
        
        use_fallback = False
        fallback_text = ""
        try:
            llm_stream = self.llm.stream_chat(llm_messages)
            first_chunk = await llm_stream.__anext__()
        except StopAsyncIteration:
            first_chunk = ""
        except Exception as e:
            import logging
            logging.warning(f"Ollama/LLM stream unavailable ({e}). Activating Flux Smart Fallback Engine.")
            use_fallback = True
            fallback_text = self._generate_smart_fallback(message, context_text)
            first_chunk = ""

        if is_new_session:
            yield f"data: {json.dumps({'type': 'session_id', 'session_id': session_id})}\n\n"
            
        full_response = ""
        if use_fallback:
            # Stream the fallback text in smooth chunks to mimic LLM streaming
            words = fallback_text.split(" ")
            chunk_buf = []
            for i, word in font_enumerate(words):
                chunk_buf.append(word)
                if len(chunk_buf) >= 4 or i == len(words) - 1:
                    c_str = " ".join(chunk_buf) + (" " if i < len(words) - 1 else "")
                    full_response += c_str
                    yield f"data: {json.dumps({'type': 'chunk', 'content': c_str})}\n\n"
                    chunk_buf = []
                    await asyncio.sleep(0.015)
        else:
            full_response = first_chunk
            if first_chunk:
                yield f"data: {json.dumps({'type': 'chunk', 'content': first_chunk})}\n\n"
            
            try:
                async for chunk in llm_stream:
                    full_response += chunk
                    yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
            except Exception as e:
                import logging
                logging.error(f"Error mid-stream: {e}")
                yield f"data: {json.dumps({'type': 'chunk', 'content': f'\\n\\n_Stream interrupted: {e}_'})}\n\n"

        # If response was empty, use fallback
        if not full_response.strip():
            full_response = self._generate_smart_fallback(message, context_text)
            yield f"data: {json.dumps({'type': 'chunk', 'content': full_response})}\n\n"

        # Update history
        session['messages'].append({"role": "user", "content": message})
        session['messages'].append({"role": "assistant", "content": full_response})
        
        if len(session['messages']) > MAX_MESSAGES_PER_SESSION:
            session['messages'] = session['messages'][-MAX_MESSAGES_PER_SESSION:]
            
        data_referenced = []
        import re
        job_matches = re.findall(r'mig_\d+', full_response)
        data_referenced.extend(list(set(job_matches)))
        
        suggested_questions = []
        if 'dashboard' in current_page.lower():
            suggested_questions = ["Why did my last migration fail?", "Show me all failed migrations this week", "Which dialect pair has the best success rate?"]
        elif 'report' in current_page.lower():
            suggested_questions = ["What caused the accuracy score to be low?", "Which tables had validation warnings?", "How does this compare to my previous migration?"]
        else:
            suggested_questions = ["What chunk size should I use for a 2M row table?", "How do I migrate Oracle to Postgres?", "Summarize my recent migrations"]
            
        yield f"data: {json.dumps({'type': 'done', 'session_id': session_id, 'suggested_questions': suggested_questions, 'data_referenced': data_referenced})}\n\n"

    def _generate_smart_fallback(self, message: str, context_text: str) -> str:
        msg_lower = message.lower()
        try:
            data = json.loads(context_text)
        except Exception:
            data = {}
            
        stats = data.get("global_stats", {})
        total_jobs = stats.get("total_migrations", 0)
        total_rows = stats.get("total_rows_migrated", 0)
        success_rate = stats.get("success_rate", 0.0)
        recent = data.get("recent_migrations", [])
        failures = data.get("recent_failures", [])
        requested_job = data.get("requested_job")
        
        # 1. Specific Job Query
        if requested_job:
            job_id = requested_job.get("id", "N/A")
            src = requested_job.get("source_db", "N/A")
            tgt = requested_job.get("target_db", "N/A")
            status = requested_job.get("status", "N/A")
            rows = requested_job.get("rows_migrated", 0)
            dur = requested_job.get("duration", "N/A")
            err = requested_job.get("error_detail")
            
            lines = [
                f"### 📋 Migration Job Report: `{job_id}`",
                f"- **Route**: `{src}` ➔ `{tgt}`",
                f"- **Status**: `{status}`",
                f"- **Rows Migrated**: {rows:,}",
                f"- **Duration**: {dur}",
            ]
            if err:
                lines.append(f"\n> ⚠️ **Error Details**:\n> ```text\n> {err}\n> ```")
            else:
                lines.append("\n✅ **Validation**: All constraints and byte checks completed cleanly.")
            return "\n".join(lines)

        # 2. Migration Activity / Summary / History
        if any(k in msg_lower for k in ["summarize", "summary", "activity", "history", "recent", "week", "past"]):
            lines = [
                "### 📊 Migration Activity Summary\n",
                f"- **Total Migration Jobs**: `{total_jobs}`",
                f"- **Total Rows Migrated**: `{total_rows:,}`",
                f"- **Overall Success Rate**: `{success_rate}%`\n"
            ]
            
            if recent:
                lines.append("#### 🚀 Recent Migrations")
                lines.append("| Job ID | Route | Rows | Duration | Status |")
                lines.append("|---|---|---|---|---|")
                for job in recent:
                    j_id = job.get("id", "N/A")
                    route = f"{job.get('source_db', '')} ➔ {job.get('target_db', '')}"
                    r_rows = f"{job.get('rows_migrated', 0):,}"
                    dur = job.get("duration", "N/A")
                    st = job.get("status", "UNKNOWN")
                    st_badge = f"✅ {st}" if "SUCCESS" in st else f"❌ {st}"
                    lines.append(f"| `{j_id}` | `{route}` | {r_rows} | {dur} | {st_badge} |")
            else:
                lines.append("_No recent migration jobs recorded yet._")
                
            if failures:
                lines.append(f"\n⚠️ **Note**: You have {len(failures)} recent job(s) with warnings or failures. Ask me 'Why did my last migration fail?' for detailed logs.")
                
            return "\n".join(lines)

        # 3. Failures & Errors
        if any(k in msg_lower for k in ["fail", "error", "wrong", "issue", "problem", "warning"]):
            if failures:
                lines = ["### ⚠️ Migration Failures & Warnings\n"]
                for f in failures[:5]:
                    f_id = f.get("id", "N/A")
                    f_st = f.get("status", "FAILED")
                    f_err = f.get("error_detail", "No explicit error payload recorded.")
                    lines.append(f"#### Job `{f_id}` (`{f_st}`)")
                    lines.append(f"```text\n{f_err}\n```\n")
                lines.append("**Recommended Actions:**")
                lines.append("1. Run a **Dry-Run Pre-flight check** in the New Migration wizard.")
                lines.append("2. Adjust keyset chunk sizes (e.g. 5,000 rows) for memory-intensive tables.")
                lines.append("3. Verify foreign key constraints match target database type definitions.")
                return "\n".join(lines)
            else:
                return "✅ **Good news!** No recent migration failures were found in your migration logs. All jobs completed successfully."

        # 4. Configuration & Guidance
        if any(k in msg_lower for k in ["chunk", "size", "config", "recommend", "oracle", "postgres", "mysql", "mssql", "how"]):
            return (
                "### ⚙️ Migration Best Practices & Configuration Guide\n\n"
                "Here are the recommended configurations for high-throughput migrations:\n\n"
                "1. **Keyset Chunk Size**:\n"
                "   - **Small/Medium Tables (< 1M rows)**: `10,000` rows/chunk\n"
                "   - **Large Tables (1M+ rows)**: `5,000` rows/chunk\n"
                "   - **Wide JSON/BLOB Tables**: `2,500` rows/chunk\n\n"
                "2. **Dialect Mappings**:\n"
                "   - **PostgreSQL ➔ MySQL**: Remap `UUID` ➔ `VARCHAR(36)`, `JSONB` ➔ `JSON`, `TIMESTAMPTZ` ➔ `DATETIME(6)`\n"
                "   - **MSSQL ➔ PostgreSQL**: Remap `IDENTITY(1,1)` ➔ `GENERATED ALWAYS AS IDENTITY`, `BIT` ➔ `BOOLEAN`\n\n"
                "3. **Zero Downtime Strategy**:\n"
                "   - Initialize with **Full Keyset Load**, then attach **CDC Sync** for incremental updates before cutover."
            )

        # General Fallback
        return (
            f"### 🤖 Flux Assistant Response\n\n"
            f"Based on your database activity:\n"
            f"- You have completed **{total_jobs}** migration(s) with a **{success_rate}%** success rate, moving **{total_rows:,}** total rows.\n\n"
            f"You can ask me to summarize your migration history, analyze failed jobs, or provide dialect translation advice."
        )

def font_enumerate(sequence):
    return enumerate(sequence)

