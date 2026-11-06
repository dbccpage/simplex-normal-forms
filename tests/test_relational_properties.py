"""Property-based correctness tests for classical relational dependency algebra.

Checks over seeded random functional-dependency sets on at most 6 attributes:
1. Attribute closure and candidate-key enumeration agree with brute force over all attribute subsets.
2. Bernstein 3NF synthesis is dependency-preserving and lossless (chase reaches a distinguished row).
3. Tsou-Fischer BCNF decomposition is lossless and every output table is in BCNF.
4. Chase lossy/lossless verdict agrees with actual natural join of projections on small instances,
   and when lossy, spurious_tuple_witness appears in the natural join of projections of the chase
   counterexample instance and not in the original relation.
"""

from __future__ import annotations

from itertools import combinations, product
import random
from typing import Dict, FrozenSet, Iterable, List, Sequence, Set, Tuple

from normal_forms.domain.relational import (
    FunctionalDependency,
    RelationalSchema,
     check_bcnf,
    chase_join_dependency,
    compute_attribute_closure,
)
from normal_forms.domain.relational_advanced import (
    decompose_bcnf_tree,
    project_functional_dependencies,
    synthesize_3nf_bernstein,
)


def _brute_force_closure(
    attrs: Sequence[str],
    seed_subset: Iterable[str],
    fds: Sequence[FunctionalDependency],
) -> FrozenSet[str]:
    """Computes X^+ by checking all 2^|U| Boolean valuations satisfying F."""
    attr_list = sorted(attrs)
    seed_set = set(seed_subset)
    in_closure = set(attr_list)

    for bits in product((0, 1), repeat=len(attr_list)):
        valuation = dict(zip(attr_list, bits))
        if not all(valuation[a] == 1 for a in seed_set):
            continue
        satisfies_fds = True
        for fd in fds:
            if all(valuation[a] == 1 for a in fd.determinant):
                if not all(valuation[b] == 1 for b in fd.dependent):
                    satisfies_fds = False
                    break
        if not satisfies_fds:
            continue
        for a in list(in_closure):
            if valuation[a] == 0:
                in_closure.remove(a)

    return frozenset(in_closure)


def _brute_force_candidate_keys(
    attrs: Sequence[str],
    fds: Sequence[FunctionalDependency],
) -> Set[FrozenSet[str]]:
    """Enumerates all minimal superkeys by checking all non-empty subsets of U."""
    attr_list = sorted(attrs)
    all_set = frozenset(attr_list)
    superkeys: List[FrozenSet[str]] = []

    for r in range(1, len(attr_list) + 1):
        for comb in combinations(attr_list, r):
            sub = frozenset(comb)
            if _brute_force_closure(attr_list, sub, fds) == all_set:
                superkeys.append(sub)

    minimal: Set[FrozenSet[str]] = set()
    for sk in superkeys:
        if not any(other < sk for other in superkeys):
            minimal.add(sk)
    return minimal


def _project_relation(
    rows: Sequence[Dict[str, str]],
    comp: Iterable[str],
) -> List[Dict[str, str]]:
    cols = sorted(comp)
    seen: Set[Tuple[str, ...]] = set()
    out: List[Dict[str, str]] = []
    for row in rows:
        key = tuple(row[c] for c in cols)
        if key not in seen:
            seen.add(key)
            out.append({c: row[c] for c in cols})
    return out


def _natural_join(
    left: Sequence[Dict[str, str]],
    right: Sequence[Dict[str, str]],
) -> List[Dict[str, str]]:
    if not left:
        return []
    if not right:
        return []
    left_cols = set(left[0].keys())
    right_cols = set(right[0].keys())
    shared = sorted(left_cols & right_cols)
    all_cols = sorted(left_cols | right_cols)

    seen: Set[Tuple[str, ...]] = set()
    joined: List[Dict[str, str]] = []
    for r1 in left:
        for r2 in right:
            if all(r1[c] == r2[c] for c in shared):
                merged = {**r1, **r2}
                tup = tuple(merged[c] for c in all_cols)
                if tup not in seen:
                    seen.add(tup)
                    joined.append({c: merged[c] for c in all_cols})
    return joined


def _join_all_projections(
    rows: Sequence[Dict[str, str]],
    components: Sequence[Iterable[str]],
) -> List[Dict[str, str]]:
    projections = [_project_relation(rows, comp) for comp in components]
    if not projections:
        return []
    acc = projections[0]
    for proj in projections[1:]:
        acc = _natural_join(acc, proj)
    return acc


def _relation_satisfies_fds(
    rows: Sequence[Dict[str, str]],
    fds: Iterable[FunctionalDependency],
) -> bool:
    for fd in fds:
        det_cols = sorted(fd.determinant)
        dep_cols = sorted(fd.dependent)
        for i in range(len(rows)):
            for j in range(i + 1, len(rows)):
                if all(rows[i][c] == rows[j][c] for c in det_cols):
                    if not all(rows[i][c] == rows[j][c] for c in dep_cols):
                        return False
    return True


def _random_schema(rng: random.Random) -> RelationalSchema:
    n_attrs = rng.randint(2, 6)
    attrs = [chr(ord("A") + i) for i in range(n_attrs)]
    n_fds = rng.randint(1, 6)
    fds: Set[FunctionalDependency] = set()
    for _ in range(n_fds):
        det_size = rng.randint(1, max(1, n_attrs - 1))
        det = frozenset(rng.sample(attrs, det_size))
        remaining = [a for a in attrs if a not in det]
        if not remaining:
            dep = frozenset(rng.sample(attrs, 1))
        else:
            dep_size = rng.randint(1, min(2, len(remaining)))
            dep = frozenset(rng.sample(remaining, dep_size))
        fds.add(FunctionalDependency(det, dep))
    return RelationalSchema(attributes=frozenset(attrs), dependencies=frozenset(fds))


def test_closure_and_candidate_keys_match_brute_force() -> None:
    rng = random.Random(20261105)
    for iteration in range(150):
        schema = _random_schema(rng)
        attrs = sorted(schema.attributes)
        fds = list(schema.dependencies)

        for r in range(len(attrs) + 1):
            for comb in combinations(attrs, r):
                got = compute_attribute_closure(comb, fds)
                expected = _brute_force_closure(attrs, comb, fds)
                assert got == expected, (
                    f"Closure mismatch at seed=20261105 iter={iteration} "
                    f"subset={comb} fds={fds}: got={got}, expected={expected}"
                )

        got_keys = set(schema.candidate_keys())
        expected_keys = _brute_force_candidate_keys(attrs, fds)
        assert got_keys == expected_keys, (
            f"Candidate keys mismatch at seed=20261105 iter={iteration} "
            f"fds={fds}: got={got_keys}, expected={expected_keys}"
        )


def test_3nf_synthesis_is_dependency_preserving_and_lossless() -> None:
    rng = random.Random(20261106)
    for iteration in range(150):
        schema = _random_schema(rng)
        decomp = synthesize_3nf_bernstein(schema)
        assert len(decomp) >= 1
        assert frozenset().union(*decomp) == schema.attributes

        # Dependency preservation: every input FD is implied by the union of FDs projected onto the 3NF tables
        projected_union: List[FunctionalDependency] = []
        for comp in decomp:
            projected_union.extend(project_functional_dependencies(schema.dependencies, comp))

        for fd in schema.dependencies:
            closure = compute_attribute_closure(fd.determinant, projected_union)
            assert fd.dependent.issubset(closure), (
                f"3NF synthesis lost FD {fd} at seed=20261106 iter={iteration}: "
                f"decomp={decomp}, projected_union={projected_union}"
            )

        # Lossless join: when decomposed into >=2 tables, chase reaches a distinguished row
        if len(decomp) >= 2:
            chase = chase_join_dependency(
                heading=sorted(schema.attributes),
                dependencies=schema.dependencies,
                components=decomp,
            )
            assert chase.is_implied is True, (
                f"3NF synthesis is not lossless at seed=20261106 iter={iteration}: "
                f"schema={schema}, decomp={decomp}, chase={chase}"
            )
            assert chase.distinguished_row_index is not None
            dist_row = chase.final_tableau[chase.distinguished_row_index]
            assert all(dist_row[a] == f"a_{a}" for a in schema.attributes)


def test_bcnf_decomposition_is_lossless_and_in_bcnf() -> None:
    rng = random.Random(20261107)
    for iteration in range(150):
        schema = _random_schema(rng)
        leaves = decompose_bcnf_tree(schema)
        assert len(leaves) >= 1
        assert frozenset().union(*(s.attributes for s in leaves)) == schema.attributes

        for leaf in leaves:
            ok_bcnf, reason = check_bcnf(leaf)
            assert ok_bcnf is True, (
                f"BCNF leaf failed check_bcnf at seed=20261107 iter={iteration}: "
                f"leaf={leaf}, reason={reason}"
            )

        if len(leaves) >= 2:
            chase = chase_join_dependency(
                heading=sorted(schema.attributes),
                dependencies=schema.dependencies,
                components=[s.attributes for s in leaves],
            )
            assert chase.is_implied is True, (
                f"BCNF decomposition is lossy at seed=20261107 iter={iteration}: "
                f"schema={schema}, leaves={leaves}, chase={chase}"
            )
            assert chase.distinguished_row_index is not None


def test_chase_verdict_agrees_with_natural_join_and_spurious_tuple_witness() -> None:
    rng = random.Random(20261108)
    lossy_count = 0
    lossless_count = 0

    for iteration in range(150):
        schema = _random_schema(rng)
        attrs = sorted(schema.attributes)
        if len(attrs) < 3:
            continue

        # Build a random 2-way or 3-way decomposition covering all attributes
        k = rng.randint(1, len(attrs) - 1)
        part1 = set(attrs[:k])
        part2 = set(attrs[k:])
        overlap = rng.sample(attrs, rng.randint(1, len(attrs) - 1))
        comp1 = frozenset(part1 | set(overlap[:1]))
        comp2 = frozenset(part2 | set(overlap))
        if comp1 == schema.attributes or comp2 == schema.attributes:
            continue
        components = [comp1, comp2]

        chase = chase_join_dependency(
            heading=attrs,
            dependencies=schema.dependencies,
            components=components,
        )
        assert chase.is_implied in (True, False)

        # The final chase tableau is a relation over attrs
        final_rows = [{c: row[c] for c in attrs} for row in chase.final_tableau]
        joined_rows = _join_all_projections(final_rows, components)

        if chase.is_implied is False:
            lossy_count += 1
            assert _relation_satisfies_fds(final_rows, schema.dependencies), (
                f"Lossy counterexample tableau violates FDs at iter={iteration}: {final_rows}"
            )
            witness = chase.spurious_tuple_witness
            assert witness is not None, "Lossy chase must return a spurious_tuple_witness"
            witness_clean = {c: witness[c] for c in attrs}
            assert witness_clean not in final_rows, (
                f"Spurious witness {witness_clean} was already in the original relation {final_rows}"
            )
            assert witness_clean in joined_rows, (
                f"Spurious witness {witness_clean} did not appear in the join of projections {joined_rows}"
            )
        else:
            lossless_count += 1
            assert chase.spurious_tuple_witness is None
            dist_witness = {c: f"a_{c}" for c in attrs}
            assert dist_witness in final_rows
            # Run chase to full fixpoint (early_exit=False) to get an FD-valid instance I
            full_chase = chase_join_dependency(
                heading=attrs,
                dependencies=schema.dependencies,
                components=components,
                early_exit=False,
            )
            valid_instance = _project_relation(
                [{c: row[c] for c in attrs} for row in full_chase.final_tableau],
                attrs,
            )
            assert _relation_satisfies_fds(valid_instance, schema.dependencies)
            rejoined = _join_all_projections(valid_instance, components)
            assert len(rejoined) == len(valid_instance) and all(
                r in valid_instance for r in rejoined
            ), f"Lossless decomposition produced spurious tuples on {valid_instance}: {rejoined}"

    assert lossy_count >= 10, f"Expected at least 10 lossy cases, got {lossy_count}"
    assert lossless_count >= 10, f"Expected at least 10 lossless cases, got {lossless_count}"

