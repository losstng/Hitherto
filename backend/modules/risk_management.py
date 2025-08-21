"""Module 1: Risk Management - Supreme Court for trade proposals."""

import logging
import numpy as np
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel

from backend.schemas.core.schemas import (
    SignalBase, 
    TradeProposal,
    TradeAction,
    MessageEnvelope,
)
from .base import ModuleBase, ModuleResult, ModuleError


class RiskLimits(BaseModel):
    """Risk limit configuration."""
    max_position_size: float = 1000.0  # Maximum position size per asset
    max_portfolio_exposure: float = 10000.0  # Maximum total portfolio exposure
    max_var_per_asset: float = 0.05  # Maximum 95% VaR per asset (5%)
    max_portfolio_var: float = 0.15  # Maximum portfolio VaR (15%)
    max_correlation_exposure: float = 0.3  # Maximum exposure to correlated assets
    position_concentration_limit: float = 0.25  # Max 25% of portfolio in single asset


class RiskConfig(BaseModel):
    """Configuration for the Risk Management module."""
    limits: RiskLimits = RiskLimits()
    var_confidence_level: float = 0.95  # VaR confidence level
    var_lookback_days: int = 252  # Days of historical data for VaR calculation
    enable_kill_switch: bool = True
    correlation_threshold: float = 0.7  # Assets with correlation > this are considered correlated
    stress_test_scenarios: List[str] = ["market_crash", "interest_rate_shock", "liquidity_crisis"]


class RiskVerdict(BaseModel):
    """Risk evaluation verdict for a trade proposal."""
    verdict: str  # "APPROVED", "DOWNGRADED", "REJECTED"
    original_actions: List[TradeAction]
    adjusted_actions: Optional[List[TradeAction]] = None
    risk_flags: List[str] = []
    risk_metrics: Dict[str, float] = {}
    confidence: float = 1.0
    rationale: str = ""


class RiskSignal(SignalBase):
    """Risk management signal containing verdict."""
    message_type: str = "RiskSignal"
    
    def __init__(self, verdict: RiskVerdict, **kwargs):
        # Convert RiskVerdict to dict format for payload
        payload_dict = verdict.model_dump()
        super().__init__(payload=payload_dict, **kwargs)


class VaRCalculator:
    """Value at Risk calculator using historical simulation."""
    
    def __init__(self, confidence_level: float = 0.95):
        self.confidence_level = confidence_level
    
    def calculate_var(self, returns: List[float]) -> float:
        """Calculate VaR using historical simulation."""
        if not returns or len(returns) < 30:
            return 0.0
        
        returns_array = np.array(returns)
        var_quantile = 1 - self.confidence_level
        var = -np.percentile(returns_array, var_quantile * 100)
        
        return float(var)
    
    def calculate_cvar(self, returns: List[float]) -> float:
        """Calculate Conditional VaR (Expected Shortfall)."""
        if not returns or len(returns) < 30:
            return 0.0
        
        returns_array = np.array(returns)
        var_quantile = 1 - self.confidence_level
        var_threshold = np.percentile(returns_array, var_quantile * 100)
        
        # CVaR is the expected value of returns below the VaR threshold
        tail_returns = returns_array[returns_array <= var_threshold]
        if len(tail_returns) == 0:
            return 0.0
        
        cvar = -np.mean(tail_returns)
        return float(cvar)


class PortfolioRiskAnalyzer:
    """Analyzes portfolio-level risk metrics."""
    
    def __init__(self, config: RiskConfig):
        self.config = config
        self.var_calculator = VaRCalculator(config.var_confidence_level)
    
    def analyze_position_limits(self, actions: List[TradeAction]) -> Tuple[List[str], List[TradeAction]]:
        """Check position size limits and adjust if necessary."""
        flags = []
        adjusted_actions = []
        
        for action in actions:
            if action.size > self.config.limits.max_position_size:
                flags.append(f"{action.asset}: position size {action.size} exceeds limit {self.config.limits.max_position_size}")
                
                # Downgrade to maximum allowed size
                adjusted_action = TradeAction(
                    asset=action.asset,
                    action=action.action,
                    size=self.config.limits.max_position_size
                )
                adjusted_actions.append(adjusted_action)
            else:
                adjusted_actions.append(action)
        
        return flags, adjusted_actions
    
    def analyze_portfolio_exposure(self, actions: List[TradeAction]) -> List[str]:
        """Check total portfolio exposure limits."""
        flags = []
        
        total_exposure = sum(abs(action.size) for action in actions)
        if total_exposure > self.config.limits.max_portfolio_exposure:
            flags.append(f"Total portfolio exposure {total_exposure} exceeds limit {self.config.limits.max_portfolio_exposure}")
        
        return flags
    
    def analyze_concentration_risk(self, actions: List[TradeAction]) -> List[str]:
        """Check position concentration limits."""
        flags = []
        
        if not actions:
            return flags
        
        total_exposure = sum(abs(action.size) for action in actions)
        if total_exposure == 0:
            return flags
        
        for action in actions:
            concentration = abs(action.size) / total_exposure
            if concentration > self.config.limits.position_concentration_limit:
                flags.append(f"{action.asset}: concentration {concentration:.2%} exceeds limit {self.config.limits.position_concentration_limit:.2%}")
        
        return flags
    
    def analyze_var_limits(
        self, 
        actions: List[TradeAction], 
        historical_data: Optional[Dict[str, List[float]]] = None
    ) -> List[str]:
        """Check VaR limits using historical data."""
        flags = []
        
        if not historical_data:
            return flags
        
        for action in actions:
            if action.asset in historical_data:
                returns = historical_data[action.asset]
                var = self.var_calculator.calculate_var(returns)
                
                if var > self.config.limits.max_var_per_asset:
                    flags.append(f"{action.asset}: VaR {var:.2%} exceeds limit {self.config.limits.max_var_per_asset:.2%}")
        
        return flags


class RiskManagementModule(ModuleBase):
    """Module 1: Risk Management - Evaluates and controls trade proposals."""
    
    def __init__(self, communication=None):
        super().__init__("risk_management", "1.0.0", communication)
        self.risk_config: Optional[RiskConfig] = None
        self.portfolio_analyzer: Optional[PortfolioRiskAnalyzer] = None
        self.kill_switch_active = False
        self.historical_data: Dict[str, List[float]] = {}
        
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the Risk Management module."""
        try:
            # Parse configuration
            self.risk_config = RiskConfig(**config)
            
            # Initialize components
            self.portfolio_analyzer = PortfolioRiskAnalyzer(self.risk_config)
            
            # Load historical data if provided
            if "historical_data" in config:
                self.historical_data = config["historical_data"]
            
            self.activate()
            logging.info(f"Risk Management module initialized with config: {self.risk_config}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to initialize Risk Management module: {e}")
            return False
    
    def cleanup(self) -> None:
        """Clean up Risk Management module resources."""
        self.deactivate()
        logging.info("Risk Management module cleaned up")
    
    def get_subscribed_message_types(self) -> List[str]:
        """Subscribe to trade proposals for risk evaluation."""
        return ["TradeProposal"]
    
    def activate_kill_switch(self, reason: str) -> None:
        """Activate the kill switch to halt all trading."""
        self.kill_switch_active = True
        logging.critical(f"KILL SWITCH ACTIVATED: {reason}")
    
    def deactivate_kill_switch(self) -> None:
        """Deactivate the kill switch."""
        self.kill_switch_active = False
        logging.info("Kill switch deactivated")
    
    def evaluate_trade_proposal(self, proposal: TradeProposal) -> RiskVerdict:
        """Evaluate a trade proposal and return risk verdict."""
        
        if not self.risk_config or not self.portfolio_analyzer:
            return RiskVerdict(
                verdict="REJECTED",
                original_actions=proposal.payload.actions,
                risk_flags=["Risk module not properly initialized"],
                rationale="Risk system unavailable"
            )
        
        # Check kill switch
        if self.kill_switch_active:
            return RiskVerdict(
                verdict="REJECTED",
                original_actions=proposal.payload.actions,
                risk_flags=["Kill switch active"],
                rationale="Trading halted by kill switch"
            )
        
        actions = proposal.payload.actions
        all_flags = []
        risk_metrics = {}
        
        # 1. Analyze position limits
        position_flags, adjusted_actions = self.portfolio_analyzer.analyze_position_limits(actions)
        all_flags.extend(position_flags)
        
        # 2. Analyze portfolio exposure
        exposure_flags = self.portfolio_analyzer.analyze_portfolio_exposure(adjusted_actions)
        all_flags.extend(exposure_flags)
        
        # 3. Analyze concentration risk
        concentration_flags = self.portfolio_analyzer.analyze_concentration_risk(adjusted_actions)
        all_flags.extend(concentration_flags)
        
        # 4. Analyze VaR limits
        var_flags = self.portfolio_analyzer.analyze_var_limits(adjusted_actions, self.historical_data)
        all_flags.extend(var_flags)
        
        # 5. Calculate risk metrics
        total_exposure = sum(abs(action.size) for action in adjusted_actions)
        risk_metrics["total_exposure"] = total_exposure
        risk_metrics["num_positions"] = len([a for a in adjusted_actions if a.action != "HOLD"])
        
        # Calculate portfolio VaR if historical data available
        if self.historical_data:
            portfolio_var = self._calculate_portfolio_var(adjusted_actions)
            risk_metrics["portfolio_var"] = portfolio_var
            
            if portfolio_var > self.risk_config.limits.max_portfolio_var:
                all_flags.append(f"Portfolio VaR {portfolio_var:.2%} exceeds limit {self.risk_config.limits.max_portfolio_var:.2%}")
        
        # Determine verdict
        if not all_flags:
            verdict = "APPROVED"
            rationale = "All risk checks passed"
            final_actions = adjusted_actions
        elif len(adjusted_actions) != len(actions):
            # Some actions were downsized
            verdict = "DOWNGRADED" 
            rationale = f"Position sizes adjusted due to risk limits. Flags: {'; '.join(all_flags[:3])}"
            final_actions = adjusted_actions
        else:
            # Risk flags present but no adjustments possible
            verdict = "REJECTED"
            rationale = f"Risk limits breached. Flags: {'; '.join(all_flags[:3])}"
            final_actions = None
        
        return RiskVerdict(
            verdict=verdict,
            original_actions=actions,
            adjusted_actions=final_actions,
            risk_flags=all_flags,
            risk_metrics=risk_metrics,
            confidence=1.0,
            rationale=rationale
        )
    
    def _calculate_portfolio_var(self, actions: List[TradeAction]) -> float:
        """Calculate portfolio-level VaR (simplified correlation assumption)."""
        
        if not self.historical_data or not actions:
            return 0.0
        
        # Check if portfolio_analyzer is available
        if not self.portfolio_analyzer:
            return 0.0
        
        # Simplified portfolio VaR calculation
        # In practice, would use full covariance matrix
        individual_vars = []
        weights = []
        
        total_exposure = sum(abs(action.size) for action in actions)
        if total_exposure == 0:
            return 0.0
        
        for action in actions:
            if action.asset in self.historical_data:
                returns = self.historical_data[action.asset]
                var = self.portfolio_analyzer.var_calculator.calculate_var(returns)
                individual_vars.append(var)
                weights.append(abs(action.size) / total_exposure)
            else:
                individual_vars.append(0.0)
                weights.append(0.0)
        
        if not individual_vars:
            return 0.0
        
        # Simplified: assume average correlation of 0.3
        avg_correlation = 0.3
        portfolio_var = 0.0
        
        for i, (var_i, weight_i) in enumerate(zip(individual_vars, weights)):
            for j, (var_j, weight_j) in enumerate(zip(individual_vars, weights)):
                if i == j:
                    portfolio_var += (weight_i ** 2) * (var_i ** 2)
                else:
                    portfolio_var += 2 * weight_i * weight_j * var_i * var_j * avg_correlation
        
        return float(np.sqrt(max(0, portfolio_var)))
    
    def process(self, context: Dict[str, SignalBase]) -> ModuleResult:
        """Process incoming signals and evaluate trade proposals."""
        
        if not self.risk_config:
            return ModuleResult(
                success=False,
                errors=["Risk Management module not properly initialized"]
            )
        
        try:
            signals_generated = []
            warnings = []
            
            # Look for trade proposals in the context or from module communication
            trade_proposals = []
            
            # Check context for trade proposals
            for signal in context.values():
                if hasattr(signal, 'message_type') and signal.message_type == 'TradeProposal':
                    trade_proposals.append(signal)
            
            # Check incoming messages
            relevant_messages = self.communication.get_messages_for_module(self.name)
            for message in relevant_messages:
                if isinstance(message, TradeProposal):
                    trade_proposals.append(message)
            
            if not trade_proposals:
                # No trade proposals to evaluate
                return ModuleResult(
                    success=True,
                    signals=[],
                    warnings=["No trade proposals received for evaluation"],
                    metadata={"kill_switch_active": self.kill_switch_active}
                )
            
            # Evaluate each trade proposal
            for proposal in trade_proposals:
                verdict = self.evaluate_trade_proposal(proposal)
                
                # Create risk signal
                risk_signal = RiskSignal(
                    verdict=verdict,
                    timestamp=datetime.utcnow(),
                    origin_module="risk_management",
                    message_type="RiskSignal",
                    confidence=verdict.confidence
                )
                
                signals_generated.append(risk_signal)
                
                # Log verdict
                logging.info(f"Risk verdict for proposal: {verdict.verdict} - {verdict.rationale}")
                
                # Activate kill switch for severe violations
                if verdict.verdict == "REJECTED" and any("exceeds limit" in flag for flag in verdict.risk_flags):
                    if self.risk_config.enable_kill_switch:
                        self.activate_kill_switch(f"Multiple risk limits breached: {verdict.risk_flags}")
            
            return ModuleResult(
                success=True,
                signals=signals_generated,
                warnings=warnings,
                metadata={
                    "proposals_evaluated": len(trade_proposals),
                    "kill_switch_active": self.kill_switch_active,
                    "risk_metrics": {signal.payload.risk_metrics for signal in signals_generated if hasattr(signal.payload, 'risk_metrics')}
                }
            )
            
        except Exception as e:
            error_msg = f"Risk Management processing failed: {str(e)}"
            logging.error(error_msg)
            return ModuleResult(
                success=False,
                errors=[error_msg]
            )
    
    def update_historical_data(self, asset: str, returns: List[float]) -> None:
        """Update historical data for an asset."""
        self.historical_data[asset] = returns
    
    def get_risk_status(self) -> Dict[str, Any]:
        """Get current risk status and metrics."""
        status = {
            "kill_switch_active": self.kill_switch_active,
            "limits": self.risk_config.limits.model_dump() if self.risk_config else {},
            "historical_data_assets": list(self.historical_data.keys()),
            "module_status": self.status.value
        }
        return status
