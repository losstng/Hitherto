"""Demo script showing how to use the Module Communication Protocol."""

import logging
import time
from datetime import datetime
from typing import Dict, Any

from backend.modules import (
    OverseerModule, 
    RiskManagementModule, 
    create_default_protocol,
    ModuleResult
)
from backend.schemas.core.schemas import (
    SentimentSignal,
    SentimentPayload,
    TechnicalSignal, 
    TechnicalPayload,
    SignalBase
)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_mock_sentiment_signal(asset: str, score: float) -> SentimentSignal:
    """Create a mock sentiment signal for testing."""
    payload = SentimentPayload(
        asset=asset,
        sentiment_score=score,
        summary=f"Sentiment analysis for {asset}",
        confidence=0.85,
        rationale=f"Based on news analysis, sentiment score is {score}"
    )
    
    return SentimentSignal(
        timestamp=datetime.utcnow(),
        origin_module="sentiment",
        message_type="SentimentSignal",
        payload=payload,
        confidence=0.85
    )


def create_mock_technical_signal(asset: str, strength: str) -> TechnicalSignal:
    """Create a mock technical signal for testing."""
    payload = TechnicalPayload(
        asset=asset,
        indicator="RSI",
        value=75.0 if strength == "bullish" else 25.0,
        signal_strength=strength
    )
    
    return TechnicalSignal(
        timestamp=datetime.utcnow(),
        origin_module="technical", 
        message_type="TechnicalSignal",
        payload=payload,
        confidence=0.9
    )


def demo_module_communication():
    """Demonstrate the module communication protocol."""
    
    logger.info("Starting Hitherto Module Communication Protocol Demo")
    
    # 1. Create communication protocol
    protocol = create_default_protocol()
    
    # 2. Configure modules
    overseer_config = {
        "regime_config": {
            "dwell_periods": 2,
            "confidence_threshold": 0.7,
            "default_regime": "bull"
        },
        "playbook_config": {
            "bull_weights": {
                "sentiment": 0.4,
                "technical": 0.3,
                "fundamental": 0.3
            },
            "review_threshold": 50.0
        },
        "max_actions_per_cycle": 3,
        "min_confidence_threshold": 0.5
    }
    
    risk_config = {
        "limits": {
            "max_position_size": 100.0,
            "max_portfolio_exposure": 500.0,
            "max_var_per_asset": 0.1
        },
        "enable_kill_switch": True,
        "historical_data": {
            "AAPL": [-0.02, 0.01, -0.015, 0.025, -0.01] * 50,  # Mock returns
            "GOOGL": [-0.025, 0.015, -0.01, 0.02, -0.005] * 50,
            "TSLA": [-0.05, 0.03, -0.02, 0.04, -0.015] * 50
        }
    }
    
    # 3. Create and register modules
    overseer = OverseerModule()
    risk_mgmt = RiskManagementModule()
    
    success = protocol.register_module(overseer, overseer_config)
    logger.info(f"Overseer module registration: {'SUCCESS' if success else 'FAILED'}")
    
    success = protocol.register_module(risk_mgmt, risk_config)
    logger.info(f"Risk Management module registration: {'SUCCESS' if success else 'FAILED'}")
    
    # 4. Create mock market signals
    mock_signals = {
        "sentiment_aapl": create_mock_sentiment_signal("AAPL", 0.7),
        "sentiment_googl": create_mock_sentiment_signal("GOOGL", -0.3),
        "technical_aapl": create_mock_technical_signal("AAPL", "bullish"),
        "technical_googl": create_mock_technical_signal("GOOGL", "bearish"),
        "technical_tsla": create_mock_technical_signal("TSLA", "bullish")
    }
    
    logger.info(f"Created {len(mock_signals)} mock market signals")
    
    # 5. Execute multiple cycles to demonstrate signal flow
    for cycle in range(3):
        logger.info(f"\n{'='*50}")
        logger.info(f"EXECUTING CYCLE {cycle + 1}")
        logger.info(f"{'='*50}")
        
        # Modify signals slightly each cycle to show evolution
        for signal in mock_signals.values():
            if hasattr(signal.payload, 'sentiment_score'):
                # Add some noise to sentiment
                signal.payload.sentiment_score += (cycle * 0.1 - 0.1)
            elif hasattr(signal.payload, 'value'):
                # Modify technical indicator values
                signal.payload.value += (cycle * 2.0)
        
        # Execute the cycle
        cycle_result = protocol.execute_cycle(mock_signals)
        
        # Display results
        logger.info(f"Cycle {cycle + 1} Results:")
        logger.info(f"  Duration: {cycle_result.get('cycle_duration_seconds', 0):.2f}s")
        logger.info(f"  Signals Generated: {cycle_result.get('signals_generated', 0)}")
        logger.info(f"  Modules Executed: {cycle_result.get('modules_executed', 0)}")
        
        # Show module-specific results
        module_results = cycle_result.get('module_results', {})
        for module_name, result in module_results.items():
            if result.success:
                logger.info(f"  {module_name}: SUCCESS - {len(result.signals)} signals")
                if result.metadata:
                    for key, value in result.metadata.items():
                        if key == 'trade_proposal':
                            proposal = value.get('payload', {})
                            actions = proposal.get('actions', [])
                            logger.info(f"    Trade Actions: {len(actions)} proposed")
                            for action in actions[:2]:  # Show first 2 actions
                                logger.info(f"      {action}")
                        elif key in ['regime', 'asset_scores']:
                            logger.info(f"    {key}: {value}")
            else:
                logger.info(f"  {module_name}: FAILED - {result.errors}")
        
        # Add delay between cycles
        if cycle < 2:
            time.sleep(1)
    
    # 6. Show final statistics
    logger.info(f"\n{'='*50}")
    logger.info("FINAL STATISTICS")
    logger.info(f"{'='*50}")
    
    health_status = protocol.get_module_health()
    for module_name, health in health_status.items():
        logger.info(f"{module_name} Health: {health}")
    
    comm_stats = protocol.get_communication_stats()
    logger.info(f"Communication Stats: {comm_stats}")
    
    # 7. Demonstrate risk override
    logger.info(f"\n{'='*30}")
    logger.info("TESTING RISK OVERRIDE")
    logger.info(f"{'='*30}")
    
    # Create a high-risk signal that should trigger risk controls
    high_risk_signal = create_mock_sentiment_signal("TSLA", 0.9)
    high_risk_signal.payload.confidence = 0.95
    
    # Modify config to create large position (if overseer is properly initialized)
    if overseer.overseer_config:
        overseer.overseer_config.min_confidence_threshold = 0.3
    
    # Execute one more cycle
    risk_test_signals = {
        "high_risk_sentiment": high_risk_signal,
        "high_risk_technical": create_mock_technical_signal("TSLA", "bullish")
    }
    
    risk_cycle_result = protocol.execute_cycle(risk_test_signals)
    logger.info("Risk override test completed")
    
    # 8. Shutdown
    logger.info("\nShutting down protocol...")
    protocol.shutdown()
    logger.info("Demo completed successfully!")


if __name__ == "__main__":
    demo_module_communication()
