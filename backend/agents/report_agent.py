from structlog import get_logger

logger = get_logger()


class ReportAgent:
    def __init__(self) -> None:
        pass

    def generate_markdown_report(
        self, job_id: str, summary: dict, tables: list, errors: list
    ) -> str:
        logger.info(f"ReportAgent generating markdown for job {job_id}")

        md = f"# Migration Report: Job {job_id}\n\n"
        md += "## Summary\n"
        md += f"- Status: {summary.get('status', 'Unknown')}\n"
        md += f"- Duration: {summary.get('duration', '0s')}\n"
        md += f"- Total Tables Migrated: {len(tables)}\n\n"

        md += "## Table Details\n"
        for t in tables:
            md += f"### {t['name']}\n"
            md += f"- Source Rows: {t.get('source_rows', 0)}\n"
            md += f"- Migrated Rows: {t.get('migrated_rows', 0)}\n"
            md += f"- Status: {t.get('status', 'Unknown')}\n\n"

        if errors:
            md += "## Errors Encountered & Fixed\n"
            for e in errors:
                md += f"- **{e['table']}**: {e['message']}\n"
                if "fix" in e:
                    md += f"  - *Fix Applied*: `{e['fix']}`\n"

        return md


report_agent = ReportAgent()
