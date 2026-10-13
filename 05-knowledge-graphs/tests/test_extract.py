from kglab.extract import LINK_RELATIONS, json_schema, parse_triples


def test_parse_valid_and_invalid():
    raw = ('{"triples": [{"subject": "R-1", "relation": "serves_bay", "object": "bay 5"},'
           '{"subject": "R-1", "relation": "drives_to", "object": "bay 5"},'
           '{"subject": "", "relation": "moves", "object": "boards"}]}')
    valid, invalid = parse_triples(raw)
    assert [(m.subject, m.relation, m.object) for m in valid] == [("R-1", "serves_bay", "bay 5")]
    assert [i["error"] for i in invalid] == ["relation not in schema", "missing field"]


def test_parse_text_around_json():
    valid, invalid = parse_triples('Here: {"triples": []} done')
    assert valid == [] and invalid == []
    assert parse_triples("no json")[1][0]["error"] == "no JSON object"


def test_schema_enum():
    rel = json_schema()["properties"]["triples"]["items"]["properties"]["relation"]
    assert rel["enum"] == list(LINK_RELATIONS)
    assert "enum" not in json_schema(constrained=False)["properties"]["triples"]["items"]["properties"]["relation"]
