"""Service layer initialisation for Hitherto backend."""

from .coordinator import ModuleCoordinator, ModuleProtocol  # noqa: F401
from .technical import TechnicalAnalyzer  # noqa: F401
from .altdata import AltDataAnalyzer  # noqa: F401
from .fundamentals import FundamentalsAnalyzer  # noqa: F401
from .seasonality import SeasonalityAnalyzer  # noqa: F401
from .intermarket import IntermarketAnalyzer  # noqa: F401


def build_coordinator() -> ModuleCoordinator:
    """Return a coordinator with modules in dependency order."""

    modules = [
        TechnicalAnalyzer(),
        AltDataAnalyzer(),
        FundamentalsAnalyzer(),
        SeasonalityAnalyzer(),
        IntermarketAnalyzer(),
    ]
    return ModuleCoordinator(modules)


__all__ = [
    "ModuleCoordinator",
    "ModuleProtocol",
    "TechnicalAnalyzer",
    "AltDataAnalyzer",
    "FundamentalsAnalyzer",
    "SeasonalityAnalyzer",
    "IntermarketAnalyzer",
    "build_coordinator",
]
