import sqlite3
import json
import time
from datetime import datetime, timedelta
from typing import Any, Optional

_analytics_cache = {
    "cache_dict": {}
}
CACHE_TTL = 60

def get_analytics_summary(days: int = 30, org_id: Optional[str] = None) -> dict[str, Any]:
    from backend.main import DB_FILE
    global _analytics_cache
    now = time.time()
    
    cache_key = f"days_{days}_org_{org_id}"
    if 'cache_dict' not in _analytics_cache:
        _analytics_cache['cache_dict'] = {}
        
    cached_entry = _analytics_cache['cache_dict'].get(cache_key)
    if cached_entry and (now - cached_entry['timestamp']) < CACHE_TTL:
        return cached_entry['data']

    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    where_conditions = []
    params = []
    if days > 0:
        where_conditions.append("timestamp >= date('now', ?)")
        params.append(f"-{days} days")
    if org_id:
        where_conditions.append("org_id = ?")
        params.append(org_id)
        
    date_filter = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""
    query = f"SELECT * FROM migration_jobs {date_filter}"
    rows = cursor.execute(query, params).fetchall()
    
    total_migrations = len(rows)
    success_count = sum(1 for r in rows if r['status'] == 'SUCCESS' or r['status'] == 'SUCCESS_WITH_WARNINGS')
    partial_count = sum(1 for r in rows if r['status'] == 'PARTIAL')
    failure_count = sum(1 for r in rows if r['status'] == 'FAILED' or str(r['status']).startswith('FAILED:'))
    
    total_rows_migrated = sum((r['rows_migrated'] or 0) for r in rows)
    
    def parse_dur(d):
        if not d: return 0.0
        try:
            return float(str(d).replace('s', '').strip())
        except:
            return 0.0

    durations = [parse_dur(r['duration']) for r in rows if r['duration'] and parse_dur(r['duration']) > 0]
    avg_duration_seconds = sum(durations) / len(durations) if durations else 0.0
    
    # Compute overall rows per second
    valid_rps_jobs = [r for r in rows if r['duration'] and parse_dur(r['duration']) > 0 and (r['rows_migrated'] or 0) > 0]
    if valid_rps_jobs:
        avg_rows_per_second = sum((r['rows_migrated'] or 0) / parse_dur(r['duration']) for r in valid_rps_jobs) / len(valid_rps_jobs)
    else:
        avg_rows_per_second = 0.0

    sources = {}
    targets = {}
    dialect_pairs = {}
    migrations_by_day_dict = {}
    accuracy_scores = []
    
    for r in rows:
        src = r['source_db']
        tgt = r['target_db']
        sources[src] = sources.get(src, 0) + 1
        targets[tgt] = targets.get(tgt, 0) + 1
        
        pair = f"{src} -> {tgt}"
        if pair not in dialect_pairs:
            dialect_pairs[pair] = {'source': src, 'target': tgt, 'count': 0, 'duration_sum': 0.0, 'success_count': 0}
        dialect_pairs[pair]['count'] += 1
        dialect_pairs[pair]['duration_sum'] += parse_dur(r['duration'])
        if r['status'] == 'SUCCESS' or r['status'] == 'SUCCESS_WITH_WARNINGS':
            dialect_pairs[pair]['success_count'] += 1
            
        dt = r['timestamp'][:10] # YYYY-MM-DD
        if dt not in migrations_by_day_dict:
            migrations_by_day_dict[dt] = {'date': dt, 'count': 0, 'success': 0, 'failed': 0, 'partial': 0, 'rows': 0}
        migrations_by_day_dict[dt]['count'] += 1
        migrations_by_day_dict[dt]['rows'] += (r['rows_migrated'] or 0)
        if r['status'] == 'SUCCESS' or r['status'] == 'SUCCESS_WITH_WARNINGS':
            migrations_by_day_dict[dt]['success'] += 1
        elif r['status'] == 'PARTIAL':
            migrations_by_day_dict[dt]['partial'] += 1
        else:
            migrations_by_day_dict[dt]['failed'] += 1
            
        try:
            payload = json.loads(r['full_payload'])
            score = payload.get('validation_score')
            if score is not None:
                accuracy_scores.append(float(score))
        except:
            pass

    most_used_source = max(sources.items(), key=lambda x: x[1])[0] if sources else "N/A"
    most_used_target = max(targets.items(), key=lambda x: x[1])[0] if targets else "N/A"
    
    dialect_pair_list = []
    for p, d in dialect_pairs.items():
        dialect_pair_list.append({
            'source': d['source'],
            'target': d['target'],
            'count': d['count'],
            'avg_duration': d['duration_sum'] / d['count'] if d['count'] > 0 else 0,
            'success_rate': (d['success_count'] / d['count'] * 100.0) if d['count'] > 0 else 0
        })
        
    migrations_by_day = sorted(list(migrations_by_day_dict.values()), key=lambda x: x['date'])
    rows_migrated_by_day = [{'date': d['date'], 'rows': d['rows']} for d in migrations_by_day]
    
    # Fill in missing dates for the last N days for the chart
    if days > 0 and days <= 90:
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days-1)
        filled_migrations = []
        filled_rows = []
        
        curr = start_date
        date_map = {m['date']: m for m in migrations_by_day}
        while curr <= end_date:
            ds = curr.strftime("%Y-%m-%d")
            if ds in date_map:
                filled_migrations.append(date_map[ds])
                filled_rows.append({'date': ds, 'rows': date_map[ds]['rows']})
            else:
                filled_migrations.append({'date': ds, 'count': 0, 'success': 0, 'failed': 0, 'partial': 0, 'rows': 0})
                filled_rows.append({'date': ds, 'rows': 0})
            curr += timedelta(days=1)
        migrations_by_day = filled_migrations
        rows_migrated_by_day = filled_rows

    top_tables = sorted(rows, key=lambda x: x['rows_migrated'] or 0, reverse=True)[:10]
    top_tables_by_rows = []
    for t in top_tables:
        top_tables_by_rows.append({
            'job_id': t['id'],
            'source': t['source_db'],
            'target': t['target_db'],
            'rows': t['rows_migrated'] or 0,
            'duration': parse_dur(t['duration']),
            'status': t['status']
        })
        
    acc_dist = {"90-100": 0, "80-90": 0, "70-80": 0, "<70": 0}
    for s in accuracy_scores:
        if s >= 90: acc_dist["90-100"] += 1
        elif s >= 80: acc_dist["80-90"] += 1
        elif s >= 70: acc_dist["70-80"] += 1
        else: acc_dist["<70"] += 1
        
    accuracy_score_distribution = [{'range': k, 'count': v} for k, v in acc_dist.items()]
    avg_accuracy_score = sum(accuracy_scores) / len(accuracy_scores) if accuracy_scores else 0.0

    result = {
        "total_migrations": total_migrations,
        "success_rate": (success_count / total_migrations * 100.0) if total_migrations else 0.0,
        "partial_rate": (partial_count / total_migrations * 100.0) if total_migrations else 0.0,
        "failure_rate": (failure_count / total_migrations * 100.0) if total_migrations else 0.0,
        "total_rows_migrated": total_rows_migrated,
        "avg_rows_per_second": avg_rows_per_second,
        "avg_duration_seconds": avg_duration_seconds,
        "most_used_source": most_used_source,
        "most_used_target": most_used_target,
        "migrations_by_day": migrations_by_day,
        "migrations_by_dialect_pair": dialect_pair_list,
        "rows_migrated_by_day": rows_migrated_by_day,
        "top_tables_by_rows": top_tables_by_rows, 
        "accuracy_score_distribution": accuracy_score_distribution,
        "avg_accuracy_score": avg_accuracy_score
    }
    
    _analytics_cache['cache_dict'][cache_key] = {
        'timestamp': now,
        'data': result
    }
    
    return result
