# Module 3 – Fundamentals Analysis (Anchor)

## Role
Provides intrinsic value estimates and quality scores using financial statements and alternative data.

## Version 1: Autonomous
- Computes multi-factor rankings and probabilistic fair value bands.
- Adjusts valuations with nowcast signals from alternative data.
- Emits mispricing scores and factor exposures.

## Version 2: Human–AI Hybrid
- AI generates valuations; analysts refine assumptions and add qualitative flags.
- Humans investigate large discrepancies and feed insights back to models.
- Collaborative notes accompany structured outputs.

## Example metrics
- Price/Earnings, Return on Equity, Free Cash Flow yield.
- Alternative data like web traffic adjusts growth assumptions.

### Fair-value calculation
```
Base = EPS 2.5 * P/E 15 = 37.5
Alt-data boost (10%) => P/E 16 -> Fair value 40
```
