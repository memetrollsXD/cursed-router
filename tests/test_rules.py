from modules.portal.rules import RuleEngine


def test_rule_engine_loads_rules() -> None:
    engine = RuleEngine.from_yaml("rules/default.yaml")
    assert engine.rule_count >= 1


def test_rule_matching_by_client_and_domain() -> None:
    engine = RuleEngine.from_yaml("rules/default.yaml")
    rule = engine.match("device-7", "portal")
    assert rule is not None
    assert rule["action"] == "cat-portal"
