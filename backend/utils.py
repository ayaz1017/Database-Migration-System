import re
from typing import Any

def scrub_credentials(data: Any) -> Any:
    """
    Recursively remove sensitive fields from dicts/lists.
    """
    if isinstance(data, dict):
        scrubbed = {}
        for k, v in data.items():
            k_lower = str(k).lower()
            if any(sub in k_lower for sub in ["password", "pass", "secret", "token"]):
                scrubbed[k] = "***MASKED***"
            elif any(sub in k_lower for sub in ["host", "ip", "url", "uri"]):
                if isinstance(v, str):
                    # Keep only first 3 chars + ***
                    scrubbed[k] = v[:3] + "***" if len(v) > 3 else "***"
                else:
                    scrubbed[k] = "***MASKED***"
            elif k_lower in ["user", "username"]:
                if isinstance(v, str):
                    # Basic masking for usernames
                    scrubbed[k] = v[0] + "***" + v[-1] if len(v) > 2 else "***"
                else:
                    scrubbed[k] = "***MASKED***"
            elif k_lower == "full_payload":
                # Ensure we also aggressively mask full payload blobs if they sneak in
                if isinstance(v, str):
                    try:
                        import json
                        parsed = json.loads(v)
                        scrubbed[k] = json.dumps(scrub_credentials(parsed))
                    except:
                        scrubbed[k] = "***REDACTED_PAYLOAD***"
                else:
                    scrubbed[k] = scrub_credentials(v)
            else:
                scrubbed[k] = scrub_credentials(v)
        return scrubbed
    elif isinstance(data, list):
        return [scrub_credentials(item) for item in data]
    return data

def sanitize_identifier(identifier: str) -> str:
    """
    Sanitize a SQL identifier (table/column/schema name) to prevent SQL injection.
    Raises ValueError if identifier contains invalid characters.
    Allows dots for schema-qualified names (e.g. dbo.users).
    """
    if not re.match(r"^[a-zA-Z0-9_.-]+$", identifier):
        raise ValueError(f"Invalid characters in SQL identifier: {identifier}")
    return identifier
