import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Reproduce the exact CSV the user uploaded (the first event from their log)
sample_csv = '''Keywords,Date and Time,Source,Event ID,Task Category
Audit Success,19-07-2026 09:58:57,Microsoft-Windows-Security-Auditing,4624,Logon,"An account was successfully logged on.

Subject:
\tSecurity ID:\t\tSYSTEM
\tAccount Name:\t\tSOHAM$
\tAccount Domain:\t\tWORKGROUP
\tLogon ID:\t\t0x3E7

Logon Information:
\tLogon Type:\t\t5
\tRestricted Admin Mode:\t-
\tVirtual Account:\t\tNo
\tElevated Token:\t\tYes

New Logon:
\tSecurity ID:\t\tSYSTEM
\tAccount Name:\t\tSYSTEM
\tAccount Domain:\t\tNT AUTHORITY"
'''

from unilog.parsers.windows import WindowsParser

parser = WindowsParser()
records = list(parser.parse(sample_csv))

print(f"Records produced: {len(records)}")
for i, rec in enumerate(records):
    print(f"\n  Record {i+1}:")
    for k, v in rec.items():
        if k != "raw":
            val = str(v)[:80] if v else None
            print(f"    {k:<12} = {val}")
