"""Verification suite for Simplex Normal Forms catalog, evaluators, Wiki, SVGs, and Claim Hygiene.

AuthorityEffect: None.
"""

from __future__ import annotations

import pathlib
import re
import unittest
import xml.etree.ElementTree as ET
from fractions import Fraction

from normal_forms import NormalFormsEvaluator, check_catalog
from normal_forms.catalog import _contract_paths
from normal_forms.contract_paths import CONTRACTS_DIR
from normal_forms.domain import (
    BqnfValidator,
    street_journal_title_passes_third_and_fails_boyce_codd,
)
from normal_forms.domain.tower_forms import verify_dhnf, verify_zfnf
from normal_forms.observer_freshness_example import evaluate_freshness

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

FORBIDDEN_PATTERNS = [
    re.compile(r"\bproves\b", re.IGNORECASE),
    re.compile(r"\bguarantees\b", re.IGNORECASE),
    re.compile(r"\bmathematically\s+verifies\b", re.IGNORECASE),
    re.compile(r"\bfundamentally\b", re.IGNORECASE),
    re.compile(r"\btrue\s+intelligence\b", re.IGNORECASE),
    re.compile(r"\bimpossible\b", re.IGNORECASE),
    re.compile(r"\buniversal\b", re.IGNORECASE),
    re.compile(r"\bflawless\b", re.IGNORECASE),
    re.compile(r"\bperfectly\b", re.IGNORECASE),
    re.compile(r"\bclearly\b", re.IGNORECASE),
    re.compile(r"\bobviously\b", re.IGNORECASE),
    re.compile(r"\bsimply\b", re.IGNORECASE),
    re.compile(r"\bmerely\b", re.IGNORECASE),
    re.compile(r"\bweaponized\b", re.IGNORECASE),
    re.compile(r"\bgtmur\b", re.IGNORECASE),
]


class TestSimplexNormalForms(unittest.TestCase):
    def test_all_112_contracts_validate_against_standard(self) -> None:
        paths = _contract_paths(CONTRACTS_DIR)
        self.assertEqual(len(paths), 112)
        findings = check_catalog()
        self.assertEqual(findings, [], f"Catalog validation findings: {findings}")

    def test_zero_gtmur_across_contracts_wiki_and_code(self) -> None:
        for folder in ("contracts", "normal_forms", "wiki", "images"):
            for p in (REPO_ROOT / folder).rglob("*"):
                if p.is_file() and p.suffix in {".yaml", ".md", ".svg", ".py", ".sql", ".json"}:
                    txt = p.read_text(encoding="utf-8")
                    self.assertNotIn("gtmur", txt.lower(), f"Found legacy gtmur in {p}")

    def test_every_normal_form_has_wiki_page_and_valid_svg(self) -> None:
        paths = _contract_paths(CONTRACTS_DIR)
        for cpath in paths:
            cid = cpath.stem
            wiki_page = REPO_ROOT / "wiki" / f"{cid}.md"
            svg_file = REPO_ROOT / "images" / f"{cid}.svg"
            wiki_svg = REPO_ROOT / "wiki" / "images" / f"{cid}.svg"
            self.assertTrue(wiki_page.is_file(), f"Missing wiki page for {cid}")
            self.assertTrue(svg_file.is_file(), f"Missing SVG for {cid}")
            self.assertTrue(wiki_svg.is_file(), f"Missing wiki/images SVG for {cid}")
            ET.fromstring(svg_file.read_text(encoding="utf-8"))

    def test_claim_hygiene_across_readme_wiki_and_svgs(self) -> None:
        targets = [REPO_ROOT / "README.md"]
        targets.extend(sorted((REPO_ROOT / "wiki").glob("*.md")))
        targets.extend(sorted((REPO_ROOT / "images").glob("*.svg")))
        for p in targets:
            txt = p.read_text(encoding="utf-8")
            for pat in FORBIDDEN_PATTERNS:
                m = pat.search(txt)
                self.assertIsNone(
                    m,
                    f"Forbidden word {m.group(0) if m else ''} matched {pat.pattern} in {p.name}",
                )

    def test_relational_and_cochain_evaluators(self) -> None:
        self.assertTrue(street_journal_title_passes_third_and_fails_boyce_codd())
        with NormalFormsEvaluator() as ev:
            rows = ev.normalize_0nf_to_1nf([(1, "Alice", "Math,Physics")])
            self.assertEqual(len(rows), 2)
            w5 = ev.evaluate_5nf_project_join_integrity(
                [
                    ("Alice", "Acme", "Widget"),
                    ("Alice", "Globex", "Gadget"),
                    ("Bob", "Acme", "Gadget"),
                ]
            )
            self.assertFalse(w5["is_5nf_compliant"])

        z_res = verify_zfnf(Fraction(5, 2), Fraction(5, 2))
        self.assertEqual(z_res.terminal, "CertifiedOptimalZeroGap")

        h_res = verify_dhnf(
            {(0, 1): Fraction(3)},
            {(0, 1): Fraction(3)},
            {(0, 1): Fraction(0)},
            {(0, 1): Fraction(0)},
        )
        self.assertEqual(h_res.terminal, "HodgeDecomposedExact")

    def test_bqnf_and_observer_freshness_evaluators(self) -> None:
        res = BqnfValidator.evaluate_case(
            {
                "boundary": {
                    "relations": ["Orders"],
                    "attributes": ["customer_id", "status", "amount"],
                    "predicates": ["status = paid"],
                    "groups": ["customer_id"],
                    "aggregates": ["SUM(amount)"],
                },
                "event": {
                    "op": "UPDATE",
                    "relation": "Orders",
                    "old": {"order_id": 1, "customer_id": 7, "status": "pending", "amount": 50},
                    "new": {"order_id": 1, "customer_id": 7, "status": "paid", "amount": 80},
                },
            }
        )
        self.assertEqual(res["terminal_route"], "Repair")
        self.assertFalse(res["authorized"])

        obs = evaluate_freshness(
            {
                "packet": {"value": 10, "replica_lag_seconds": 3, "packet_scope": "public"},
                "observers": [
                    {"observer_id": "strict", "max_lag_seconds": 1, "authorized_scopes": ["public"]},
                    {"observer_id": "relaxed", "max_lag_seconds": 5, "authorized_scopes": ["public"]},
                ],
            }
        )
        self.assertEqual(obs[0]["terminal_route"], "RefreshRequired")
        self.assertEqual(obs[1]["terminal_route"], "AuthorizedFresh")


if __name__ == "__main__":
    unittest.main()
