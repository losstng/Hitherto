"""Basic test for the module system implementation."""

import sys
import traceback
from datetime import datetime

def test_module_imports():
    """Test that all modules can be imported correctly."""
    try:
        from backend.modules import (
            ModuleBase, 
            ModuleResult, 
            ModuleError,
            OverseerModule,
            RiskManagementModule,
            create_default_protocol
        )
        print("✓ All module imports successful")
        return True
    except Exception as e:
        print(f"✗ Module import failed: {e}")
        traceback.print_exc()
        return False


def test_basic_module_creation():
    """Test basic module creation and initialization."""
    try:
        from backend.modules import OverseerModule, RiskManagementModule
        
        # Test Overseer Module
        overseer = OverseerModule()
        config = {
            "regime_config": {"default_regime": "bull"},
            "playbook_config": {},
            "max_actions_per_cycle": 5,
            "min_confidence_threshold": 0.5
        }
        
        success = overseer.initialize(config)
        if not success:
            print("✗ Overseer module initialization failed")
            return False
        
        print("✓ Overseer module created and initialized")
        
        # Test Risk Management Module  
        risk_mgmt = RiskManagementModule()
        risk_config = {
            "limits": {"max_position_size": 100.0},
            "enable_kill_switch": True
        }
        
        success = risk_mgmt.initialize(risk_config)
        if not success:
            print("✗ Risk Management module initialization failed")
            return False
            
        print("✓ Risk Management module created and initialized")
        return True
        
    except Exception as e:
        print(f"✗ Module creation failed: {e}")
        traceback.print_exc()
        return False


def test_communication_protocol():
    """Test the communication protocol setup."""
    try:
        from backend.modules import create_default_protocol
        
        protocol = create_default_protocol()
        
        stats = protocol.get_communication_stats()
        print(f"✓ Communication protocol created - {stats}")
        
        protocol.shutdown()
        print("✓ Communication protocol shutdown successful")
        return True
        
    except Exception as e:
        print(f"✗ Communication protocol test failed: {e}")
        traceback.print_exc()
        return False


def test_signal_creation():
    """Test creating basic signals."""
    try:
        from backend.schemas.core.schemas import (
            SentimentSignal,
            SentimentPayload,
            TechnicalSignal,
            TechnicalPayload
        )
        
        # Test Sentiment Signal
        sentiment_payload = SentimentPayload(
            asset="AAPL",
            sentiment_score=0.7,
            summary="Positive sentiment",
            confidence=0.8
        )
        
        sentiment_signal = SentimentSignal(
            timestamp=datetime.utcnow(),
            origin_module="test",
            message_type="SentimentSignal",
            payload=sentiment_payload,
            confidence=0.8
        )
        
        print(f"✓ Sentiment signal created: {sentiment_signal.payload.asset}")
        
        # Test Technical Signal
        technical_payload = TechnicalPayload(
            asset="AAPL",
            indicator="RSI",
            value=70.0,
            signal_strength="bullish"
        )
        
        technical_signal = TechnicalSignal(
            timestamp=datetime.utcnow(),
            origin_module="test",
            message_type="TechnicalSignal", 
            payload=technical_payload,
            confidence=0.9
        )
        
        print(f"✓ Technical signal created: {technical_signal.payload.indicator}")
        return True
        
    except Exception as e:
        print(f"✗ Signal creation failed: {e}")
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all basic tests."""
    print("Running Hitherto Module System Tests...")
    print("=" * 50)
    
    tests = [
        ("Module Imports", test_module_imports),
        ("Module Creation", test_basic_module_creation),
        ("Communication Protocol", test_communication_protocol),
        ("Signal Creation", test_signal_creation)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\nTesting {test_name}...")
        try:
            if test_func():
                passed += 1
                print(f"  {test_name}: PASSED")
            else:
                print(f"  {test_name}: FAILED")
        except Exception as e:
            print(f"  {test_name}: ERROR - {e}")
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Module system is ready.")
        return True
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
