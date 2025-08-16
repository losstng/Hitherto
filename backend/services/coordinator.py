import logging
from dataclasses import dataclass, field
from typing import Dict, List, Protocol

from backend.schemas import SignalBase


class ModuleProtocol(Protocol):
    """Protocol each signal module must follow."""

    name: str

    def generate(self, context: Dict[str, SignalBase]) -> SignalBase:
        """Produce a signal given the current context."""
        ...


@dataclass
class ModuleCoordinator:
    """Sequentially executes registered modules and stores their signals."""

    modules: List[ModuleProtocol] = field(default_factory=list)
    context: Dict[str, SignalBase] = field(default_factory=dict)

    def register(self, module: ModuleProtocol) -> None:
        self.modules.append(module)

    def run(self) -> List[SignalBase]:
        signals: List[SignalBase] = []
        for module in self.modules:
            try:
                signal = module.generate(self.context)
            except Exception as exc:  # pragma: no cover - logging path
                logging.exception("module %s failed: %s", module.name, exc)
                continue
            signals.append(signal)
            self.context[module.name] = signal
        return signals
