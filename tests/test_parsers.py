import pytest
from datetime import datetime
from unilog.parsers.json_log import JSONParser

def test_json_parser_minimal():
    parser = JSONParser()
    
    # Test valid line
    line = '{"time": "2026-07-10T12:00:00Z", "level": "info", "msg": "application started"}'
    assert parser.match(line)
    res = parser.parse_line(line)
    assert not res.get("_parse_error")
    assert isinstance(res["timestamp"], datetime)
    assert res["level"] == "INFO"
    assert res["message"] == "application started"

    # Test field alias
    line2 = '{"@timestamp": "2026-07-10T12:00:00Z", "lvl": "warning", "log": "db warning"}'
    res2 = parser.parse_line(line2)
    assert res2["level"] == "WARNING"
    assert res2["message"] == "db warning"

    # Test auto level inference
    line3 = '{"timestamp": "2026-07-10T12:00:00Z", "message": "query failed", "status": "ERROR"}'
    res3 = parser.parse_line(line3)
    assert res3["level"] == "ERROR"

    # Test invalid json
    bad_line = '{"invalid": json'
    assert not parser.match(bad_line)
    res_bad = parser.parse_line(bad_line)
    assert res_bad.get("_parse_error")

    # Test confidence score
    sample = [
        '{"time": "2026-07-10T12:00:00Z", "level": "info", "msg": "ok"}',
        '{"time": "2026-07-10T12:00:01Z", "level": "warn", "msg": "ok"}',
        'invalid log line'
    ]
    score = parser.confidence_score(sample)
    assert score > 0.5

def test_nginx_parser_minimal():
    from unilog.parsers.nginx import NginxParser
    parser = NginxParser()
    
    # Combined format
    line = '127.0.0.1 - - [10/Jul/2026:20:53:59 +0530] "GET /api/v1/users HTTP/1.1" 200 456 "http://referer.com" "Mozilla/5.0"'
    assert parser.match(line)
    res = parser.parse_line(line)
    assert not res.get("_parse_error")
    assert res["source_ip"] == "127.0.0.1"
    assert res["method"] == "GET"
    assert res["path"] == "/api/v1/users"
    assert res["protocol"] == "HTTP/1.1"
    assert res["status_code"] == 200
    assert res["size"] == 456
    assert res["referer"] == "http://referer.com"
    assert res["user_agent"] == "Mozilla/5.0"
    assert isinstance(res["timestamp"], datetime)

    # Common format (no referer/UA)
    line2 = '2001:db8::1 - - [10/Jul/2026:20:53:59 +0530] "GET / HTTP/1.1" 304 -'
    res2 = parser.parse_line(line2)
    assert not res2.get("_parse_error")
    assert res2["source_ip"] == "2001:db8::1"
    assert res2["size"] is None  # '-' is converted to None
    assert res2["status_code"] == 304
    assert res2.get("referer") is None

    # Invalid line
    bad_line = "not an nginx line"
    assert not parser.match(bad_line)
    assert parser.parse_line(bad_line).get("_parse_error")

def test_apache_parser_minimal():
    from unilog.parsers.apache import ApacheParser
    parser = ApacheParser()
    
    # Combined format with negative timezone offset
    line = '127.0.0.1 - - [10/Jul/2026:20:53:59 -0700] "GET /index.html HTTP/1.1" 200 1024 "http://referrer.org" "Mozilla/5.0"'
    assert parser.match(line)
    res = parser.parse_line(line)
    assert not res.get("_parse_error")
    assert res["source_ip"] == "127.0.0.1"
    assert res["status_code"] == 200
    assert res["size"] == 1024
    assert res["referer"] == "http://referrer.org"
    assert isinstance(res["timestamp"], datetime)

def test_syslog_parser_minimal():
    from unilog.parsers.syslog import SyslogParser
    parser = SyslogParser()

    # RFC 3164 format
    line = "<34>Oct 11 22:14:15 mymachine su[1234]: 'su root' failed for lonvick on /dev/pts/8"
    assert parser.match(line)
    res = parser.parse_line(line)
    assert not res.get("_parse_error")
    assert res["priority"] == 34
    assert res["level"] == "CRITICAL"  # 34 % 8 = 2 (CRITICAL)
    assert res["hostname"] == "mymachine"
    assert res["process"] == "su"
    assert res["pid"] == 1234
    assert res["message"] == "'su root' failed for lonvick on /dev/pts/8"
    assert res["syslog_version"] == "3164"
    assert isinstance(res["timestamp"], datetime)

    # RFC 5424 format
    line2 = '<165>1 2003-10-11T22:14:15.003Z mymachine.example.com evtsys 1024 - [exampleSDID@32473 iut="3" eventSource="Application"] An application event occurred'
    assert parser.match(line2)
    res2 = parser.parse_line(line2)
    assert not res2.get("_parse_error")
    assert res2["priority"] == 165
    assert res2["level"] == "NOTICE"  # 165 % 8 = 5 (NOTICE)
    assert res2["hostname"] == "mymachine.example.com"
    assert res2["process"] == "evtsys"
    assert res2["pid"] == 1024
    assert res2["msgid"] is None
    assert res2["structured_data"] == '[exampleSDID@32473 iut="3" eventSource="Application"]'
    assert res2["message"] == "An application event occurred"
    assert res2["syslog_version"] == "5424"
    assert isinstance(res2["timestamp"], datetime)

def test_django_parser_minimal():
    from unilog.parsers.django import DjangoParser
    parser = DjangoParser()

    # Django format
    line = "[2026-07-10 12:00:00] INFO django.request: GET /api/v1/users 200 45ms"
    assert parser.match(line)
    res = parser.parse_line(line)
    assert not res.get("_parse_error")
    assert res["level"] == "INFO"
    assert res["logger"] == "django.request"
    assert res["message"] == "GET /api/v1/users 200 45ms"
    assert isinstance(res["timestamp"], datetime)

    # Python bare logging format with warning
    line2 = "2026-07-10 12:00:01,123 - root - WARN - slow query detected"
    assert parser.match(line2)
    res2 = parser.parse_line(line2)
    assert not res2.get("_parse_error")
    assert res2["level"] == "WARNING"  # WARN normalized to WARNING
    assert res2["logger"] == "root"
    assert res2["message"] == "slow query detected"
    assert isinstance(res2["timestamp"], datetime)

def test_windows_parser_csv_minimal():
    from unilog.parsers.windows import WindowsParser
    parser = WindowsParser()

    # CSV Header line (should yield _parse_error = True)
    header = "Level,Date and Time,Source,Event ID,Task Category,Description"
    assert parser.match(header)
    assert parser.parse_line(header).get("_parse_error")

    # CSV Data line
    line = '"Warning","2026-07-10 12:01:00","Disk",7,"None","The device has a bad block."'
    assert parser.match(line)
    res = parser.parse_line(line)
    assert not res.get("_parse_error")
    assert res["level"] == "WARNING"
    assert res["source"] == "Disk"
    assert res["event_id"] == 7
    assert res["category"] == "None"
    assert res["message"] == "The device has a bad block."
    assert isinstance(res["timestamp"], datetime)

def test_windows_parser_xml_minimal():
    from unilog.parsers.windows import WindowsParser
    parser = WindowsParser()

    # XML Format
    line = (
        '<Event xmlns="http://schemas.microsoft.com/win/2004/08/events/event">'
        '<System>'
        '<Provider Name="Microsoft-Windows-Security-Auditing"/>'
        '<EventID>4624</EventID>'
        '<TimeCreated SystemTime="2026-07-10T12:00:00.000000000Z"/>'
        '<Level>4</Level>'
        '<Task>12544</Task>'
        '</System>'
        '<EventData>'
        '<Data Name="TargetUserName">SYSTEM</Data>'
        '</EventData>'
        '</Event>'
    )
    assert parser.match(line)
    res = parser.parse_line(line)
    assert not res.get("_parse_error")
    assert res["level"] == "INFO"
    assert res["source"] == "Microsoft-Windows-Security-Auditing"
    assert res["event_id"] == 4624
    assert res["category"] == "12544"
    assert res["message"] == "TargetUserName=SYSTEM"
    assert isinstance(res["timestamp"], datetime)

def test_custom_parser_and_registration():
    import pytest
    from unilog.core import register_format, parse_string
    from unilog.registry import get_parser

    # Register valid custom format
    register_format(
        name="myapp",
        pattern=r'^(?P<time>\S+) (?P<level>\w+) (?P<message>.+)$',
        timestamp_field="time",
        timestamp_format="%Y-%m-%dT%H:%M:%S"
    )

    parser_cls = get_parser("myapp")
    assert parser_cls is not None
    assert parser_cls.name == "myapp"

    parser = parser_cls()
    line = "2026-07-10T12:00:00 INFO application started"
    assert parser.match(line)
    res = parser.parse_line(line)
    assert not res.get("_parse_error")
    assert res["level"] == "INFO"
    assert res["message"] == "application started"
    assert isinstance(res["timestamp"], datetime)

    # Parsing with parse_string using custom format
    df = parse_string("2026-07-10T12:00:00 INFO ok", format="myapp")
    assert len(df) == 1
    assert df.loc[0, "level"] == "INFO"

    # Registering with invalid pattern (no named groups) should raise ValueError
    with pytest.raises(ValueError, match="must contain at least one named group"):
        register_format(name="badapp", pattern=r'^\S+ \w+ .+$')
