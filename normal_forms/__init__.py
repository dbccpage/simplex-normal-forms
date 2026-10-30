"""Normal forms infrastructure layer: SQLite storage, YAML contract parsing, and multi-hop composition.

AuthorityEffect: None.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from normal_forms.catalog import check_catalog
    from normal_forms.catalog import check_document
    from normal_forms.catalog import validate_contract
    from normal_forms.contract_model import Finding
    from normal_forms.contract_model import load_yaml
    from normal_forms.contract_paths import CONTRACTS_DIR
    from normal_forms.contract_paths import NORMAL_FORMS_DIR
    from normal_forms.contract_paths import STANDARD_PATH
    from normal_forms.db_context import NormalFormsDbContext
    from normal_forms.evaluator import NormalFormsEvaluator
    from normal_forms.migrate_contract import migrate_v0_to_v1
    from normal_forms.multi_hop_composition import (
        CochainExtremaQuantileStageReceipt,
        CodaMurHopSpec,
        ExtendedMultiHopCompositionReceipt,
        MultiHopCompositionReceipt,
        ObserverPosetStageReceipt,
        SalesCochainCdcSpec,
        WatermarkSpec,
        WatermarkedStepReceipt,
        WatermarkedStreamReceipt,
        build_sealed_loss_ledger,
        decode_composite_group_key,
        encode_composite_group_key,
        evaluate_watermarked_cdc_stream_with_observer_poset,
        run_extended_multi_hop_pipeline,
        run_multi_hop_pipeline,
    )
    from normal_forms.sales_cochain import (
        rebalance_quantile_cochain,
        verify_quantile_cochain_invariants,
    )
    from normal_forms._golden_nfs import NormalFormContract
    from normal_forms._golden_nfs import NormalFormContractMetaSchema
    from normal_forms._golden_nfs import NormalFormFoundationalDefinitions
    from normal_forms._golden_nfs import NormalFormStandard
    from normal_forms._golden_nfs import QuadrilateralCriterion
    from normal_forms._golden_nfs import normal_form_contract_schema
    from normal_forms._golden_nfs import normal_form_definitions
    from normal_forms._golden_nfs import normal_form_standard_schema

__all__ = [
    "NormalFormsDbContext",
    "NormalFormsEvaluator",
    "NormalFormContract",
    "NormalFormContractMetaSchema",
    "NormalFormFoundationalDefinitions",
    "QuadrilateralCriterion",
    "NormalFormStandard",
    "normal_form_contract_schema",
    "normal_form_definitions",
    "normal_form_standard_schema",
    "NORMAL_FORMS_DIR",
    "CONTRACTS_DIR",
    "STANDARD_PATH",
    "Finding",
    "load_yaml",
    "validate_contract",
    "check_document",
    "check_catalog",
    "migrate_v0_to_v1",
    "CochainExtremaQuantileStageReceipt",
    "CodaMurHopSpec",
    "ExtendedMultiHopCompositionReceipt",
    "MultiHopCompositionReceipt",
    "ObserverPosetStageReceipt",
    "SalesCochainCdcSpec",
    "WatermarkSpec",
    "WatermarkedStepReceipt",
    "WatermarkedStreamReceipt",
    "build_sealed_loss_ledger",
    "decode_composite_group_key",
    "encode_composite_group_key",
    "evaluate_watermarked_cdc_stream_with_observer_poset",
    "rebalance_quantile_cochain",
    "run_extended_multi_hop_pipeline",
    "run_multi_hop_pipeline",
    "verify_quantile_cochain_invariants",
]

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    "check_catalog": ("normal_forms.catalog", "check_catalog"),
    "check_document": ("normal_forms.catalog", "check_document"),
    "validate_contract": ("normal_forms.catalog", "validate_contract"),
    "Finding": ("normal_forms.contract_model", "Finding"),
    "load_yaml": ("normal_forms.contract_model", "load_yaml"),
    "CONTRACTS_DIR": ("normal_forms.contract_paths", "CONTRACTS_DIR"),
    "NORMAL_FORMS_DIR": ("normal_forms.contract_paths", "NORMAL_FORMS_DIR"),
    "STANDARD_PATH": ("normal_forms.contract_paths", "STANDARD_PATH"),
    "NormalFormsDbContext": ("normal_forms.db_context", "NormalFormsDbContext"),
    "NormalFormsEvaluator": ("normal_forms.evaluator", "NormalFormsEvaluator"),
    "migrate_v0_to_v1": ("normal_forms.migrate_contract", "migrate_v0_to_v1"),
    "CochainExtremaQuantileStageReceipt": (
        "normal_forms.multi_hop_composition",
        "CochainExtremaQuantileStageReceipt",
    ),
    "CodaMurHopSpec": ("normal_forms.multi_hop_composition", "CodaMurHopSpec"),
    "ExtendedMultiHopCompositionReceipt": (
        "normal_forms.multi_hop_composition",
        "ExtendedMultiHopCompositionReceipt",
    ),
    "MultiHopCompositionReceipt": ("normal_forms.multi_hop_composition", "MultiHopCompositionReceipt"),
    "ObserverPosetStageReceipt": ("normal_forms.multi_hop_composition", "ObserverPosetStageReceipt"),
    "SalesCochainCdcSpec": ("normal_forms.multi_hop_composition", "SalesCochainCdcSpec"),
    "WatermarkSpec": ("normal_forms.multi_hop_composition", "WatermarkSpec"),
    "WatermarkedStepReceipt": ("normal_forms.multi_hop_composition", "WatermarkedStepReceipt"),
    "WatermarkedStreamReceipt": ("normal_forms.multi_hop_composition", "WatermarkedStreamReceipt"),
    "build_sealed_loss_ledger": ("normal_forms.multi_hop_composition", "build_sealed_loss_ledger"),
    "decode_composite_group_key": ("normal_forms.multi_hop_composition", "decode_composite_group_key"),
    "encode_composite_group_key": ("normal_forms.multi_hop_composition", "encode_composite_group_key"),
    "evaluate_watermarked_cdc_stream_with_observer_poset": (
        "normal_forms.multi_hop_composition",
        "evaluate_watermarked_cdc_stream_with_observer_poset",
    ),
    "rebalance_quantile_cochain": ("normal_forms.sales_cochain", "rebalance_quantile_cochain"),
    "run_extended_multi_hop_pipeline": (
        "normal_forms.multi_hop_composition",
        "run_extended_multi_hop_pipeline",
    ),
    "run_multi_hop_pipeline": ("normal_forms.multi_hop_composition", "run_multi_hop_pipeline"),
    "verify_quantile_cochain_invariants": (
        "normal_forms.sales_cochain",
        "verify_quantile_cochain_invariants",
    ),
    "NormalFormContract": ("normal_forms._golden_nfs", "NormalFormContract"),
    "NormalFormContractMetaSchema": ("normal_forms._golden_nfs", "NormalFormContractMetaSchema"),
    "NormalFormFoundationalDefinitions": ("normal_forms._golden_nfs", "NormalFormFoundationalDefinitions"),
    "NormalFormStandard": ("normal_forms._golden_nfs", "NormalFormStandard"),
    "QuadrilateralCriterion": ("normal_forms._golden_nfs", "QuadrilateralCriterion"),
    "normal_form_contract_schema": ("normal_forms._golden_nfs", "normal_form_contract_schema"),
    "normal_form_definitions": ("normal_forms._golden_nfs", "normal_form_definitions"),
    "normal_form_standard_schema": ("normal_forms._golden_nfs", "normal_form_standard_schema"),
}


def __getattr__(name: str) -> Any:
    target = _LAZY_IMPORTS.get(name)
    if target is not None:
        mod_name, attr_name = target
        mod = importlib.import_module(mod_name, __name__)
        val = getattr(mod, attr_name)
        globals()[name] = val
        return val
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
