"""Golden normal forms schema, definitions, and SQL specifications."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from normal_forms._golden_nfs.normal_form_contract_schema import NormalFormContract
    from normal_forms._golden_nfs.normal_form_contract_schema import NormalFormContractMetaSchema
    from normal_forms._golden_nfs.normal_form_definitions import NormalFormFoundationalDefinitions
    from normal_forms._golden_nfs.normal_form_definitions import QuadrilateralCriterion
    from normal_forms._golden_nfs.normal_form_standard_schema import NormalFormStandard

__all__ = [
    'NormalFormContract',
    'NormalFormContractMetaSchema',
    'NormalFormFoundationalDefinitions',
    'QuadrilateralCriterion',
    'NormalFormStandard',
    'normal_form_contract_schema',
    'normal_form_definitions',
    'normal_form_standard_schema',
]

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'NormalFormContract': ('normal_forms._golden_nfs.normal_form_contract_schema', 'NormalFormContract'),
    'NormalFormContractMetaSchema': ('normal_forms._golden_nfs.normal_form_contract_schema', 'NormalFormContractMetaSchema'),
    'NormalFormFoundationalDefinitions': ('normal_forms._golden_nfs.normal_form_definitions', 'NormalFormFoundationalDefinitions'),
    'QuadrilateralCriterion': ('normal_forms._golden_nfs.normal_form_definitions', 'QuadrilateralCriterion'),
    'NormalFormStandard': ('normal_forms._golden_nfs.normal_form_standard_schema', 'NormalFormStandard'),
}

_LAZY_SUBMODULES: dict[str, str] = {
    'normal_form_contract_schema': 'normal_forms._golden_nfs.normal_form_contract_schema',
    'normal_form_definitions': 'normal_forms._golden_nfs.normal_form_definitions',
    'normal_form_standard_schema': 'normal_forms._golden_nfs.normal_form_standard_schema',
}


def __getattr__(name: str) -> Any:
    submod = _LAZY_SUBMODULES.get(name)
    if submod is not None:
        mod = importlib.import_module(submod, __name__)
        globals()[name] = mod
        return mod
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
