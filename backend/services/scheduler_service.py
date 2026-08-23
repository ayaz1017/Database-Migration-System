import sqlite3
import json
import uuid
import datetime
import os
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

DB_FILE = os.environ.get("DB_PATH", os.path.abspath("migrations.db"))

scheduler = AsyncIOScheduler()

def start_scheduler():
    if not scheduler.running:
        scheduler.start()
        print("APScheduler started successfully.")

def shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        print("APScheduler shut down successfully.")

async def run_scheduled_migration(schedule_id: str):
    """
    Executes a scheduled migration job and updates schedule metadata in DB.
    """
    print(f"[Scheduler] Executing scheduled migration for schedule_id: {schedule_id}")
    run_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
    status = "SUCCESS"
    
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM scheduled_migrations WHERE id = ?", (schedule_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            print(f"[Scheduler] Schedule {schedule_id} not found in DB.")
            return

        schedule = dict(row)
        if not schedule.get("enabled", 1):
            conn.close()
            print(f"[Scheduler] Schedule {schedule_id} is disabled. Skipping.")
            return

        # Prepare MigrationRequest
        from backend.main import run_migration_pipeline, MigrationRequest
        from backend.models import MigrationOptions

        selected_tables = json.loads(schedule.get("selected_tables") or "[]")
        apply_masking = bool(schedule.get("apply_masking", 0))

        req = MigrationRequest(
            source_db_type=schedule.get("source_db_type"),
            source_connection=schedule.get("source_connection"),
            target_db_type=schedule.get("target_db_type"),
            target_connection=schedule.get("target_connection"),
            options=MigrationOptions(
                selected_tables=selected_tables,
                apply_masking=apply_masking
            )
        )

        job_id = f"sched_{uuid.uuid4().hex[:10]}"
        
        # Execute migration pipeline in async background task
        await run_migration_pipeline(req, job_id, org_id="default_org")

    except Exception as e:
        status = "FAILED"
        print(f"[Scheduler] Error executing scheduled migration {schedule_id}: {e}")

    finally:
        # Update schedule stats in DB
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            if status == "SUCCESS":
                cursor.execute("""
                    UPDATE scheduled_migrations 
                    SET last_run_at = ?, run_count = run_count + 1 
                    WHERE id = ?
                """, (run_time, schedule_id))
            else:
                cursor.execute("""
                    UPDATE scheduled_migrations 
                    SET last_run_at = ?, run_count = run_count + 1, failure_count = failure_count + 1 
                    WHERE id = ?
                """, (run_time, schedule_id))
            conn.commit()
            conn.close()
        except Exception as update_err:
            print(f"[Scheduler] Error updating schedule stats in DB: {update_err}")

def add_schedule_to_apscheduler(schedule: dict):
    schedule_id = schedule.get("id")
    schedule_type = schedule.get("schedule_type")
    
    # Remove existing job if already in scheduler
    if scheduler.get_job(schedule_id):
        scheduler.remove_job(schedule_id)

    if not schedule.get("enabled", 1):
        return

    try:
        if schedule_type == "cron":
            cron_expr = schedule.get("cron_expression")
            if cron_expr:
                trigger = CronTrigger.from_crontab(cron_expr)
                scheduler.add_job(
                    run_scheduled_migration,
                    trigger=trigger,
                    id=schedule_id,
                    args=[schedule_id],
                    replace_existing=True
                )
        elif schedule_type == "interval":
            interval_sec = int(schedule.get("interval_seconds", 3600))
            trigger = IntervalTrigger(seconds=interval_sec)
            scheduler.add_job(
                run_scheduled_migration,
                trigger=trigger,
                id=schedule_id,
                args=[schedule_id],
                replace_existing=True
            )
    except Exception as e:
        print(f"[Scheduler] Failed to add schedule job {schedule_id}: {e}")

def remove_schedule_from_apscheduler(schedule_id: str):
    if scheduler.get_job(schedule_id):
        scheduler.remove_job(schedule_id)

def reload_schedules_from_db():
    """
    Loads all active schedules from SQLite and registers them with APScheduler.
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM scheduled_migrations WHERE enabled = 1")
        rows = cursor.fetchall()
        conn.close()

        count = 0
        for r in rows:
            schedule = dict(r)
            add_schedule_to_apscheduler(schedule)
            count += 1
        print(f"[Scheduler] Loaded {count} scheduled migration jobs from database.")
    except Exception as e:
        print(f"[Scheduler] Error reloading schedules from DB: {e}")
