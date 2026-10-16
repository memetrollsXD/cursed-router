import unittest

from modules.portal.rules import RuleEngine


class TestRuleEngine(unittest.TestCase):
    def test_rule_engine_loads_rules(self) -> None:
        engine = RuleEngine.from_yaml("rules/default.yaml")
        self.assertGreaterEqual(engine.rule_count, 1)

    def test_rule_matching_by_client_and_domain(self) -> None:
        engine = RuleEngine.from_yaml("rules/default.yaml")
        rule = engine.match("device-7", "portal")
        self.assertIsNotNone(rule)
        assert rule is not None
        self.assertEqual(rule["action"], "cat-portal")


if __name__ == "__main__":
    unittest.main()
