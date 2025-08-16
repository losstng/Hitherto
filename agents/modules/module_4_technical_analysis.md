# Module 4 – Technical Analysis (Path Geometry)

## Role
Analyzes price and volume patterns to identify trends, volatility regimes, and microstructure cues.

## Version 1: Autonomous
- Uses adaptive indicators, volatility models, and order-flow metrics.
- Labels regimes and produces breakout or mean-reversion alerts.
- Supplies liquidity warnings for execution.

## Version 2: Human–AI Hybrid
- AI generates charts and signals; traders confirm or adjust.
- Human feedback tunes indicator parameters and liquidity heuristics.
- Manual observations can be logged as additional signals.

## Indicators
- Exponential moving averages (20/50)
- Relative Strength Index (14)
- ATR-based volatility bands

### Sample breakout alert
```json
{
  "ticker": "AAPL",
  "alert": "price_breakout",
  "level": 190.5
}
```
