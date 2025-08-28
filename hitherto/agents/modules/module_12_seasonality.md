# Module 12 – Cyclical Patterns & Seasonality (Temporal Skeleton)

## Role
Accounts for recurring calendar effects so other signals are interpreted relative to seasonal baselines.

## Version 1: Autonomous
- Decomposes time series to isolate seasonal components.
- Produces calendar features and baseline expectations.
- Flags periods with typical volatility or drift.

## Version 2: Human–AI Hybrid
- AI offers seasonal baselines; humans adjust for unusual events.
- Strategists review which seasonal patterns remain relevant.
- Overrides are logged to refine future seasonality models.

## Seasonal examples
| Period | Typical effect |
| --- | --- |
| Jan | Post-holiday rebound |
| Oct | Higher volatility |
| Dec | Santa rally |

Seasonal adjustments are applied before other modules evaluate anomalies.
