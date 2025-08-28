# Module 2 – Sentiment Analysis (Narrative Field)

## Role
Extracts crowd mood and narrative tone from news and social data, generating sentiment signals.

## Version 1: Autonomous
- Ingests textual feeds and uses transformer models for sentiment scoring.
- Tracks narrative contagion and surprise metrics.
- Publishes structured sentiment signals with confidence levels.

## Version 2: Human–AI Hybrid
- AI scores sentiment; analysts verify market-moving items.
- Humans filter low-credibility sources and provide context.
- Corrections loop back into future model training.

## Data sources
- News APIs (hourly refresh)
- Social media firehoses (5‑minute updates)
- Analyst reports and blogs (daily)

### Sentiment signal format
```json
{
  "ticker": "TSLA",
  "score": -0.4,
  "confidence": 0.73
}
```
