"""Local heuristics for quick transaction classification.

This module now delegates to :class:`~bankcleanr.rules.manager.Manager`
so that all classification uses the same code path as the LLM backed
classifier.  Previously the logic here duplicated the regex lookups which
meant any refactor in :mod:`manager` had to be mirrored.  By funnelling
everything through ``Manager`` we ensure the heuristics used by the
auto-learning LLM service are identical to those used for the
"heuristics only" mode.
"""

from typing import Iterable, List

from bankcleanr.transaction import normalise
from .manager import Manager


def classify_transactions(transactions: Iterable) -> List[str]:
    """Classify transactions locally using regex patterns.

    The input transactions can be dictionaries, dataclass instances or
    :class:`~bankcleanr.transaction.Transaction` objects.  They are first
    normalised and then passed to :class:`Manager` for classification.
    """

    manager = Manager()
    tx_objs = [normalise(tx) for tx in transactions]
    return manager.classify(tx_objs)
