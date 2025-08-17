from datetime import datetime

from backend.schemas import FundamentalPayload, FundamentalSignal
from backend.services import (
    ModuleCoordinator,
    SentimentAnalyzer,
    AltDataAnalyzer,
    FundamentalsAnalyzer,
    SeasonalityAnalyzer,
    IntermarketAnalyzer,
    TechnicalAnalyzer,
)
from backend.services.overseer import Overseer, load_playbooks
from backend.database import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def test_fundamental_signal_model():
    payload = FundamentalPayload(
        asset="AAPL",
        fair_value_estimate=100.0,
        mispricing_percent=10.0,
        confidence=0.9,
    )
    sig = FundamentalSignal(
        origin_module="fundamentals",
        timestamp=datetime.utcnow(),
        payload=payload,
        confidence=payload.confidence,
    )
    assert sig.message_type == "FundamentalSignal"
    assert sig.payload.asset == "AAPL"
    assert sig.payload.mispricing_percent == 10.0


def test_fundamentals_analyzer_basic():
    analyzer = FundamentalsAnalyzer(eps=5.0, benchmark_pe=10.0, price=50.0)
    sig = analyzer.generate({})
    assert isinstance(sig, FundamentalSignal)
    assert sig.payload.fair_value_estimate == 50.0
    assert sig.payload.mispricing_percent == 0.0


def test_module_coordinator_runs_all_modules():
    coord = ModuleCoordinator([
        SentimentAnalyzer(),
        TechnicalAnalyzer(),
        AltDataAnalyzer(),
        FundamentalsAnalyzer(),
        SeasonalityAnalyzer(),
        IntermarketAnalyzer(),
    ])
    signals = coord.run()
    assert len(signals) == 6
    assert set(coord.context.keys()) == {
        "sentiment",
        "technical",
        "altdata",
        "fundamentals",
        "seasonality",
        "intermarket",
    }


def test_overseer_cycle_with_new_modules():
    playbooks = load_playbooks("backend/config/playbooks.json")
    overseer = Overseer(playbooks)
    coord = ModuleCoordinator([
        SentimentAnalyzer(),
        TechnicalAnalyzer(),
        AltDataAnalyzer(),
        FundamentalsAnalyzer(),
        SeasonalityAnalyzer(),
        IntermarketAnalyzer(),
    ])
    engine = create_engine("sqlite://")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    result = overseer.run_cycle(coord, db=session)
    assert len(result["signals"]) == 6
    assert any(sig.message_type == "FundamentalSignal" for sig in result["signals"])
    assert result["proposal"].payload.actions
