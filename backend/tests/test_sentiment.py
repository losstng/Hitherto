from datetime import datetime

from backend.services.sentiment import SentimentAnalyzer
from backend.database import Base
from backend import models
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def test_generate_from_newsletters():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Seed a newsletter
    nl = models.Newsletter(
        title="Report",
        category="AAPL",
        sender="news@example.com",
        received_at=datetime(2024, 1, 1),
        extracted_text="Apple reports good profit and strong growth",
        message_id="1",
    )
    session.add(nl)
    session.commit()

    analyzer = SentimentAnalyzer()
    signals = analyzer.generate_from_newsletters(session)

    assert len(signals) == 1
    sig = signals[0]
    assert sig.payload.asset == "AAPL"
    assert sig.payload.sentiment_score > 0
    # persisted
    assert session.query(models.Signal).count() == 1
