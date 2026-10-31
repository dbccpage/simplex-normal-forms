"""Property-based and adversarial tests for the normal_forms.ai RAG/MCP decorator pipeline.

Tests:
  1. 80 randomized trials of @coda_mur_projection over variable RAG chunk corpora and token
     budgets, checking SHA-256 Merkle loss ledgers, exact additive token conservation, lossless
     text reconstruction from (projected_chunks + loss_ledger), and fail-closed rejection on
     tampered ledgers or dropped protected fields.
  2. 80 randomized trials of @observer_freshness_gate over a 4-agent observer poset chain
     (O_1 <= O_2 <= O_3 <= O_4), checking upward poset monotonicity, lag-shift anti-monotonicity,
     and the epistemic authority firewall (certified_implies_authorized == False).
  3. Complete refusal matrix for Level 00 WDNF/PDNF (support floor, irreflexivity, ghost
     distinctions, witness multiplicity erasure), OBNF collision relativization, and ASRF
     self-reference / cycle guards.

AuthorityEffect: None.
certified_implies_authorized: false.
"""

from __future__ import annotations

import random
import unittest
from typing import Any, Dict, List, Mapping, Sequence

from normal_forms.ai import (
    CodaMurContextEnvelope,
    coda_mur_projection,
    detokenize_whitespace,
    evaluate_asrf_guard,
    evaluate_obnf_projection_collision,
    evaluate_wdnf_candidate_cut,
    observer_freshness_gate,
    run_rag_mcp_pipeline,
    tokenize_whitespace,
)
from normal_forms.observer_freshness_example import ObserverSpec
from normal_forms.reconciliation_example import verify_loss_ledger_integrity


class TestAiRagMcpPipeline(unittest.TestCase):
    """Property-based and adversarial verification for normal_forms.ai decorators."""

    def test_coda_mur_projection_decorator_context_truncation_loss_ledgers_80_trials(self) -> None:
        rng = random.Random(20261031)
        vocab = [
            "alpha",
            "beta",
            "gamma",
            "delta",
            "epsilon",
            "zeta",
            "eta",
            "theta",
            "iota",
            "kappa",
            "lambda",
            "mu",
            "nu",
            "xi",
            "omicron",
            "pi",
            "rho",
            "sigma",
            "tau",
            "upsilon",
        ]

        all_source_fields = (
            "chunk_id",
            "doc_id",
            "text",
            "relevance_score",
            "embedding_l2_norm",
            "internal_acl_role",
            "crawler_timestamp",
        )

        lossless_count = 0
        degraded_count = 0

        for trial in range(80):
            num_chunks = rng.randint(3, 10)
            chunks: List[Dict[str, Any]] = []
            total_tokens = 0
            for idx in range(num_chunks):
                tok_len = rng.randint(6, 24)
                words = [rng.choice(vocab) for _ in range(tok_len)]
                text_val = " ".join(words)
                total_tokens += tok_len
                chunks.append(
                    {
                        "chunk_id": f"trial_{trial}_chk_{idx}",
                        "doc_id": f"doc_{trial}_{idx}",
                        "text": text_val,
                        "relevance_score": round(rng.uniform(0.5, 0.99), 4),
                        "embedding_l2_norm": round(rng.uniform(0.98, 1.02), 6),
                        "internal_acl_role": rng.choice(["finance", "legal", "engineering"]),
                        "crawler_timestamp": 1700000000 + idx * 60,
                    }
                )

            # Randomly choose lossless vs attribute-dropping vs token-truncating regime
            mode = trial % 4
            if mode == 0:
                # Lossless: keep all source fields and no token truncation
                target_fields = all_source_fields
                budget = total_tokens + 50
            elif mode == 1:
                # Attribute erasure only, no token truncation
                target_fields = ("chunk_id", "doc_id", "text", "relevance_score")
                budget = total_tokens + 50
            elif mode == 2:
                # Token truncation only, all fields retained
                target_fields = all_source_fields
                budget = max(1, rng.randint(4, total_tokens - 2))
            else:
                # Both attribute erasure and aggressive token truncation (dropping whole chunks too)
                target_fields = ("chunk_id", "doc_id", "text", "relevance_score")
                budget = max(1, rng.randint(3, max(4, total_tokens // 2)))

            @coda_mur_projection(
                source_fields=all_source_fields,
                target_fields=target_fields,
                key_field="chunk_id",
                protected_fields=("chunk_id", "doc_id"),
                score_field="relevance_score",
                text_field="text",
                max_token_budget=budget,
            )
            def project_chunks(
                src_chunks: Sequence[Mapping[str, Any]],
            ) -> List[Dict[str, Any]]:
                return [{k: c[k] for k in target_fields} for c in src_chunks]

            envelope = project_chunks(chunks)

            self.assertTrue(envelope.admitted)
            self.assertTrue(envelope.certified)
            self.assertFalse(envelope.authorized)
            self.assertFalse(envelope.certified_implies_authorized)
            self.assertEqual(envelope.authority_effect, "None")
            self.assertTrue(envelope.token_conservation_commutes)
            self.assertTrue(envelope.score_conservation_commutes)
            self.assertEqual(envelope.source_token_count, total_tokens)
            self.assertEqual(
                envelope.retained_token_count + envelope.truncated_token_count,
                envelope.source_token_count,
            )
            self.assertLessEqual(envelope.retained_token_count, budget)

            if mode == 0:
                lossless_count += 1
                self.assertEqual(envelope.local_route, "TransportOk")
                self.assertEqual(envelope.canonical_terminal, "Preserve")
                self.assertIsNone(envelope.loss_ledger)
                self.assertEqual(envelope.truncated_token_count, 0)
                self.assertEqual(envelope.dropped_chunk_count, 0)
            else:
                degraded_count += 1
                self.assertEqual(envelope.local_route, "DegradedTransportWithLoss")
                self.assertEqual(envelope.canonical_terminal, "Quarantine")
                self.assertIsNotNone(envelope.loss_ledger)
                assert envelope.loss_ledger is not None
                ok_seal, err_seal = verify_loss_ledger_integrity(envelope.loss_ledger)
                self.assertTrue(ok_seal, msg=f"LossLedger seal failed: {err_seal}")

                # Reconstruct exact original text of every chunk from retained_chunks + LossLedger
                retained_map = {c["chunk_id"]: c for c in envelope.projected_chunks}
                ledger_map = {
                    e["row_key"]: e["erased_fields"] for e in envelope.loss_ledger["entries"]
                }
                for orig in chunks:
                    cid = orig["chunk_id"]
                    orig_tokens = tokenize_whitespace(orig["text"])
                    ret_tokens = (
                        tokenize_whitespace(retained_map[cid]["text"])
                        if cid in retained_map
                        else []
                    )
                    trunc_tokens = ledger_map[cid].get("__truncated_tokens__", [])
                    self.assertEqual(
                        ret_tokens + trunc_tokens,
                        orig_tokens,
                        msg=f"Exact token sequence reconstruction failed on chunk {cid}",
                    )
                    self.assertEqual(
                        detokenize_whitespace(ret_tokens + trunc_tokens),
                        orig["text"],
                    )

                # Negative control A: tampered LossLedger fails closed
                tampered_env = project_chunks(chunks, tamper_loss_ledger=True)
                self.assertFalse(tampered_env.admitted)
                self.assertFalse(tampered_env.certified)
                self.assertEqual(tampered_env.local_route, "TransportViolation")
                self.assertEqual(tampered_env.canonical_terminal, "Reject")

                # Negative control B: omitted LossLedger fails closed
                omitted_env = project_chunks(chunks, omit_loss_ledger=True)
                self.assertFalse(omitted_env.admitted)
                self.assertFalse(omitted_env.certified)
                self.assertEqual(omitted_env.local_route, "TransportViolation")
                self.assertEqual(omitted_env.canonical_terminal, "Reject")

        self.assertGreaterEqual(lossless_count, 15)
        self.assertGreaterEqual(degraded_count, 50)

    def test_observer_freshness_gate_and_mcp_authorization_firewall_80_trials(self) -> None:
        rng = random.Random(20261101)

        poset = [
            ObserverSpec("obs_tier1_hft", 5, ("rag_core",)),
            ObserverSpec("obs_tier2_Search", 20, ("rag_core", "rag_enterprise")),
            ObserverSpec(
                "obs_tier3_analyst",
                90,
                ("rag_core", "rag_enterprise", "rag_compliance"),
            ),
            ObserverSpec(
                "obs_tier4_archive",
                600,
                ("rag_core", "rag_enterprise", "rag_compliance", "rag_cold"),
            ),
        ]

        @coda_mur_projection(
            source_fields=("chunk_id", "doc_id", "text", "relevance_score", "debug_trace"),
            target_fields=("chunk_id", "doc_id", "text", "relevance_score"),
            key_field="chunk_id",
            protected_fields=("chunk_id", "doc_id"),
            max_token_budget=16,
        )
        def compress_chunks(chunks: Sequence[Mapping[str, Any]]) -> None:
            return None

        execution_counter = {"count": 0}

        @observer_freshness_gate(observer_poset=poset)
        def mcp_write_audit_note(
            envelope: CodaMurContextEnvelope,
            *,
            ticket_id: str = "TCK-1",
        ) -> Dict[str, Any]:
            execution_counter["count"] += 1
            return {
                "ticket_id": ticket_id,
                "retained_tokens": envelope.retained_token_count,
            }

        authorized_executions = 0
        certified_not_authorized_blocks = 0

        for trial in range(80):
            candidates = [
                {
                    "chunk_id": f"c_{trial}_1",
                    "doc_id": f"d_{trial}_1",
                    "text": "First retrieved evidence segment with nine distinct whitespace tokens here",
                    "relevance_score": 0.95,
                    "debug_trace": "trace_a",
                },
                {
                    "chunk_id": f"c_{trial}_2",
                    "doc_id": f"d_{trial}_2",
                    "text": "Second retrieved evidence segment with additional context tokens for truncation",
                    "relevance_score": 0.88,
                    "debug_trace": "trace_b",
                },
            ]

            lag_low = rng.choice([2, 10, 45, 200, 800])
            lag_high = lag_low + rng.randint(15, 300)
            scope = rng.choice(["rag_core", "rag_enterprise", "rag_compliance", "rag_cold"])
            obs_spec = rng.choice(poset)

            # 1. Evaluate with policy_verifier=None: even if fresh, tool MUST NOT execute
            prev_count = execution_counter["count"]
            pipe_unauth = run_rag_mcp_pipeline(
                candidates=candidates,
                projection_fn=compress_chunks,
                mcp_tool_fn=mcp_write_audit_note,
                observer_id=obs_spec.observer_id,
                packet_metadata={"packet_scope": scope, "replica_lag_seconds": lag_low},
                policy_verifier=None,
                ticket_id=f"TCK-{trial}",
            )
            self.assertFalse(pipe_unauth.tool_executed)
            self.assertFalse(pipe_unauth.authorized)
            self.assertEqual(execution_counter["count"], prev_count)

            assert pipe_unauth.mcp_receipt is not None
            self.assertTrue(pipe_unauth.mcp_receipt.poset_valid_order)
            self.assertTrue(pipe_unauth.mcp_receipt.poset_monotonic)

            if pipe_unauth.mcp_receipt.freshness_route == "AuthorizedFresh":
                certified_not_authorized_blocks += 1
                self.assertTrue(pipe_unauth.certified)
                self.assertEqual(
                    pipe_unauth.mcp_receipt.terminal_route,
                    "CertifiedNotAuthorized",
                )
                self.assertEqual(
                    pipe_unauth.mcp_receipt.authorization_status,
                    "certified_not_authorized",
                )

            # 2. Evaluate with bare string policy_verifier="authorized": must fail closed
            pipe_str_verifier = run_rag_mcp_pipeline(
                candidates=candidates,
                projection_fn=compress_chunks,
                mcp_tool_fn=mcp_write_audit_note,
                observer_id=obs_spec.observer_id,
                packet_metadata={"packet_scope": scope, "replica_lag_seconds": lag_low},
                policy_verifier="authorized",
            )
            self.assertFalse(pipe_str_verifier.tool_executed)
            self.assertFalse(pipe_str_verifier.authorized)

            # 3. Evaluate with independent policy_verifier={"verifier_identity": "policy_guard_v2", "outcome": "authorized"}
            pipe_auth_low = run_rag_mcp_pipeline(
                candidates=candidates,
                projection_fn=compress_chunks,
                mcp_tool_fn=mcp_write_audit_note,
                observer_id=obs_spec.observer_id,
                packet_metadata={"packet_scope": scope, "replica_lag_seconds": lag_low},
                policy_verifier={
                    "verifier_identity": "policy_guard_v2",
                    "outcome": "authorized",
                },
                ticket_id=f"TCK-{trial}",
            )
            assert pipe_auth_low.mcp_receipt is not None

            expected_fresh_low = (
                scope in obs_spec.authorized_scopes and lag_low <= obs_spec.max_lag_seconds
            )
            self.assertEqual(pipe_auth_low.tool_executed, expected_fresh_low)
            self.assertEqual(pipe_auth_low.authorized, expected_fresh_low)
            if expected_fresh_low:
                authorized_executions += 1
                self.assertEqual(pipe_auth_low.pipeline_terminal, "Preserve")
                self.assertEqual(
                    pipe_auth_low.mcp_receipt.tool_output["ticket_id"],
                    f"TCK-{trial}",
                )

            # 4. Lag-shift anti-monotonicity: increasing lag to lag_high >= lag_low never flips stale -> fresh
            pipe_auth_high = run_rag_mcp_pipeline(
                candidates=candidates,
                projection_fn=compress_chunks,
                mcp_tool_fn=mcp_write_audit_note,
                observer_id=obs_spec.observer_id,
                packet_metadata={"packet_scope": scope, "replica_lag_seconds": lag_high},
                policy_verifier={
                    "verifier_identity": "policy_guard_v2",
                    "outcome": "authorized",
                },
            )
            assert pipe_auth_high.mcp_receipt is not None
            for res_low, res_high in zip(
                pipe_auth_low.mcp_receipt.poset_resolutions,
                pipe_auth_high.mcp_receipt.poset_resolutions,
            ):
                if not res_low["authorized"]:
                    self.assertFalse(
                        res_high["authorized"],
                        msg=f"Lag anti-monotonicity violated for {res_low['observer_id']}",
                    )

        self.assertGreaterEqual(authorized_executions, 15)
        self.assertGreaterEqual(certified_not_authorized_blocks, 15)

    def test_wdnf_primitive_difference_obnf_and_asrf_refusal_matrix(self) -> None:
        # 1. WDNF Subsingleton collapse refusal (|X| < 2)
        subsingleton = [{"chunk_id": "only_one", "doc_id": "d1", "text": "hello world"}]
        wdnf_single = evaluate_wdnf_candidate_cut(subsingleton)
        self.assertFalse(wdnf_single.admitted)
        self.assertEqual(wdnf_single.local_terminal, "SubsingletonCollapseRefusal")
        self.assertEqual(wdnf_single.canonical_terminal, "Refuse")

        # 2. WDNF Irreflexivity refusal ((x, x) asserted)
        two_chunks = [
            {"chunk_id": "c1", "doc_id": "d1", "text": "alpha beta"},
            {"chunk_id": "c2", "doc_id": "d2", "text": "gamma delta"},
        ]
        wdnf_self = evaluate_wdnf_candidate_cut(
            two_chunks,
            asserted_pairs=[("c1", "c1")],
        )
        self.assertFalse(wdnf_self.admitted)
        self.assertEqual(wdnf_self.local_terminal, "IrreflexivityViolation")
        self.assertEqual(wdnf_self.canonical_terminal, "Reject")
        self.assertEqual(wdnf_self.offending_pair, ("c1", "c1"))

        # 3. WDNF Ghost distinction refusal (asserted difference with zero witness differences)
        duplicate_content = [
            {"chunk_id": "c1", "doc_id": "same_doc", "text": "identical text"},
            {"chunk_id": "c2", "doc_id": "same_doc", "text": "identical text"},
        ]
        wdnf_ghost = evaluate_wdnf_candidate_cut(
            duplicate_content,
            distinction_fields=("doc_id", "text"),
            asserted_pairs=[("c1", "c2")],
        )
        self.assertFalse(wdnf_ghost.admitted)
        self.assertEqual(wdnf_ghost.local_terminal, "GhostDistinctionViolation")
        self.assertEqual(wdnf_ghost.canonical_terminal, "Reject")

        # 4. WDNF Witness multiplicity erasure (multiple differing features collapse to 1 pair)
        wdnf_valid = evaluate_wdnf_candidate_cut(
            two_chunks,
            distinction_fields=("doc_id", "text"),
            asserted_pairs=[("c1", "c2"), ("c2", "c1")],
        )
        self.assertTrue(wdnf_valid.admitted)
        self.assertEqual(wdnf_valid.local_terminal, "AdmittedCut")
        self.assertEqual(wdnf_valid.canonical_terminal, "Preserve")
        self.assertEqual(wdnf_valid.normalized_distinction_pairs, (("c1", "c2"),))

        # 5. OBNF Admissible non-key collision vs Protected determinant collision
        obnf_admissible = evaluate_obnf_projection_collision(
            source_chunks=two_chunks,
            projected_chunks=[
                {"chunk_id": "c1", "text": "collapsed summary"},
                {"chunk_id": "c2", "text": "collapsed summary"},
            ],
            key_field="chunk_id",
            target_fields=("chunk_id", "text"),
            protected_fields=("chunk_id",),
        )
        self.assertTrue(obnf_admissible.admitted)
        self.assertEqual(obnf_admissible.local_terminal, "AcceptAdmissibleCollision")
        self.assertEqual(obnf_admissible.colliding_pairs, (("c1", "c2"),))

        obnf_obstructed = evaluate_obnf_projection_collision(
            source_chunks=two_chunks,
            projected_chunks=[
                {"chunk_id": "c1", "doc_id": "colliding_doc", "text": "a"},
                {"chunk_id": "c2", "doc_id": "colliding_doc", "text": "b"},
            ],
            key_field="chunk_id",
            target_fields=("chunk_id", "doc_id", "text"),
            protected_fields=("doc_id",),
        )
        self.assertFalse(obnf_obstructed.admitted)
        self.assertEqual(obnf_obstructed.local_terminal, "PromoteToObstruction")
        self.assertEqual(obnf_obstructed.canonical_terminal, "Reject")

        # 6. ASRF Self-Reference & Directed Cycle Refusals
        asrf_self_id = evaluate_asrf_guard(
            {"producer_identity": "agent_alpha", "evaluator_identity": "agent_alpha"}
        )
        self.assertFalse(asrf_self_id.admitted)
        self.assertEqual(asrf_self_id.local_terminal, "SelfReferenceRefusal")
        self.assertEqual(asrf_self_id.canonical_terminal, "Refuse")

        asrf_cycle = evaluate_asrf_guard(
            {
                "producer_identity": "agent_alpha",
                "evaluator_identity": "agent_beta",
                "call_graph_edges": [
                    ("agent_alpha", "agent_beta"),
                    ("agent_beta", "agent_gamma"),
                    ("agent_gamma", "agent_alpha"),
                ],
            }
        )
        self.assertFalse(asrf_cycle.admitted)
        self.assertEqual(asrf_cycle.local_terminal, "CycleDetected")
        self.assertEqual(asrf_cycle.canonical_terminal, "Refuse")
        self.assertEqual(
            asrf_cycle.cycle_witness,
            ("agent_alpha", "agent_beta", "agent_gamma", "agent_alpha"),
        )


if __name__ == "__main__":
    unittest.main()
