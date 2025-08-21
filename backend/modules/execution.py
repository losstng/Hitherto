"""Execution Module - Order Management and Trade Execution."""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from .base import ModuleBase, ModuleResult, ModuleError
from .database import DatabaseManager, ExecutionReport
from .llm_integration import EnhancedLLMReasoner
from backend.schemas.core.schemas import SignalBase, TradeProposal, TradeAction


class OrderType(str, Enum):
    """Order types."""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "STOP_LOSS"
    STOP_LIMIT = "STOP_LIMIT"


class OrderStatus(str, Enum):
    """Order status."""
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class OrderSide(str, Enum):
    """Order side."""
    BUY = "BUY"
    SELL = "SELL"


class ExecutionConfig(BaseModel):
    """Execution system configuration."""
    
    broker_name: str = "MOCK"
    sandbox_mode: bool = True
    max_order_value: float = 100000.0
    max_orders_per_minute: int = 60
    estimated_slippage: float = 0.001
    estimated_commission: float = 0.001
    order_timeout_seconds: int = 300
    enable_circuit_breakers: bool = True
    max_daily_loss: float = 0.05
    max_position_size: float = 0.10


class Order(BaseModel):
    """Order representation."""
    
    order_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    asset: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float] = None
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = 0.0
    average_fill_price: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    submitted_at: Optional[datetime] = None
    filled_at: Optional[datetime] = None
    proposal_id: Optional[str] = None


class Fill(BaseModel):
    """Order fill representation."""
    
    fill_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    order_id: str
    asset: str
    side: OrderSide
    quantity: float
    price: float
    commission: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MockBroker:
    """Mock broker for simulation."""
    
    def __init__(self, config: ExecutionConfig):
        self.config = config
        self.connected = False
        self.orders: Dict[str, Order] = {}
        self.fills: List[Fill] = []
        self.positions: Dict[str, float] = {}
        self.cash_balance = 100000.0
        self.mock_prices: Dict[str, float] = {}
    
    async def connect(self) -> bool:
        """Connect to mock broker."""
        self.connected = True
        logging.info("Connected to mock broker")
        return True
    
    async def disconnect(self) -> None:
        """Disconnect from mock broker."""
        self.connected = False
        logging.info("Disconnected from mock broker")
    
    def _get_mock_price(self, asset: str) -> float:
        """Get mock price for asset."""
        if asset not in self.mock_prices:
            hash_val = hash(asset) % 1000
            self.mock_prices[asset] = 50.0 + (hash_val / 10.0)
        return self.mock_prices[asset]
    
    async def submit_order(self, order: Order) -> str:
        """Submit order to mock broker."""
        if not self.connected:
            raise Exception("Not connected to broker")
        
        order.status = OrderStatus.SUBMITTED
        order.submitted_at = datetime.utcnow()
        self.orders[order.order_id] = order
        
        # Simulate immediate fill for market orders
        if order.order_type == OrderType.MARKET:
            await self._simulate_fill(order)
        
        logging.info(f"Submitted order {order.order_id}: {order.side} {order.quantity} {order.asset}")
        return order.order_id
    
    async def _simulate_fill(self, order: Order) -> None:
        """Simulate order fill."""
        fill_price = self._get_mock_price(order.asset)
        
        # Add slippage
        if order.side == OrderSide.BUY:
            fill_price *= (1 + self.config.estimated_slippage)
        else:
            fill_price *= (1 - self.config.estimated_slippage)
        
        commission = order.quantity * fill_price * self.config.estimated_commission
        
        # Create fill
        fill = Fill(
            order_id=order.order_id,
            asset=order.asset,
            side=order.side,
            quantity=order.quantity,
            price=fill_price,
            commission=commission
        )
        
        self.fills.append(fill)
        
        # Update order
        order.status = OrderStatus.FILLED
        order.filled_quantity = order.quantity
        order.average_fill_price = fill_price
        order.filled_at = datetime.utcnow()
        
        # Update positions
        if order.side == OrderSide.BUY:
            self.positions[order.asset] = self.positions.get(order.asset, 0.0) + order.quantity
            self.cash_balance -= (order.quantity * fill_price) + commission
        else:
            self.positions[order.asset] = self.positions.get(order.asset, 0.0) - order.quantity
            self.cash_balance += (order.quantity * fill_price) - commission
        
        logging.info(f"Filled order {order.order_id}: {order.quantity} @ {fill_price:.2f}")
    
    async def get_positions(self) -> Dict[str, float]:
        """Get current positions."""
        return self.positions.copy()
    
    async def get_account_balance(self) -> Dict[str, float]:
        """Get account balance."""
        equity = self.cash_balance + sum(
            qty * self._get_mock_price(asset) 
            for asset, qty in self.positions.items()
        )
        return {"cash": self.cash_balance, "equity": equity}
    
    async def get_market_price(self, asset: str) -> Optional[float]:
        """Get current market price."""
        return self._get_mock_price(asset)


class ExecutionSignal(SignalBase):
    """Execution status signal."""
    message_type: str = "ExecutionSignal"
    
    def __init__(self, execution_data: Dict[str, Any], **kwargs):
        super().__init__(payload=execution_data, **kwargs)


class ExecutionModule(ModuleBase):
    """Module for order execution and broker integration."""
    
    def __init__(self, communication=None):
        super().__init__("execution", "1.0.0", communication)
        
        self.execution_config: Optional[ExecutionConfig] = None
        self.broker: Optional[MockBroker] = None
        self.circuit_breaker_active = False
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.active_orders: Dict[str, Order] = {}
        self.order_history: List[Order] = []
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the execution module."""
        try:
            self.execution_config = ExecutionConfig(**config)
            self.broker = MockBroker(self.execution_config)
            
            # Connect to broker asynchronously
            asyncio.create_task(self._initialize_broker())
            
            self.activate()
            logging.info(f"Execution module initialized with broker: {self.execution_config.broker_name}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to initialize execution module: {e}")
            return False
    
    async def _initialize_broker(self) -> None:
        """Initialize broker connection."""
        if self.broker:
            await self.broker.connect()
    
    def cleanup(self) -> None:
        """Clean up execution module resources."""
        if self.broker:
            asyncio.create_task(self.broker.disconnect())
        self.deactivate()
        logging.info("Execution module cleaned up")
    
    def get_subscribed_message_types(self) -> List[str]:
        """Subscribe to risk signals for execution."""
        return ["RiskSignal"]
    
    def activate_circuit_breaker(self, reason: str) -> None:
        """Activate circuit breaker to halt trading."""
        self.circuit_breaker_active = True
        logging.critical(f"EXECUTION CIRCUIT BREAKER ACTIVATED: {reason}")
    
    def deactivate_circuit_breaker(self) -> None:
        """Deactivate circuit breaker."""
        self.circuit_breaker_active = False
        logging.info("Execution circuit breaker deactivated")
    
    async def create_order_from_action(self, action: TradeAction) -> Optional[Order]:
        """Create order from trade action."""
        
        if action.action.upper() == "HOLD" or action.size <= 0:
            return None
        
        side_map = {"BUY": OrderSide.BUY, "SELL": OrderSide.SELL}
        side = side_map.get(action.action.upper())
        
        if not side:
            logging.warning(f"Unknown action: {action.action}")
            return None
        
        # Get current market price
        market_price = None
        if self.broker:
            market_price = await self.broker.get_market_price(action.asset)
        
        order = Order(
            asset=action.asset,
            side=side,
            order_type=OrderType.MARKET,
            quantity=action.size,
            price=market_price
        )
        
        return order
    
    async def execute_order(self, order: Order) -> bool:
        """Execute an order."""
        
        if not self.broker or not self.broker.connected:
            logging.error("Broker not connected")
            return False
        
        if self.circuit_breaker_active:
            logging.warning("Circuit breaker active, skipping execution")
            return False
        
        try:
            broker_order_id = await self.broker.submit_order(order)
            self.active_orders[order.order_id] = order
            self.daily_trades += 1
            
            logging.info(f"Successfully executed order {order.order_id}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to execute order {order.order_id}: {e}")
            order.status = OrderStatus.REJECTED
            return False
    
    def generate_execution_summary(self, order: Order) -> str:
        """Generate execution summary."""
        
        # Simple execution summary without LLM
        return (f"Executed {order.side.value} {order.quantity} {order.asset} "
                f"at {order.average_fill_price:.2f} via {order.order_type.value} order")
    
    async def monitor_risk_limits(self) -> None:
        """Monitor execution risk limits."""
        
        if not self.broker or not self.execution_config or not self.execution_config.enable_circuit_breakers:
            return
        
        try:
            # Check daily loss limit
            if abs(self.daily_pnl) > self.execution_config.max_daily_loss:
                self.activate_circuit_breaker(f"Daily loss limit exceeded: {self.daily_pnl:.2%}")
                return
            
            # Check position concentrations
            positions = await self.broker.get_positions()
            balance = await self.broker.get_account_balance()
            total_value = balance.get("equity", 0.0)
            
            if total_value > 0:
                for asset, quantity in positions.items():
                    market_price = await self.broker.get_market_price(asset)
                    if market_price:
                        position_value = quantity * market_price
                        concentration = abs(position_value) / total_value
                        
                        if concentration > self.execution_config.max_position_size:
                            self.activate_circuit_breaker(
                                f"Position concentration exceeded: {asset} {concentration:.2%}"
                            )
                            return
                            
        except Exception as e:
            logging.error(f"Risk monitoring error: {e}")
    
    def process(self, context: Dict[str, SignalBase]) -> ModuleResult:
        """Process execution signals."""
        
        if not self.execution_config or not self.broker:
            return ModuleResult(
                success=False,
                errors=["Execution module not properly initialized"]
            )
        
        try:
            signals_generated = []
            warnings = []
            
            # Get incoming risk signals
            risk_signals = []
            
            # Check context for risk signals
            for signal in context.values():
                if hasattr(signal, 'message_type') and signal.message_type == 'RiskSignal':
                    risk_signals.append(signal)
            
            # Check communication for risk signals
            relevant_messages = self.communication.get_messages_for_module(self.name)
            for message in relevant_messages:
                if hasattr(message, 'message_type') and message.message_type == 'RiskSignal':
                    risk_signals.append(message)
            
            if not risk_signals:
                return ModuleResult(
                    success=True,
                    signals=[],
                    warnings=["No risk signals received for execution"],
                    metadata={"circuit_breaker_active": self.circuit_breaker_active}
                )
            
            # Process approved risk signals
            executed_orders = []
            
            for risk_signal in risk_signals:
                if hasattr(risk_signal, 'payload') and isinstance(risk_signal.payload, dict):
                    verdict = risk_signal.payload.get('verdict', 'REJECTED')
                    
                    if verdict == 'APPROVED':
                        # Execute original actions
                        original_actions = risk_signal.payload.get('original_actions', [])
                        for action_data in original_actions:
                            # Convert dict to TradeAction if needed
                            if isinstance(action_data, dict):
                                action = TradeAction(**action_data)
                            else:
                                action = action_data
                            
                            # Create and execute order
                            order = asyncio.run(self.create_order_from_action(action))
                            if order:
                                success = asyncio.run(self.execute_order(order))
                                if success:
                                    executed_orders.append(order)
                    
                    elif verdict == 'DOWNGRADED':
                        # Execute adjusted actions
                        adjusted_actions = risk_signal.payload.get('adjusted_actions', [])
                        for action_data in adjusted_actions:
                            if isinstance(action_data, dict):
                                action = TradeAction(**action_data)
                            else:
                                action = action_data
                            
                            order = asyncio.run(self.create_order_from_action(action))
                            if order:
                                success = asyncio.run(self.execute_order(order))
                                if success:
                                    executed_orders.append(order)
                        
                        warnings.append(f"Executed downgraded proposal: {risk_signal.payload.get('rationale', '')}")
                    
                    else:  # REJECTED
                        warnings.append(f"Proposal rejected: {risk_signal.payload.get('rationale', '')}")
            
            # Generate execution signals for executed orders
            for order in executed_orders:
                execution_data = {
                    "order_id": order.order_id,
                    "asset": order.asset,
                    "side": order.side.value,
                    "quantity": order.quantity,
                    "status": order.status.value,
                    "filled_quantity": order.filled_quantity,
                    "average_fill_price": order.average_fill_price,
                    "summary": self.generate_execution_summary(order)
                }
                
                execution_signal = ExecutionSignal(
                    execution_data=execution_data,
                    timestamp=datetime.utcnow(),
                    origin_module="execution",
                    confidence=1.0
                )
                
                signals_generated.append(execution_signal)
            
            # Monitor risk limits
            asyncio.create_task(self.monitor_risk_limits())
            
            return ModuleResult(
                success=True,
                signals=signals_generated,
                warnings=warnings,
                metadata={
                    "orders_executed": len(executed_orders),
                    "circuit_breaker_active": self.circuit_breaker_active,
                    "daily_trades": self.daily_trades,
                    "daily_pnl": self.daily_pnl
                }
            )
            
        except Exception as e:
            error_msg = f"Execution processing failed: {str(e)}"
            logging.error(error_msg)
            return ModuleResult(
                success=False,
                errors=[error_msg]
            )
    
    async def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get current portfolio summary."""
        
        if not self.broker:
            return {}
        
        try:
            positions = await self.broker.get_positions()
            balance = await self.broker.get_account_balance()
            
            portfolio_value = balance.get("equity", 0.0)
            cash = balance.get("cash", 0.0)
            
            position_values = {}
            for asset, quantity in positions.items():
                market_price = await self.broker.get_market_price(asset)
                if market_price:
                    position_values[asset] = quantity * market_price
            
            return {
                "total_value": portfolio_value,
                "cash": cash,
                "positions": positions,
                "position_values": position_values,
                "daily_trades": self.daily_trades,
                "daily_pnl": self.daily_pnl,
                "circuit_breaker_active": self.circuit_breaker_active,
                "active_orders": len(self.active_orders)
            }
            
        except Exception as e:
            logging.error(f"Failed to get portfolio summary: {e}")
            return {}
    
    def get_execution_status(self) -> Dict[str, Any]:
        """Get execution module status."""
        
        return {
            "broker_connected": self.broker.connected if self.broker else False,
            "broker_type": self.execution_config.broker_name if self.execution_config else "unknown",
            "circuit_breaker_active": self.circuit_breaker_active,
            "daily_trades": self.daily_trades,
            "daily_pnl": self.daily_pnl,
            "active_orders": len(self.active_orders),
            "module_status": self.status.value
        }
