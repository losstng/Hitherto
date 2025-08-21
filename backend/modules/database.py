"""Unified and enhanced database layer for Hitherto modules architecture.

This module provides a comprehensive database layer that consolidates and enhances
the previous services and modules database approaches while maintaining compatibility.
"""

import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, DateTime, JSON, Boolean, Float, Text,
    Enum, ForeignKey, func, Index, and_, or_
)
from sqlalchemy.orm import relationship, Session, sessionmaker
from sqlalchemy.sql import select, update, delete
from pydantic import BaseModel
import enum

# Import existing database components for compatibility
from backend.database import engine, SessionLocal, Base

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS
# ============================================================================

class ModuleStatus(enum.Enum):
    """Module operational status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class RegimeType(enum.Enum):
    """Market regime classification types."""
    BULL = "bull"
    BEAR = "bear"
    SIDEWAYS = "sideways"
    HIGH_VOL = "high_vol"
    LOW_VOL = "low_vol"
    CRISIS = "crisis"
    RECOVERY = "recovery"
    UNKNOWN = "unknown"


class RiskLevel(enum.Enum):
    """Risk assessment levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class OrderStatus(enum.Enum):
    """Order execution status."""
    PENDING = "pending"
    SUBMITTED = "submitted"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


# ============================================================================
# ENHANCED MODELS
# ============================================================================

class ModuleRegistry(Base):
    """Registry and status tracking for all system modules."""
    __tablename__ = "module_registry"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    version = Column(String(20), nullable=False)
    status = Column(String(20), default="inactive", nullable=False, index=True)
    config_json = Column(JSON, nullable=True)
    last_execution = Column(DateTime, nullable=True, index=True)
    execution_count = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
    avg_execution_time_ms = Column(Float, nullable=True)
    success_rate = Column(Float, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    health_checks = relationship("ModuleHealthCheck", back_populates="module", lazy="dynamic")
    
    def __repr__(self):
        return f"<ModuleRegistry(name='{self.name}', status='{self.status}')>"


class ModuleHealthCheck(Base):
    """Health monitoring for modules."""
    __tablename__ = "module_health_checks"
    
    id = Column(Integer, primary_key=True, index=True)
    module_id = Column(Integer, ForeignKey("module_registry.id"), nullable=False, index=True)
    status = Column(String(20), nullable=False)
    response_time_ms = Column(Float, nullable=True)
    error_count = Column(Integer, default=0, nullable=False)
    memory_usage_mb = Column(Float, nullable=True)
    cpu_usage_percent = Column(Float, nullable=True)
    details_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Relationships
    module = relationship("ModuleRegistry", back_populates="health_checks")
    
    __table_args__ = (
        Index('ix_module_health_created', 'module_id', 'created_at'),
    )


class RegimeState(Base):
    """Enhanced regime classification with human confirmation workflow."""
    __tablename__ = "regime_states"
    
    id = Column(Integer, primary_key=True, index=True)
    regime_type = Column(String(20), nullable=False, index=True)
    confidence = Column(Float, nullable=False)
    classification_method = Column(String(50), nullable=False)
    classified_by = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=False, nullable=False, index=True)
    confirmed_by_human = Column(Boolean, default=False, nullable=False)
    requires_confirmation = Column(Boolean, default=False, nullable=False)
    effective_from = Column(DateTime, nullable=False, index=True)
    effective_until = Column(DateTime, nullable=True)
    context_json = Column(JSON, nullable=True)
    reasoning = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    __table_args__ = (
        Index('ix_regime_active_time', 'is_active', 'effective_from'),
        Index('ix_regime_type_time', 'regime_type', 'effective_from'),
    )


class RiskEvaluation(Base):
    """Risk assessment results for proposals."""
    __tablename__ = "risk_evaluations"
    
    id = Column(Integer, primary_key=True, index=True)
    proposal_id = Column(String(100), nullable=False, index=True)
    risk_level = Column(String(20), nullable=False, index=True)
    var_99 = Column(Float, nullable=True)
    expected_shortfall = Column(Float, nullable=True)
    max_drawdown = Column(Float, nullable=True)
    sharpe_ratio = Column(Float, nullable=True)
    verdict = Column(String(20), nullable=False)
    flags_json = Column(JSON, nullable=True)
    recommendations_json = Column(JSON, nullable=True)
    evaluation_method = Column(String(50), nullable=False)
    model_version = Column(String(20), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    __table_args__ = (
        Index('ix_risk_level_created', 'risk_level', 'created_at'),
    )


class ExecutionReport(Base):
    """Order execution tracking and reporting."""
    __tablename__ = "execution_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    proposal_id = Column(String(100), nullable=True, index=True)
    order_id = Column(String(100), unique=True, nullable=False, index=True)
    asset = Column(String(20), nullable=False, index=True)
    side = Column(String(10), nullable=False)
    quantity = Column(Float, nullable=False)
    order_type = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, index=True)
    filled_quantity = Column(Float, default=0.0, nullable=False)
    average_fill_price = Column(Float, nullable=True)
    total_commission = Column(Float, nullable=True)
    submitted_at = Column(DateTime, nullable=True, index=True)
    filled_at = Column(DateTime, nullable=True)
    broker_name = Column(String(50), nullable=True)
    execution_metadata = Column(JSON, nullable=True)
    execution_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    __table_args__ = (
        Index('ix_execution_asset_status', 'asset', 'status'),
        Index('ix_execution_submitted', 'submitted_at'),
    )


class PortfolioSnapshot(Base):
    """Portfolio state snapshots for risk monitoring."""
    __tablename__ = "portfolio_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    positions_json = Column(JSON, nullable=False)
    cash_balance = Column(Float, nullable=False)
    total_value = Column(Float, nullable=False)
    portfolio_var = Column(Float, nullable=True)
    portfolio_volatility = Column(Float, nullable=True)
    max_position_concentration = Column(Float, nullable=True)
    correlation_risk = Column(Float, nullable=True)
    snapshot_reason = Column(String(50), nullable=False)
    market_hours = Column(Boolean, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    __table_args__ = (
        Index('ix_portfolio_snapshot_created', 'created_at'),
    )


# ============================================================================
# DATABASE MANAGER
# ============================================================================

class DatabaseManager:
    """Unified database manager for all module operations."""
    
    def __init__(self, session: Optional[Session] = None):
        self.session = session
        self._own_session = session is None
    
    def __enter__(self):
        if self._own_session:
            self.session = SessionLocal()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._own_session and self.session:
            if exc_type:
                self.session.rollback()
            else:
                self.session.commit()
            self.session.close()
    
    def get_session(self) -> Session:
        """Get database session."""
        if not self.session:
            self.session = SessionLocal()
        return self.session
    
    # Module Management
    def register_module(self, name: str, version: str, config: Optional[Dict] = None) -> ModuleRegistry:
        """Register or update a module."""
        session = self.get_session()
        
        # Try to find existing module
        module = session.query(ModuleRegistry).filter(ModuleRegistry.name == name).first()
        
        if module:
            # Update existing module using SQL update
            session.execute(
                update(ModuleRegistry)
                .where(ModuleRegistry.name == name)
                .values(
                    version=version,
                    config_json=config,
                    updated_at=datetime.utcnow()
                )
            )
            if self._own_session:
                session.commit()
            # Refresh the module object
            session.refresh(module)
        else:
            # Create new module
            module = ModuleRegistry(
                name=name,
                version=version,
                config_json=config,
                status="inactive"
            )
            session.add(module)
            if self._own_session:
                session.commit()
        
        return module
    
    def update_module_status(self, name: str, status: str, error_message: Optional[str] = None) -> None:
        """Update module status."""
        session = self.get_session()
        
        session.execute(
            update(ModuleRegistry)
            .where(ModuleRegistry.name == name)
            .values(
                status=status,
                error_message=error_message,
                updated_at=datetime.utcnow()
            )
        )
        
        if self._own_session:
            session.commit()
    
    def record_module_execution(self, name: str, execution_time_ms: float, success: bool = True) -> None:
        """Record module execution metrics."""
        session = self.get_session()
        
        # Get current module data
        module = session.query(ModuleRegistry).filter(ModuleRegistry.name == name).first()
        if not module:
            return
        
        # Calculate new values
        new_count = module.execution_count + 1
        
        # Update running average
        if module.avg_execution_time_ms is not None:
            new_avg = ((module.avg_execution_time_ms * module.execution_count) + execution_time_ms) / new_count
        else:
            new_avg = execution_time_ms
        
        # Update the module
        session.execute(
            update(ModuleRegistry)
            .where(ModuleRegistry.name == name)
            .values(
                execution_count=new_count,
                last_execution=datetime.utcnow(),
                avg_execution_time_ms=new_avg,
                updated_at=datetime.utcnow()
            )
        )
        
        if self._own_session:
            session.commit()
    
    # Regime Management
    def set_active_regime(self, regime_type: str, confidence: float, 
                          method: str, classified_by: str, context: Optional[Dict] = None) -> RegimeState:
        """Set the current active market regime."""
        session = self.get_session()
        
        # Deactivate current regime
        session.execute(
            update(RegimeState)
            .where(RegimeState.is_active == True)
            .values(
                is_active=False,
                effective_until=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        )
        
        # Create new regime
        regime = RegimeState(
            regime_type=regime_type,
            confidence=confidence,
            classification_method=method,
            classified_by=classified_by,
            is_active=True,
            effective_from=datetime.utcnow(),
            context_json=context
        )
        
        session.add(regime)
        if self._own_session:
            session.commit()
        return regime
    
    def get_active_regime(self) -> Optional[RegimeState]:
        """Get the currently active regime."""
        session = self.get_session()
        return session.query(RegimeState).filter(RegimeState.is_active == True).first()
    
    # Risk Management
    def store_risk_evaluation(self, risk_eval: 'RiskEvaluationData') -> RiskEvaluation:
        """Store risk evaluation results."""
        session = self.get_session()
        
        risk_evaluation = RiskEvaluation(
            proposal_id=risk_eval.proposal_id or "unknown",
            risk_level=risk_eval.risk_level.lower(),
            var_99=risk_eval.var_99,
            expected_shortfall=risk_eval.expected_shortfall,
            max_drawdown=risk_eval.max_drawdown,
            sharpe_ratio=risk_eval.sharpe_ratio,
            verdict=risk_eval.verdict,
            flags_json=risk_eval.flags,
            recommendations_json=risk_eval.recommendations,
            evaluation_method=risk_eval.evaluation_method or "unknown"
        )
        
        session.add(risk_evaluation)
        if self._own_session:
            session.commit()
        return risk_evaluation
    
    # Execution Management
    def store_execution_report(self, exec_report: 'ExecutionReportData') -> ExecutionReport:
        """Store execution report."""
        session = self.get_session()
        
        execution = ExecutionReport(
            proposal_id=exec_report.proposal_id,
            order_id=exec_report.order_id,
            asset=exec_report.asset,
            side=exec_report.side,
            quantity=exec_report.quantity,
            order_type=exec_report.order_type,
            status=exec_report.status.lower(),
            filled_quantity=exec_report.filled_quantity or 0.0,
            average_fill_price=exec_report.average_fill_price,
            total_commission=exec_report.total_commission,
            submitted_at=exec_report.submitted_at,
            filled_at=exec_report.filled_at,
            broker_name=exec_report.broker_name,
            execution_metadata=exec_report.metadata,
            execution_summary=exec_report.execution_summary
        )
        
        session.add(execution)
        if self._own_session:
            session.commit()
        return execution
    
    # Portfolio Management
    def create_portfolio_snapshot(self, positions: Dict[str, float], cash_balance: float,
                                  total_value: float, reason: str = "scheduled") -> PortfolioSnapshot:
        """Create a portfolio snapshot."""
        session = self.get_session()
        
        snapshot = PortfolioSnapshot(
            positions_json=positions,
            cash_balance=cash_balance,
            total_value=total_value,
            snapshot_reason=reason,
            market_hours=datetime.now().weekday() < 5  # Simplified market hours
        )
        
        session.add(snapshot)
        if self._own_session:
            session.commit()
        return snapshot
    
    # Health Monitoring
    def record_health_check(self, module_name: str, status: str, 
                           response_time_ms: Optional[float] = None, 
                           details: Optional[Dict] = None) -> ModuleHealthCheck:
        """Record a module health check."""
        session = self.get_session()
        
        module = session.query(ModuleRegistry).filter(ModuleRegistry.name == module_name).first()
        if not module:
            # Auto-register module if not exists
            module = self.register_module(module_name, "unknown")
        
        health_check = ModuleHealthCheck(
            module_id=module.id,
            status=status,
            response_time_ms=response_time_ms,
            details_json=details
        )
        
        session.add(health_check)
        if self._own_session:
            session.commit()
        return health_check
    
    # Signal and Proposal Management (Legacy compatibility)
    def save_signal(self, signal: Union[Dict[str, Any], Any], module_id: Optional[Union[str, int]] = None) -> str:
        """Save a signal for legacy compatibility."""
        # For now, just generate a unique ID and log
        signal_id = f"signal_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
        module_str = str(module_id) if module_id is not None else "unknown"
        logger.info(f"Signal saved with ID: {signal_id}, module: {module_str}")
        
        # Handle different signal types
        try:
            if hasattr(signal, 'model_dump'):
                signal_data = signal.model_dump()
            elif hasattr(signal, '__dict__'):
                signal_data = signal.__dict__
            elif isinstance(signal, dict):
                signal_data = signal
            else:
                signal_data = {"raw": str(signal)}
        except Exception as e:
            logger.warning(f"Error serializing signal: {e}")
            signal_data = {"raw": str(signal)}
        
        logger.debug(f"Signal data: {signal_data}")
        return signal_id
    
    def save_proposal(self, proposal_id: Union[str, Dict[str, Any]], proposal_data: Union[Dict[str, Any], str], 
                      module_id: Optional[Union[str, int]] = None) -> str:
        """Save a proposal for legacy compatibility."""
        # Handle parameter order flexibility
        if isinstance(proposal_id, dict):
            # proposal_id is actually proposal_data, proposal_data is module_id
            actual_proposal_data = proposal_id
            actual_module_id = proposal_data if isinstance(proposal_data, str) else str(proposal_data)
            actual_proposal_id = f"proposal_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
        else:
            actual_proposal_id = str(proposal_id)
            actual_proposal_data = proposal_data if isinstance(proposal_data, dict) else {"raw": str(proposal_data)}
            actual_module_id = str(module_id) if module_id is not None else "unknown"
        
        logger.info(f"Proposal saved: {actual_proposal_id}, module: {actual_module_id}")
        logger.debug(f"Proposal data: {actual_proposal_data}")
        return actual_proposal_id
    
    def update_regime(self, regime_data: Dict[str, Any]) -> None:
        """Update regime for legacy compatibility."""
        regime_type = regime_data.get('type', 'unknown')
        confidence = regime_data.get('confidence', 0.5)
        method = regime_data.get('method', 'legacy')
        classified_by = regime_data.get('classified_by', 'overseer')
        context = regime_data.get('context', {})
        
        self.set_active_regime(
            regime_type=regime_type,
            confidence=confidence,
            method=method,
            classified_by=classified_by,
            context=context
        )

    # Utility methods
    def cleanup_old_data(self, days_to_keep: int = 90) -> int:
        """Clean up old data to maintain performance."""
        from datetime import timedelta
        session = self.get_session()
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        # Clean up old health checks
        result = session.execute(
            delete(ModuleHealthCheck)
            .where(ModuleHealthCheck.created_at < cutoff_date)
        )
        
        if self._own_session:
            session.commit()
        
        return result.rowcount if result else 0
    
    def get_module_stats(self, module_name: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive stats for a module."""
        session = self.get_session()
        
        module = session.query(ModuleRegistry).filter(ModuleRegistry.name == module_name).first()
        if not module:
            return None
        
        # Get recent health checks
        recent_checks = (
            session.query(ModuleHealthCheck)
            .filter(ModuleHealthCheck.module_id == module.id)
            .order_by(ModuleHealthCheck.created_at.desc())
            .limit(10)
            .all()
        )
        
        return {
            "module": {
                "name": module.name,
                "version": module.version,
                "status": module.status,
                "execution_count": module.execution_count,
                "last_execution": module.last_execution,
                "avg_execution_time_ms": module.avg_execution_time_ms,
                "success_rate": module.success_rate,
                "error_message": module.error_message
            },
            "recent_health_checks": [
                {
                    "status": check.status,
                    "response_time_ms": check.response_time_ms,
                    "created_at": check.created_at,
                    "details": check.details_json
                }
                for check in recent_checks
            ]
        }
    
    def get_all_modules(self) -> List[ModuleRegistry]:
        """Get all registered modules."""
        session = self.get_session()
        return session.query(ModuleRegistry).all()
    
    def get_module_by_name(self, name: str) -> Optional[ModuleRegistry]:
        """Get a module by name."""
        session = self.get_session()
        return session.query(ModuleRegistry).filter(ModuleRegistry.name == name).first()


# ============================================================================
# DATA TRANSFER OBJECTS
# ============================================================================

class RiskEvaluationData(BaseModel):
    """Data transfer object for risk evaluations."""
    proposal_id: Optional[str] = None
    risk_level: str
    var_99: Optional[float] = None
    expected_shortfall: Optional[float] = None
    max_drawdown: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    verdict: str
    flags: Optional[Dict[str, Any]] = None
    recommendations: Optional[Dict[str, Any]] = None
    evaluation_method: Optional[str] = None


class ExecutionReportData(BaseModel):
    """Data transfer object for execution reports."""
    proposal_id: Optional[str] = None
    order_id: str
    asset: str
    side: str
    quantity: float
    order_type: str
    status: str
    filled_quantity: Optional[float] = None
    average_fill_price: Optional[float] = None
    total_commission: Optional[float] = None
    submitted_at: Optional[datetime] = None
    filled_at: Optional[datetime] = None
    broker_name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    execution_summary: Optional[str] = None


# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

def create_tables():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)
    logger.info("Enhanced database tables created successfully")


def get_db():
    """Get database session (FastAPI dependency)."""
    logger.debug("Creating new database session")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        logger.debug("Database session closed")


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def get_database_manager(session: Optional[Session] = None) -> DatabaseManager:
    """Get a database manager instance."""
    return DatabaseManager(session)


# Legacy compatibility functions
def get_session() -> Session:
    """Get a database session for legacy compatibility."""
    return SessionLocal()
