import re
import hmac
import hashlib
import json
import sqlite3
import datetime
import asyncio
import httpx
import os

DB_FILE = os.environ.get("DB_PATH", os.path.abspath("migrations.db"))

async def deliver_webhook(webhook: dict, event_type: str, payload: dict) -> dict:
    """
    Sends an HTTP POST request to the webhook URL with HMAC-SHA256 signature.
    """
    url = webhook.get("url")
    secret = webhook.get("secret", "")
    webhook_id = webhook.get("id")

    body_data = {
        "event": event_type,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "payload": payload
    }
    raw_body = json.dumps(body_data)

    signature = hmac.new(
        secret.encode('utf-8'),
        raw_body.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    headers = {
        "Content-Type": "application/json",
        "X-Fluxline-Signature": f"sha256={signature}",
        "X-Fluxline-Event": event_type,
        "User-Agent": "Fluxline-Webhook-Dispatcher/1.0"
    }

    status_str = "FAILED"
    delivery_time = datetime.datetime.now(datetime.timezone.utc).isoformat()

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, content=raw_body, headers=headers)
            if resp.is_success:
                status_str = f"200 OK ({resp.status_code})"
            else:
                status_str = f"HTTP {resp.status_code}"
    except Exception as e:
        status_str = f"ERROR: {str(e)[:100]}"

    # Update SQLite database status
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE webhooks SET last_delivery = ?, last_status = ? WHERE id = ?",
            (delivery_time, status_str, webhook_id)
        )
        conn.commit()
        conn.close()
    except Exception as err:
        print(f"Failed to update webhook delivery status in DB: {err}")

    return {
        "webhook_id": webhook_id,
        "status": status_str,
        "delivered_at": delivery_time
    }

async def trigger_webhooks(org_id: str, event_type: str, payload: dict):
    """
    Queries active webhooks for org_id and delivers payload asynchronously.
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM webhooks WHERE enabled = 1 AND (org_id = ? OR org_id = 'default_org')",
            (org_id,)
        )
        rows = cursor.fetchall()
        conn.close()

        webhooks = [dict(r) for r in rows]
        
        # Filter webhooks that match event_type
        matching = []
        for wh in webhooks:
            events_str = wh.get("events", "*")
            if events_str == "*" or event_type in events_str.split(","):
                matching.append(wh)

        # Fire delivery tasks asynchronously without blocking main flow
        tasks = [deliver_webhook(wh, event_type, payload) for wh in matching]
        if tasks:
            asyncio.create_task(asyncio.gather(*tasks, return_exceptions=True))
    except Exception as e:
        print(f"Error triggering webhooks for event {event_type}: {e}")
