import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Simulate exactly what the upload endpoint does
import io
import unilog
from unilog.parsers.windows import WindowsParser

sample_csv = '''Keywords,Date and Time,Source,Event ID,Task Category
Audit Success,19-07-2026 09:58:57,Microsoft-Windows-Security-Auditing,4624,Logon,"An account was successfully logged on.

Subject:
\tSecurity ID:\t\tSYSTEM
\tAccount Name:\t\tSOHAM$
\tAccount Domain:\t\tWORKGROUP
\tLogon ID:\t\t0x3E7

Logon Information:
\tLogon Type:\t\t5
\tVirtual Account:\t\tNo
\tElevated Token:\t\tYes"
Audit Failure,19-07-2026 09:59:10,Microsoft-Windows-Security-Auditing,4625,Logon,"An account failed to log on.

Subject:
\tSecurity ID:\t\tSYSTEM
\tAccount Name:\t\tSOHAM$

Failure Information:
\tFailure Reason:\t\tUnknown user name or bad password.
\tStatus:\t\t0xC000006D
\tSub Status:\t\t0xC0000064"
'''

# Step 1: auto-detect
text = sample_csv
det = unilog.detect(io.StringIO(text))
print(f"detect() result: {det['format']}")

# Step 2: CSV fallback check
wp = WindowsParser()
if wp._is_event_viewer_csv(text):
    print("_is_event_viewer_csv: True -> using 'windows' parser")
    resolved = "windows"
else:
    resolved = det["format"]

# Step 3: parse_string
df = unilog.parse_string(text, format=resolved)
print(f"\nparse_string() produced {len(df)} records:")
for _, row in df.iterrows():
    print(f"  [{row.get('level')}] {row.get('source')} | event_id={row.get('event_id')} | ts={row.get('timestamp')} | category={row.get('category')}")
