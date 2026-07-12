from unilog.parsers.windows import WindowsParser

def test_xml_entity_expansion_blocked():
    parser = WindowsParser()
    
    # Billion laughs expansion payload
    xml_bomb = (
        '<?xml version="1.0"?>'
        '<!DOCTYPE lolz ['
        '<!ENTITY lol "lol">'
        '<!ENTITY lol1 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">'
        '<!ENTITY lol2 "&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;">'
        ']>'
        '<Event xmlns="http://schemas.microsoft.com/win/2004/08/events/event">'
        '<System>'
        '<Provider Name="MockProvider"/>'
        '<EventID>100</EventID>'
        '<TimeCreated SystemTime="2026-07-10T12:00:00.000Z"/>'
        '<Level>4</Level>'
        '<Task>0</Task>'
        '</System>'
        '<EventData>'
        '<Data Name="Payload">&lol2;</Data>'
        '</EventData>'
        '</Event>'
    )
    
    # Parser should catch defusedxml EntitiesForbidden or DTDForbidden exception 
    # and return _parse_error = True
    res = parser.parse_line(xml_bomb)
    assert res.get("_parse_error") is True
    assert res.get("raw") == xml_bomb
