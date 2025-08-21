"""Module 0: Command & Control (Overseer) - Central orchestrator and regime classifier."""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel

from backend.schemas.core.schemas import (
    SignalBase, 
    RegimeSignal, 
    RegimePayload,
    TradeProposal,
    TradeProposalPayload,
    TradeAction,
    SentimentSignal,
    TechnicalSignal,
    FundamentalSignal,
    AltDataSignal,
    SeasonalitySignal,
    IntermarketSignal,
)
from .base import ModuleBase, ModuleResult, ModuleError
from .database import DatabaseManager, RegimeType
from .llm_integration import EnhancedLLMReasoner, create_default_reasoner


class RegimeClassificationConfig(BaseModel):
    """Configuration for regime classification."""
    dwell_periods: int = 3  # Number of periods to confirm regime change
    confidence_threshold: float = 0.8
    default_regime: str = "bull"
    classification_method: str = "statistical"  # "statistical" or "llm"


class PlaybookConfig(BaseModel):
    """Configuration for strategy playbooks."""
    bull_weights: Dict[str, float] = {
        "sentiment": 0.3,
        "technical": 0.3, 
        "fundamental": 0.2,
        "altdata": 0.1,
        "seasonality": 0.1
    }
    bear_weights: Dict[str, float] = {
        "sentiment": 0.2,
        "technical": 0.4,
        "fundamental": 0.2,
        "altdata": 0.1,
        "seasonality": 0.1
    }
    sideways_weights: Dict[str, float] = {
        "sentiment": 0.2,
        "technical": 0.2,
        "fundamental": 0.3,
        "altdata": 0.15,
        "seasonality": 0.15
    }
    review_threshold: float = 100.0  # Size threshold requiring human review


class OverseerConfig(BaseModel):
    """Configuration for the Overseer module."""
    regime_config: RegimeClassificationConfig = RegimeClassificationConfig()
    playbook_config: PlaybookConfig = PlaybookConfig()
    enable_human_confirmation: bool = False
    max_actions_per_cycle: int = 5
    min_confidence_threshold: float = 0.6


class RegimeClassifier:
    """Regime classification with hysteresis and confirmation logic."""
    
    def __init__(self, config: RegimeClassificationConfig, db_manager: Optional[DatabaseManager] = None):
        self.config = config
        self.db_manager = db_manager
        self._current_regime = config.default_regime
        self._pending_regime: Optional[str] = None
        self._confirmation_count = 0
        self._awaiting_human_confirmation = False
        
        # Initialize with database state if available
        if self.db_manager:
            active_regime = self.db_manager.get_active_regime()
            if active_regime:
                self._current_regime = active_regime.regime_type.value
        
    @property
    def current_regime(self) -> str:
        """Get the currently active regime."""
        return self._current_regime
    
    @property
    def awaiting_confirmation(self) -> bool:
        """Check if regime change is pending human confirmation."""
        return self._awaiting_human_confirmation
    
    def _detect_regime_statistical(self) -> Tuple[str, float]:
        """Simple statistical regime detection based on time."""
        # Placeholder implementation - in real system would use HMM/Bayesian methods
        current_minute = datetime.utcnow().minute
        if current_minute < 20:
            return "bull", 0.85
        elif current_minute < 40:
            return "bear", 0.75
        else:
            return "sideways", 0.70
    
    def _detect_regime_llm(self, context: Dict[str, SignalBase], reasoner: Optional[EnhancedLLMReasoner] = None) -> Tuple[str, float]:
        """LLM-based regime detection using signal context."""
        if not reasoner or not reasoner.available:
            return self._detect_regime_statistical()
        
        try:
            # Prepare market data from signals
            market_data = {}
            recent_signals = []
            
            for signal in context.values():
                recent_signals.append(signal.model_dump())
                if hasattr(signal.payload, 'asset'):
                    asset = signal.payload.asset
                    if asset not in market_data:
                        market_data[asset] = {}
                    
                    # Extract relevant data based on signal type
                    if isinstance(signal, TechnicalSignal):
                        market_data[asset]['technical'] = signal.payload.signal_strength
                    elif isinstance(signal, SentimentSignal):
                        market_data[asset]['sentiment'] = signal.payload.sentiment_score
            
            # Get historical context from database
            historical_context = {}
            if self.db_manager:
                # Get recent regime history
                try:
                    # This would be implemented in a real system
                    historical_context = {"recent_regimes": "placeholder"}
                except Exception as e:
                    logging.warning(f"Failed to get historical context: {e}")
            
            # Use LLM to classify regime
            result = reasoner.classify_regime(market_data, recent_signals, historical_context)
            
            regime = result.get('regime', 'bull').lower()
            confidence = float(result.get('confidence', 0.5))
            
            logging.info(f"LLM regime classification: {regime} (confidence: {confidence:.2f})")
            return regime, confidence
            
        except Exception as e:
            logging.error(f"LLM regime classification failed: {e}")
            return self._detect_regime_statistical()
    
    def classify(self, context: Dict[str, SignalBase], reasoner: Optional[EnhancedLLMReasoner] = None) -> RegimeSignal:
        """Classify current market regime with confirmation logic."""
        
        # Detect potential regime
        if self.config.classification_method == "llm":
            candidate_regime, confidence = self._detect_regime_llm(context, reasoner)
        else:
            candidate_regime, confidence = self._detect_regime_statistical()
        
        # Apply hysteresis logic
        if candidate_regime != self._current_regime:
            if self._pending_regime != candidate_regime:
                # New regime candidate
                self._pending_regime = candidate_regime
                self._confirmation_count = 1
            else:
                # Same pending regime
                self._confirmation_count += 1
                
                if self._confirmation_count >= self.config.dwell_periods:
                    if confidence >= self.config.confidence_threshold:
                        # Auto-confirm regime change
                        self._current_regime = candidate_regime
                        self._pending_regime = None
                        self._confirmation_count = 0
                        self._awaiting_human_confirmation = False
                        
                        # Save to database
                        if self.db_manager:
                            try:
                                self.db_manager.update_regime(
                                    candidate_regime, confidence, self.config.classification_method
                                )
                            except Exception as e:
                                logging.error(f"Failed to save regime to database: {e}")
                        
                        logging.info(f"Regime change confirmed: {self._current_regime}")
                    else:
                        # Request human confirmation for low-confidence changes
                        self._awaiting_human_confirmation = True
        else:
            # Same as current regime
            self._pending_regime = None
            self._confirmation_count = 0
        
        payload = RegimePayload(
            regime_label=self._current_regime,
            confidence=confidence
        )
        
        return RegimeSignal(
            timestamp=datetime.utcnow(),
            origin_module="overseer",
            message_type="RegimeSignal",
            payload=payload,
            confidence=confidence
        )
    
    def confirm_pending_regime(self) -> bool:
        """Manually confirm pending regime change."""
        if self._awaiting_human_confirmation and self._pending_regime:
            self._current_regime = self._pending_regime
            self._pending_regime = None
            self._confirmation_count = 0
            self._awaiting_human_confirmation = False
            logging.info(f"Human confirmed regime change: {self._current_regime}")
            return True
        return False


class SignalFuser:
    """Fuses signals from multiple modules based on regime-specific weights."""
    
    def __init__(self, playbook_config: PlaybookConfig):
        self.playbook_config = playbook_config
    
    def _get_regime_weights(self, regime: str) -> Dict[str, float]:
        """Get module weights for the given regime."""
        if regime == "bull":
            return self.playbook_config.bull_weights
        elif regime == "bear":
            return self.playbook_config.bear_weights
        elif regime == "sideways":
            return self.playbook_config.sideways_weights
        else:
            # Default to bull weights
            return self.playbook_config.bull_weights
    
    def _extract_signal_score(self, signal: SignalBase) -> float:
        """Extract numerical score from a signal."""
        if isinstance(signal, SentimentSignal):
            return signal.payload.sentiment_score
        elif isinstance(signal, TechnicalSignal):
            # Convert signal strength to score
            strength_map = {"bullish": 1.0, "bearish": -1.0, "neutral": 0.0}
            return strength_map.get(signal.payload.signal_strength.lower(), 0.0)
        elif isinstance(signal, FundamentalSignal):
            return signal.payload.mispricing_percent / 100.0
        elif isinstance(signal, AltDataSignal):
            return signal.payload.value
        elif isinstance(signal, SeasonalitySignal):
            return signal.payload.bias
        elif isinstance(signal, IntermarketSignal):
            return signal.payload.value
        else:
            return 0.0
    
    def fuse_signals(
        self, 
        signals: List[SignalBase], 
        regime: str
    ) -> Dict[str, float]:
        """Fuse signals into asset-level scores based on regime weights."""
        
        weights = self._get_regime_weights(regime)
        asset_scores: Dict[str, float] = {}
        
        for signal in signals:
            # Get asset from signal payload
            asset = getattr(signal.payload, 'asset', None)
            if not asset:
                continue
            
            # Get module weight
            module_weight = weights.get(signal.origin_module, 0.0)
            
            # Extract signal score
            signal_score = self._extract_signal_score(signal)
            
            # Apply confidence weighting
            confidence = signal.confidence or 1.0
            weighted_score = module_weight * signal_score * confidence
            
            # Accumulate scores per asset
            if asset not in asset_scores:
                asset_scores[asset] = 0.0
            asset_scores[asset] += weighted_score
        
        return asset_scores


class OverseerModule(ModuleBase):
    """Module 0: Command & Control - Central orchestrator and regime classifier."""
    
    def __init__(self, communication=None):
        super().__init__("overseer", "1.0.0", communication)
        self.overseer_config: Optional[OverseerConfig] = None
        self.regime_classifier: Optional[RegimeClassifier] = None
        self.signal_fuser: Optional[SignalFuser] = None
        self.db_manager: Optional[DatabaseManager] = None
        self.llm_reasoner: Optional[EnhancedLLMReasoner] = None
        
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the Overseer module."""
        try:
            # Parse configuration
            self.overseer_config = OverseerConfig(**config)
            
            # Initialize database manager
            self.db_manager = DatabaseManager()
            
            # Initialize LLM reasoner
            self.llm_reasoner = create_default_reasoner()
            
            # Initialize components
            self.regime_classifier = RegimeClassifier(
                self.overseer_config.regime_config, 
                self.db_manager
            )
            self.signal_fuser = SignalFuser(self.overseer_config.playbook_config)
            
            self.activate()
            logging.info(f"Overseer module initialized with config: {self.overseer_config}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to initialize Overseer module: {e}")
            return False
    
    def cleanup(self) -> None:
        """Clean up Overseer module resources."""
        self.deactivate()
        logging.info("Overseer module cleaned up")
    
    def get_subscribed_message_types(self) -> List[str]:
        """Subscribe to all signal types for fusion."""
        return [
            "SentimentSignal",
            "TechnicalSignal", 
            "FundamentalSignal",
            "AltDataSignal",
            "SeasonalitySignal",
            "IntermarketSignal"
        ]
    
    def _generate_trade_actions(
        self, 
        asset_scores: Dict[str, float], 
        regime: str
    ) -> List[TradeAction]:
        """Generate trade actions based on fused asset scores."""
        
        if not self.overseer_config:
            return []
        
        actions = []
        
        # Sort assets by absolute score (highest conviction first)
        sorted_assets = sorted(
            asset_scores.items(), 
            key=lambda x: abs(x[1]), 
            reverse=True
        )
        
        # Limit number of actions
        max_actions = self.overseer_config.max_actions_per_cycle
        
        for asset, score in sorted_assets[:max_actions]:
            # Skip low-confidence signals
            if abs(score) < self.overseer_config.min_confidence_threshold:
                continue
            
            # Determine action and size based on score
            if score > 0:
                action = "BUY"
            elif score < 0:
                action = "SELL"
            else:
                continue
            
            # Size proportional to conviction
            base_size = 100
            size = base_size * min(abs(score), 1.0)
            
            actions.append(TradeAction(
                asset=asset,
                action=action,
                size=round(size, 2)
            ))
        
        # Add HOLD action if no trades generated
        if not actions:
            actions.append(TradeAction(
                asset="CASH",
                action="HOLD", 
                size=0.0
            ))
        
        return actions
    
    def _generate_rationale(
        self, 
        regime: str, 
        asset_scores: Dict[str, float], 
        actions: List[TradeAction]
    ) -> List[str]:
        """Generate human-readable rationale for trade proposal."""
        
        rationale = [
            f"Market regime classified as: {regime}",
            f"Asset scores: {asset_scores}",
            f"Generated {len(actions)} trade actions"
        ]
        
        for action in actions:
            if action.action != "HOLD":
                score = asset_scores.get(action.asset, 0.0)
                rationale.append(
                    f"{action.action} {action.size} {action.asset} "
                    f"(score: {score:.2f})"
                )
        
        return rationale
    
    def process(self, context: Dict[str, SignalBase]) -> ModuleResult:
        """Process signals and generate trade proposals."""
        
        if not self.overseer_config or not self.regime_classifier or not self.signal_fuser:
            return ModuleResult(
                success=False,
                errors=["Overseer module not properly initialized"]
            )
        
        try:
            # 1. Classify current market regime
            regime_signal = self.regime_classifier.classify(context, self.llm_reasoner)
            current_regime = self.regime_classifier.current_regime
            
            # 2. Collect all signals from other modules
            signals = [signal for signal in context.values() if signal.origin_module != "overseer"]
            
            # 3. Determine trade actions (use LLM if available, fallback to rule-based)
            if self.llm_reasoner and self.llm_reasoner.available:
                # Use LLM for trade decisions
                playbook_weights = self.signal_fuser._get_regime_weights(current_regime)
                actions, rationale = self.llm_reasoner.decide_trades(
                    current_regime, signals, playbook_weights
                )
            else:
                # Fallback to rule-based approach
                asset_scores = self.signal_fuser.fuse_signals(signals, current_regime)
                actions = self._generate_trade_actions(asset_scores, current_regime)
                rationale = self._generate_rationale(current_regime, asset_scores, actions)
            
            # 4. Create trade proposal
            requires_human = (
                self.overseer_config.enable_human_confirmation or
                any(action.size > self.overseer_config.playbook_config.review_threshold for action in actions) or
                self.regime_classifier.awaiting_confirmation
            )
            
            proposal_payload = TradeProposalPayload(
                regime=current_regime,
                actions=actions,
                rationale=rationale,
                requires_human=requires_human,
                status="PENDING_REVIEW" if requires_human else "AUTO_APPROVED"
            )
            
            trade_proposal = TradeProposal(
                timestamp=datetime.utcnow(),
                origin_module="overseer",
                message_type="TradeProposal",
                payload=proposal_payload
            )
            
            # 5. Save to database
            try:
                if self.db_manager:
                    # Save signals to database
                    for signal in [regime_signal] + signals:
                        try:
                            # Get module ID (simplified - in real implementation would maintain module registry)
                            module_id = 1  # Placeholder
                            self.db_manager.save_signal(signal, module_id)
                        except Exception as e:
                            logging.warning(f"Failed to save signal to database: {e}")
                    
                    # Save proposal to database
                    self.db_manager.save_proposal(
                        proposal_payload.model_dump(), 
                        "overseer"
                    )
            except Exception as e:
                logging.error(f"Database operations failed: {e}")
            
            return ModuleResult(
                success=True,
                signals=[regime_signal],  # Only include signals, not proposals
                metadata={
                    "regime": current_regime,
                    "signals_processed": len(signals),
                    "awaiting_regime_confirmation": self.regime_classifier.awaiting_confirmation,
                    "trade_proposal": trade_proposal.model_dump(),  # Include as metadata
                    "llm_used": self.llm_reasoner and self.llm_reasoner.available,
                    "proposal_summary": self._generate_proposal_summary(trade_proposal) if self.llm_reasoner else "No LLM summary available"
                }
            )
            
        except Exception as e:
            error_msg = f"Overseer processing failed: {str(e)}"
            logging.error(error_msg)
            return ModuleResult(
                success=False,
                errors=[error_msg]
            )
    
    def _generate_proposal_summary(self, proposal: TradeProposal) -> str:
        """Generate human-readable summary of the proposal."""
        if self.llm_reasoner and self.llm_reasoner.available:
            return self.llm_reasoner.summarize_proposal(proposal)
        else:
            # Fallback summary
            actions = proposal.payload.actions
            if not actions:
                return "No actions proposed"
            
            action_parts = []
            for action in actions:
                if action.action != "HOLD":
                    action_parts.append(f"{action.action} {action.size} {action.asset}")
            
            return f"Proposed: {'; '.join(action_parts)}" if action_parts else "Hold all positions"
    
    def confirm_regime_change(self) -> bool:
        """Manually confirm pending regime change."""
        if self.regime_classifier:
            return self.regime_classifier.confirm_pending_regime()
        return False
    
    def get_current_regime(self) -> str:
        """Get the current market regime."""
        if self.regime_classifier:
            return self.regime_classifier.current_regime
        return "unknown"
