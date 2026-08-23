import os
import json
import re

def patch_transaction_manager():
    tm_path = r"backend\execution\transaction_manager.py"
    with open(tm_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Update __init__ to accept job_id
    if "def __init__(self, target_conn, db_type: str, group_tables: list[str]):" in content:
        content = content.replace(
            "def __init__(self, target_conn, db_type: str, group_tables: list[str]):",
            "def __init__(self, target_conn, db_type: str, group_tables: list[str], job_id: str = None):\n        self.job_id = job_id"
        )
    
    # Add index methods
    index_methods = """
    def _save_dropped_indexes(self, table: str, indexes: list[str]):
        if not self.job_id: return
        import sqlite3, json, os
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "migrations.db")
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT full_payload FROM migration_jobs WHERE id = ?", (self.job_id,))
        row = c.fetchone()
        if row and row[0]:
            payload = json.loads(row[0])
            if "dropped_indexes" not in payload:
                payload["dropped_indexes"] = {}
            if table not in payload["dropped_indexes"]:
                payload["dropped_indexes"][table] = []
            payload["dropped_indexes"][table].extend(indexes)
            c.execute("UPDATE migration_jobs SET full_payload = ? WHERE id = ?", (json.dumps(payload), self.job_id))
            conn.commit()
        conn.close()

    def _get_dropped_indexes(self, table: str) -> list[str]:
        if not self.job_id: return []
        import sqlite3, json, os
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "migrations.db")
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT full_payload FROM migration_jobs WHERE id = ?", (self.job_id,))
        row = c.fetchone()
        conn.close()
        if row and row[0]:
            payload = json.loads(row[0])
            return payload.get("dropped_indexes", {}).get(table, [])
        return []

    def _clear_dropped_indexes(self, table: str):
        if not self.job_id: return
        import sqlite3, json, os
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "migrations.db")
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT full_payload FROM migration_jobs WHERE id = ?", (self.job_id,))
        row = c.fetchone()
        if row and row[0]:
            payload = json.loads(row[0])
            if "dropped_indexes" in payload and table in payload["dropped_indexes"]:
                del payload["dropped_indexes"][table]
                c.execute("UPDATE migration_jobs SET full_payload = ? WHERE id = ?", (json.dumps(payload), self.job_id))
                conn.commit()
        conn.close()

    def disable_indexes_for_table(self, table: str, row_count: int):
        import os
        threshold = int(os.environ.get("DISABLE_INDEX_THRESHOLD", 100000))
        if row_count < threshold:
            return
        
        if self.db_type in ["postgres", "postgresql"]:
            try:
                self.cursor.execute(f"SELECT indexname, indexdef FROM pg_indexes WHERE tablename = '{table}' AND indexname NOT IN (SELECT conname FROM pg_constraint WHERE contype = 'p')")
                indexes = self.cursor.fetchall()
                if indexes:
                    defs = [idx[1] for idx in indexes]
                    self._save_dropped_indexes(table, defs)
                    for idx in indexes:
                        self.cursor.execute(f"DROP INDEX IF EXISTS {idx[0]}")
            except Exception as e:
                logger.warning(f"Failed to drop indexes for {table}: {e}")
        elif self.db_type == "mysql":
            try:
                self.cursor.execute(f"ALTER TABLE {table} DISABLE KEYS")
            except: pass
        elif self.db_type == "mssql":
            if not hasattr(self, "_use_tablock_cache"):
                self._use_tablock_cache = {}
            self._use_tablock_cache[table] = True

    def enable_indexes_for_table(self, table: str):
        if self.db_type in ["postgres", "postgresql"]:
            defs = self._get_dropped_indexes(table)
            for ddl in defs:
                try:
                    self.cursor.execute(ddl)
                except Exception as e:
                    logger.warning(f"Failed to recreate index {ddl}: {e}")
            self._clear_dropped_indexes(table)
        elif self.db_type == "mysql":
            try:
                self.cursor.execute(f"ALTER TABLE {table} ENABLE KEYS")
            except: pass
            
"""
    if "def disable_indexes_for_table" not in content:
        content = content.replace("def commit(self):", index_methods + "\n    def commit(self):")
        
    # patch mssql bulk insert
    if 'sql = f"INSERT INTO {table_name} ({cols_str}) VALUES ({placeholders})"' in content:
        content = content.replace(
            'sql = f"INSERT INTO {table_name} ({cols_str}) VALUES ({placeholders})"',
            'use_tablock = " WITH (TABLOCK)" if getattr(self, "_use_tablock_cache", {}).get(table_name) else ""\n            sql = f"INSERT INTO {table_name}{use_tablock} ({cols_str}) VALUES ({placeholders})"'
        )
        
    with open(tm_path, "w", encoding="utf-8") as f:
        f.write(content)


def patch_main_py():
    main_path = r"backend\main.py"
    with open(main_path, "r", encoding="utf-8") as f:
        content = f.read()

    replacement = """
        source_engine = get_engine(req.source)
        target_engine = get_engine(req.target)
        
        from backend.execution.transaction_manager import TransactionManager
        import time
        import os
        
        def get_chunk_size(row_count: int) -> int:
            if not row_count or row_count < 10000: return int(os.environ.get("CHUNK_SIZE_TIER1", 1000))
            if row_count < 100000: return int(os.environ.get("CHUNK_SIZE_TIER2", 10000))
            if row_count < 1000000: return int(os.environ.get("CHUNK_SIZE_TIER3", 50000))
            return int(os.environ.get("CHUNK_SIZE_TIER4", 100000))
            
        total_inserted = 0
        migrated_tables = set()
        
        cyclic_groups = resolution.circular_dependency_groups
        self_refs = resolution.self_referencing_tables
        
        groups_to_migrate = []
        for g in cyclic_groups:
            groups_to_migrate.append(g)
        for t in self_refs:
            if not any(t in g for g in cyclic_groups):
                groups_to_migrate.append([t])
                
        last_bcast = 0
        async def throttled_broadcast(payload):
            nonlocal last_bcast
            now = time.time()
            if payload.get("status") == "done" or (now - last_bcast) > 1.0:
                await broadcast_progress(payload)
                last_bcast = now
                
        # Phase 1: Sequential Cyclic Groups
        for group in groups_to_migrate:
            target_raw = get_raw_conn(req.target)
            tm = TransactionManager(target_raw, req.target.db_type, group, job_id=job_id)
            if not tm.check_privileges():
                tm.close()
                target_raw.close()
                raise RuntimeError(tm.get_missing_privilege_error(req.target.username))
                
            tm.begin_transaction()
            group_inserted = 0
            txn_start = time.time()
            try:
                tm.disable_constraints()
                for table_name in group:
                    table_schema_obj = next((t for t in source_schema["tables"] if t["name"] == table_name), None)
                    if not table_schema_obj: continue
                    
                    row_count = table_schema_obj.get("row_count", 0)
                    chunk_size = get_chunk_size(row_count)
                    await broadcast_progress({"step": "data", "status": "running", "table": table_name, "rows_done": 0, "rows_total": row_count})
                    
                    tm.disable_indexes_for_table(table_name, row_count)
                    
                    if hasattr(source_engine, "stream_table"):
                        if req.source.db_type.lower() == "mysql":
                            pk = table_schema_obj.get("primary_keys", ["id"])[0] if table_schema_obj.get("primary_keys") else table_schema_obj.get("columns", [{"name": "id"}])[0]["name"]
                            stream = source_engine.stream_table(table_name, pk, chunk_size=chunk_size)
                        else:
                            if req.source.db_type.lower() == "mssql":
                                stream = source_engine.stream_table(table_name, chunk_size=chunk_size, table_schema=table_schema_obj)
                            else:
                                stream = source_engine.stream_table(table_name, chunk_size=chunk_size)
                                
                        table_inserted = 0
                        for chunk in stream:
                            inserted = tm.bulk_insert_chunk(table_name, chunk)
                            actual_inserted = len(chunk) if inserted < 0 else inserted
                            table_inserted += actual_inserted
                            group_inserted += actual_inserted
                            await asyncio.sleep(0)
                            await throttled_broadcast({"step": "data", "status": "running", "table": table_name, "rows_done": table_inserted, "rows_total": row_count})
                            
                    tm.enable_indexes_for_table(table_name)
                    migrated_tables.add(table_name)
                
                tm.enable_constraints()
                violations = tm.validate_constraints()
                if violations:
                    raise RuntimeError(f"Constraint violations found: {violations}")
                tm.commit()
                total_inserted += group_inserted
                if time.time() - txn_start > 300:
                    print(f"WARNING: Transaction for group {group} took longer than 300 seconds.")
            except Exception as e:
                tm.rollback()
                for table_name in group:
                    tm.enable_indexes_for_table(table_name)
                raise RuntimeError(f"Transaction failed for group {group}: {e}")
            finally:
                tm.close()
                target_raw.close()

        # Phase 2: Parallel Independent Tables by Topological Generation
        MAX_PARALLEL_TABLES = int(os.environ.get("MAX_PARALLEL_TABLES", 4))
        semaphore = asyncio.Semaphore(MAX_PARALLEL_TABLES)
        
        def run_table_worker(table_name, row_count, table_schema_obj):
            worker_src = get_engine(req.source)
            worker_tgt_raw = get_raw_conn(req.target)
            tm = TransactionManager(worker_tgt_raw, req.target.db_type, [table_name], job_id=job_id)
            try:
                tm.begin_transaction()
                tm.disable_indexes_for_table(table_name, row_count)
                
                chunk_size = get_chunk_size(row_count)
                if hasattr(worker_src, "stream_table"):
                    if req.source.db_type.lower() == "mysql":
                        pk = table_schema_obj.get("primary_keys", ["id"])[0] if table_schema_obj.get("primary_keys") else table_schema_obj.get("columns", [{"name": "id"}])[0]["name"]
                        start_pk = None
                        try:
                            # best effort max pk logic
                            tr_cur = worker_tgt_raw.cursor()
                            tr_cur.execute(f"SELECT MAX({pk}) FROM {table_name}")
                            max_val = tr_cur.fetchone()
                            if max_val and max_val[0] is not None: start_pk = max_val[0]
                        except: pass
                        stream = worker_src.stream_table(table_name, pk, chunk_size=chunk_size, start_pk=start_pk)
                    else:
                        if req.source.db_type.lower() == "mssql":
                            stream = worker_src.stream_table(table_name, chunk_size=chunk_size, table_schema=table_schema_obj)
                        else:
                            stream = worker_src.stream_table(table_name, chunk_size=chunk_size)
                            
                    table_inserted = 0
                    for chunk in stream:
                        inserted = tm.bulk_insert_chunk(table_name, chunk)
                        actual_inserted = len(chunk) if inserted < 0 else inserted
                        table_inserted += actual_inserted
                        # We do not broadcast inside the thread to avoid event loop issues, we yield back
                        # Actually we can't await inside run_in_executor, so we just return the total at the end
                        
                tm.enable_indexes_for_table(table_name)
                tm.commit()
                return table_inserted
            except Exception as e:
                tm.rollback()
                tm.enable_indexes_for_table(table_name)
                raise e
            finally:
                tm.close()
                worker_tgt_raw.close()
                
        async def migrate_table_task(table_name):
            async with semaphore:
                table_schema_obj = next((t for t in source_schema.get("tables", []) if t["name"] == table_name), None)
                if not table_schema_obj: return 0
                row_count = table_schema_obj.get("row_count", 0)
                await broadcast_progress({"step": "data", "status": "running", "table": table_name, "rows_done": 0, "rows_total": row_count})
                
                table_inserted = await asyncio.to_thread(run_table_worker, table_name, row_count, table_schema_obj)
                
                await broadcast_progress({"step": "data", "status": "running", "table": table_name, "rows_done": table_inserted, "rows_total": row_count})
                return table_inserted
                
        for generation in getattr(resolution, "migration_generations", []):
            gen_tasks = []
            for table_name in generation:
                if table_name not in migrated_tables:
                    gen_tasks.append(migrate_table_task(table_name))
                    migrated_tables.add(table_name)
            
            if gen_tasks:
                results = await asyncio.gather(*gen_tasks, return_exceptions=False)
                total_inserted += sum(results)
                
        # Also catch any tables missing from the generation graph just in case
        fallback_tasks = []
        for table in source_schema.get("tables", []):
            if table["name"] not in migrated_tables:
                fallback_tasks.append(migrate_table_task(table["name"]))
                migrated_tables.add(table["name"])
        if fallback_tasks:
            results = await asyncio.gather(*fallback_tasks, return_exceptions=False)
            total_inserted += sum(results)

        duration = time.time() - start_time"""
        
    start_str = "source_engine = get_engine(req.source)"
    end_str = "duration = time.time() - start_time"
    
    s_idx = content.find(start_str)
    e_idx = content.find(end_str)
    if s_idx != -1 and e_idx != -1:
        e_idx += len(end_str)
        content = content[:s_idx] + replacement.strip() + content[e_idx:]
        
        with open(main_path, "w", encoding="utf-8") as f:
            f.write(content)
            
if __name__ == "__main__":
    patch_transaction_manager()
    patch_main_py()
    print("Patched successfully")
