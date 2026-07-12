from unilog.parsers.windows import WindowsParser

def test_empty_xml_elements():
    parser = WindowsParser()
    
    # Malformed XML events
    inputs = [
        "<Event></Event>",
        "<Event><System></System></Event>",
        "<Event xmlns=\"...\"><System><ProviderName>X</ProviderName></System></Event>",
        "<Event",
        "<>",
        ""
    ]
    
    for inp in inputs:
        res = parser.parse_line(inp)
        # WindowsParser should skip or return parse error
        assert res.get("_parse_error") is True
