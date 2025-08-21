"""Unified and enhanced database layer for Hitherto modules architecture.

This module provides a comprehensive database layer that consolidates and enhances
the previous services and modules database approaches. It includes:

1. Core system models (signals, proposals, decisions)
2. Module management and health tracking
3. Regime classification and state management
4. Risk evaluation and portfolio tracking
5. Execution reporting and order management
6. Data ingestion models (newsletters, SEC filings)
7. Human feedback and override tracking

The design supports both the legacy services workflow and the new modules architecture.
"""

import logging
from typing import Any, Dict, List, Optional, Type, TypeVar, Union
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, DateTime, JSON, Boolean, Float, Text,
    Enum, ForeignKey, func, Index, UniqueConstraint, create_engine
)
from sqlalchemy.orm import relationship, Session, sessionmaker, declarative_base
from pydantic import BaseModel
import enum

from backend.env import DATABASE_URL

logger = logging.getLogger(__name__)

# Database setup - use existing engine and session from backend.database
try:
    from backend.database import engine, SessionLocal, Base as LegacyBase
    logger.info("Using existing database engine and session")
except ImportError:
    # Fallback if backend.database is not available
    if DATABASE_URL:
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    else:
        raise ValueError("DATABASE_URL not configured")

# Use the existing Base for compatibility
Base = LegacyBase

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


class ProposalStatus(enum.Enum):
    """Trade proposal lifecycle status."""
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    CANCELLED = "cancelled"


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
# MIXINS
# ============================================================================

class TimestampMixin:
    """Mixin for automatic timestamp tracking."""
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


class MetadataMixin:
    """Mixin for flexible metadata storage."""
    metadata_json = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)


# ============================================================================
# ENHANCED SYSTEM MODELS
# ============================================================================

class ModuleRegistry(Base, TimestampMixin):
    """Registry and status tracking for all system modules."""
    __tablename__ = "module_registry"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    version = Column(String(20), nullable=False)
    status = Column(Enum(ModuleStatus), default=ModuleStatus.INACTIVE, nullable=False, index=True)
    config_json = Column(JSON, nullable=True)
    last_execution = Column(DateTime, nullable=True, index=True)
    execution_count = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
    
    # Performance metrics
    avg_execution_time_ms = Column(Float, nullable=True)
    success_rate = Column(Float, nullable=True)
    
    # Relationships
    health_checks = relationship("ModuleHealthCheck", back_populates="module")
    
    def __repr__(self):
        return f"<ModuleRegistry(name='{self.name}', status='{self.status.value}')>"


class ModuleHealthCheck(Base, TimestampMixin):
    """Health monitoring and performance metrics for modules."""
    __tablename__ = "module_health_checks"
    
    id = Column(Integer, primary_key=True, index=True)
    module_id = Column(Integer, ForeignKey("module_registry.id"), nullable=False, index=True)
    status = Column(Enum(ModuleStatus), nullable=False)
    response_time_ms = Column(Float, nullable=True)
    error_count = Column(Integer, default=0, nullable=False)
    memory_usage_mb = Column(Float, nullable=True)
    cpu_usage_percent = Column(Float, nullable=True)
    details_json = Column(JSON, nullable=True)
    
    # Relationships
    module = relationship("ModuleRegistry", back_populates="health_checks")
    
    __table_args__ = (
        Index('ix_module_health_created', 'module_id', 'created_at'),
    )


class EnhancedRegimeState(Base, TimestampMixin):
    """Enhanced regime classification with human confirmation workflow."""
    __tablename__ = "enhanced_regime_states"
    
    id = Column(Integer, primary_key=True, index=True)
    regime_type = Column(Enum(RegimeType), nullable=False, index=True)
    confidence = Column(Float, nullable=False)
    
    # Classification metadata
    classification_method = Column(String(50), nullable=False)  # "statistical", "llm", "human", "hybrid"
    classified_by = Column(String(100), nullable=False)  # Module or user name
    
    # State management
    is_active = Column(Boolean, default=False, nullable=False, index=True)
    confirmed_by_human = Column(Boolean, default=False, nullable=False)
    requires_confirmation = Column(Boolean, default=False, nullable=False)
    
    # Timing
    effective_from = Column(DateTime, nullable=False, index=True)
    effective_until = Column(DateTime, nullable=True)
    
    # Context and reasoning
    context_json = Column(JSON, nullable=True)
    reasoning = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    
    __table_args__ = (
        Index('ix_regime_active_time', 'is_active', 'effective_from'),
        Index('ix_regime_type_time', 'regime_type', 'effective_from'),
    )


class EnhancedSignal(Base, TimestampMixin):
    """Enhanced signal storage with module tracking and regime context."""
    __tablename__ = "enhanced_signals"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Module tracking
    origin_module_id = Column(Integer, ForeignKey("module_registry.id"), nullable=True, index=True)
    module_name = Column(String(100), nullable=False, index=True)
    
    # Signal classification
    signal_type = Column(String(50), nullable=False, index=True)
    message_type = Column(String(50), nullable=False)
    
    # Core signal data
    payload_json = Column(JSON, nullable=False)
    confidence = Column(Float, nullable=True)
    
    # Context
    asset = Column(String(20), nullable=True, index=True)
    regime_id = Column(Integer, ForeignKey("enhanced_regime_states.id"), nullable=True, index=True)
    
    # Timing and lifecycle
    timestamp = Column(DateTime, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=True)
    processing_time_ms = Column(Float, nullable=True)
    
    # Relationships
    origin_module = relationship("ModuleRegistry", foreign_keys=[origin_module_id])
    regime = relationship("EnhancedRegimeState")
    
    __table_args__ = (
        Index('ix_enhanced_signal_module_time', 'module_name', 'timestamp'),
        Index('ix_enhanced_signal_asset_time', 'asset', 'timestamp'),
    )


class EnhancedProposal(Base, TimestampMixin):
    """Enhanced trade proposals with regime context and risk tracking."""
    __tablename__ = "enhanced_proposals"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Core proposal data
    proposal_json = Column(JSON, nullable=False)
    status = Column(Enum(ProposalStatus), default=ProposalStatus.PENDING_REVIEW, nullable=False, index=True)
    
    # Context
    regime_id = Column(Integer, ForeignKey("enhanced_regime_states.id"), nullable=True, index=True)
    originating_signal_id = Column(Integer, ForeignKey("enhanced_signals.id"), nullable=True, index=True)
    
    # Risk and validation
    risk_level = Column(Enum(RiskLevel), nullable=True, index=True)
    requires_human_approval = Column(Boolean, default=False, nullable=False)
    approved_by = Column(String(100), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    # Execution tracking
    executed_at = Column(DateTime, nullable=True)
    execution_summary = Column(Text, nullable=True)
    
    # Relationships
    regime = relationship("EnhancedRegimeState")
    originating_signal = relationship("EnhancedSignal")
    risk_evaluations = relationship("RiskEvaluation", back_populates="proposal")
    execution_reports = relationship("ExecutionReport", back_populates="proposal")
    
    __table_args__ = (
        Index('ix_enhanced_proposal_status_created', 'status', 'created_at'),
        Index('ix_enhanced_proposal_regime_status', 'regime_id', 'status'),
    )


# ============================================================================
# RISK MANAGEMENT MODELS
# ============================================================================

class RiskEvaluation(Base, TimestampMixin):
    """Risk assessment results for proposals."""
    __tablename__ = "risk_evaluations"
    
    id = Column(Integer, primary_key=True, index=True)
    proposal_id = Column(Integer, ForeignKey("enhanced_proposals.id"), nullable=False, index=True)
    
    # Risk metrics
    risk_level = Column(Enum(RiskLevel), nullable=False, index=True)
    var_99 = Column(Float, nullable=True)  # 99% Value at Risk
    expected_shortfall = Column(Float, nullable=True)  # Conditional VaR
    max_drawdown = Column(Float, nullable=True)
    sharpe_ratio = Column(Float, nullable=True)
    
    # Evaluation results
    verdict = Column(String(20), nullable=False)  # APPROVED, DOWNGRADED, REJECTED
    flags_json = Column(JSON, nullable=True)
    recommendations_json = Column(JSON, nullable=True)
    
    # Analysis context
    evaluation_method = Column(String(50), nullable=False)
    model_version = Column(String(20), nullable=True)
    
    # Relationships
    proposal = relationship("EnhancedProposal", back_populates="risk_evaluations")
    
    __table_args__ = (
        Index('ix_risk_level_created', 'risk_level', 'created_at'),
    )


class PortfolioSnapshot(Base, TimestampMixin):
    """Portfolio state snapshots for risk monitoring."""
    __tablename__ = "portfolio_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Portfolio composition
    positions_json = Column(JSON, nullable=False)  # Asset -> quantity mapping
    cash_balance = Column(Float, nullable=False)
    total_value = Column(Float, nullable=False)
    
    # Risk metrics
    portfolio_var = Column(Float, nullable=True)
    portfolio_volatility = Column(Float, nullable=True)
    max_position_concentration = Column(Float, nullable=True)
    correlation_risk = Column(Float, nullable=True)
    
    # Context
    snapshot_reason = Column(String(50), nullable=False)  # "scheduled", "trade", "alert"
    market_hours = Column(Boolean, nullable=False)
    
    __table_args__ = (
        Index('ix_portfolio_snapshot_created', 'created_at'),
    )


# ============================================================================
# EXECUTION MODELS
# ============================================================================

class ExecutionReport(Base, TimestampMixin):
    """Order execution tracking and reporting."""
    __tablename__ = "execution_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    proposal_id = Column(Integer, ForeignKey("enhanced_proposals.id"), nullable=True, index=True)
    
    # Order details
    order_id = Column(String(100), unique=True, nullable=False, index=True)
    asset = Column(String(20), nullable=False, index=True)
    side = Column(String(10), nullable=False)  # BUY/SELL
    quantity = Column(Float, nullable=False)
    order_type = Column(String(20), nullable=False)
    
    # Execution results
    status = Column(Enum(OrderStatus), nullable=False, index=True)
    filled_quantity = Column(Float, default=0.0, nullable=False)
    average_fill_price = Column(Float, nullable=True)
    total_commission = Column(Float, nullable=True)
    
    # Timing
    submitted_at = Column(DateTime, nullable=True, index=True)
    filled_at = Column(DateTime, nullable=True)
    
    # Metadata
    broker_name = Column(String(50), nullable=True)
    execution_metadata = Column(JSON, nullable=True)
    execution_summary = Column(Text, nullable=True)
    
    # Relationships
    proposal = relationship("EnhancedProposal", back_populates="execution_reports")
    
    __table_args__ = (
        Index('ix_execution_asset_status', 'asset', 'status'),
        Index('ix_execution_submitted', 'submitted_at'),
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
        
        module = session.query(ModuleRegistry).filter_by(name=name).first()
        if module:
            # Update existing module
            session.execute(
                session.query(ModuleRegistry)
                .filter_by(name=name)
                .update({
                    "version": version,
                    "config_json": config,
                    "updated_at": datetime.utcnow()
                })
            )
        else:
            module = ModuleRegistry(
                name=name,
                version=version,
                config_json=config,
                status=ModuleStatus.INACTIVE
            )
            session.add(module)
        
        if self._own_session:
            session.commit()
        return module
    
    def update_module_status(self, name: str, status: ModuleStatus, error_message: Optional[str] = None) -> None:
        """Update module status."""
        session = self.get_session()
        
        session.execute(
            session.query(ModuleRegistry)
            .filter_by(name=name)
            .update({
                "status": status,
                "error_message": error_message,
                "updated_at": datetime.utcnow()
            })
        )
        
        if self._own_session:
            session.commit()
    
    def record_module_execution(self, name: str, execution_time_ms: float, success: bool = True) -> None:
        """Record module execution metrics."""
        session = self.get_session()
        
        module = session.query(ModuleRegistry).filter_by(name=name).first()
        if module:
            new_count = module.execution_count + 1
            
            # Calculate new average execution time
            if module.avg_execution_time_ms:
                new_avg = ((module.avg_execution_time_ms * module.execution_count) + execution_time_ms) / new_count
            else:
                new_avg = execution_time_ms
            
            session.execute(
                session.query(ModuleRegistry)
                .filter_by(name=name)
                .update({
                    "execution_count": new_count,
                    "last_execution": datetime.utcnow(),
                    "avg_execution_time_ms": new_avg,
                    "updated_at": datetime.utcnow()
                })
            )
            
            if self._own_session:
                session.commit()
    
    # Signal Management
    def store_signal(self, signal_data: Dict[str, Any], module_name: str) -> EnhancedSignal:
        """Store a signal in the database."""
        session = self.get_session()
        
        # Get module ID if exists
        module = session.query(ModuleRegistry).filter_by(name=module_name).first()
        module_id = module.id if module else None
        
        signal = EnhancedSignal(
            origin_module_id=module_id,
            module_name=module_name,
            signal_type=signal_data.get("signal_type", "unknown"),
            message_type=signal_data.get("message_type", "Signal"),
            payload_json=signal_data.get("payload", {}),
            confidence=signal_data.get("confidence"),
            asset=signal_data.get("asset"),
            timestamp=signal_data.get("timestamp", datetime.utcnow()),
            processing_time_ms=signal_data.get("processing_time_ms")
        )
        
        session.add(signal)
        if self._own_session:
            session.commit()
        return signal
    
    # Regime Management
    def set_active_regime(self, regime_type: RegimeType, confidence: float, 
                          method: str, classified_by: str, context: Optional[Dict] = None) -> EnhancedRegimeState:
        """Set the current active market regime."""
        session = self.get_session()
        
        # Deactivate current regime
        session.execute(
            session.query(EnhancedRegimeState)
            .filter_by(is_active=True)
            .update({
                "is_active": False,
                "effective_until": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            })
        )
        
        # Create new regime
        regime = EnhancedRegimeState(
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
    
    def get_active_regime(self) -> Optional[EnhancedRegimeState]:
        """Get the currently active regime."""
        session = self.get_session()
        return session.query(EnhancedRegimeState).filter_by(is_active=True).first()
    
    # Risk Management
    def store_risk_evaluation(self, risk_eval: 'RiskEvaluationData') -> RiskEvaluation:
        """Store risk evaluation results."""
        session = self.get_session()
        
        risk_evaluation = RiskEvaluation(
            proposal_id=risk_eval.proposal_id,
            risk_level=RiskLevel(risk_eval.risk_level.lower()),
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
            status=OrderStatus(exec_report.status.lower()),
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
    
    # Utility methods
    def cleanup_old_data(self, days_to_keep: int = 90) -> int:
        """Clean up old data to maintain performance."""
        session = self.get_session()
        cutoff_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        cutoff_date = cutoff_date.replace(day=cutoff_date.day - days_to_keep)
        
        # Clean up old health checks
        deleted_count = session.query(ModuleHealthCheck).filter(
            ModuleHealthCheck.created_at < cutoff_date
        ).delete()
        
        # Clean up old signals (keep important ones)
        deleted_count += session.query(EnhancedSignal).filter(
            EnhancedSignal.created_at < cutoff_date,
            EnhancedSignal.signal_type.notin_(["trade_signal", "risk_alert", "regime_change"])
        ).delete()
        
        if self._own_session:
            session.commit()
        
        return deleted_count


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
