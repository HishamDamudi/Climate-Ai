"""
Injection-detection utilities.

Two distinct threats are relevant to this project because of the mixed
storage backends (pandas/CSV + MongoDB):

1. Classic SQL-injection-style payloads (`' OR '1'='1`, `; DROP TABLE`,
   `UNION SELECT`, SQL comments, etc.) - these can't directly harm MongoDB
   or pandas (no SQL is ever executed here), but they're still a strong
   signal of a malicious or fuzzing client and are worth rejecting outright
   rather than storing verbatim.

2. NoSQL / MongoDB *operator* injection - e.g. a client sending
   `{"$ne": null}` or `{"$gt": ""}` as a field value instead of a plain
   string. If that raw dict were ever passed straight into a Mongo query
   filter (`collection.find({"district": user_input})`), Mongo would
   interpret the operator instead of matching it as a literal - this is the
   real, MongoDB-specific injection risk. The defense used throughout this
   codebase is: never pass a client-supplied dict into a query filter -
   every field is coerced to its expected primitive type (str/float/int)
   *before* it touches pymongo, which destroys any operator structure.

`is_suspicious()` is a defense-in-depth pattern check (belt-and-braces on
top of type coercion + the existing "district must be a known value"
allowlist check) - it's intentionally conservative and meant for free-text
fields like usernames, district/state names, and alert search queries.
"""
import re

# A representative (not exhaustive) set of classic SQL-injection tokens.
_SQLI_PATTERNS = [
    r"(\s|^)(OR|AND)\s+['\"]?\d+['\"]?\s*=\s*['\"]?\d+",  # OR 1=1 / AND '1'='1'
    r"--",                                                  # SQL line comment
    r"/\*.*\*/",                                            # SQL block comment
    r";\s*(DROP|DELETE|UPDATE|INSERT|ALTER|TRUNCATE)\s",    # stacked queries
    r"\bUNION\b.*\bSELECT\b",
    r"\bSELECT\b.*\bFROM\b",
    r"\bDROP\s+TABLE\b",
    r"\bxp_cmdshell\b",
    r"'\s*OR\s*'",
]

# MongoDB query-operator injection - a raw operator key showing up in text.
_NOSQLI_PATTERNS = [
    r"\$where", r"\$ne\b", r"\$gt\b", r"\$lt\b", r"\$regex", r"\$or\b", r"\$exists",
]

# Basic script/markup injection (defense-in-depth for any field later
# rendered in a UI without escaping).
_XSS_PATTERNS = [
    r"<\s*script", r"javascript:", r"on\w+\s*=",
]

_ALL_PATTERNS = [re.compile(p, re.IGNORECASE) for p in (_SQLI_PATTERNS + _NOSQLI_PATTERNS + _XSS_PATTERNS)]


def is_suspicious(value: str) -> bool:
    """Returns True if `value` contains a recognizable injection pattern.
    Only meaningful for str input - callers should already be relying on
    Pydantic/type coercion to reject non-string structures (e.g. a dict
    sent where a string was expected)."""
    if not isinstance(value, str):
        return True  # wrong type at a text field is itself suspicious
    return any(p.search(value) for p in _ALL_PATTERNS)


def sanitize_text(value: str, max_len: int = 200) -> str:
    """Strips control characters and truncates length. Does NOT attempt to
    'clean' injection payloads and continue - for this project the policy is
    reject-on-detection (see is_suspicious) rather than sanitize-and-allow,
    since silently rewriting malicious input can mask attacks in logs."""
    value = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", value)
    return value.strip()[:max_len]
