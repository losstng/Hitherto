# Hitherto Doctrine Modules

This folder contains concise references for each module in the Hitherto Market operating doctrine. Each markdown file outlines the module's role and highlights differences between the autonomous (Version 1) and human–AI hybrid (Version 2) implementation plans.

## Index
| File | Summary |
| --- | --- |
| [module_0_command_control.md](module_0_command_control.md) | Overseer that fuses signals and selects playbooks |
| [module_1_risk_management.md](module_1_risk_management.md) | Risk limits and vetoes |
| [module_2_sentiment_analysis.md](module_2_sentiment_analysis.md) | Crowd sentiment signals |
| [module_3_fundamentals_analysis.md](module_3_fundamentals_analysis.md) | Intrinsic valuations and mispricing |
| [module_4_technical_analysis.md](module_4_technical_analysis.md) | Price/volume pattern detection |
| [module_5_allocation_resources.md](module_5_allocation_resources.md) | Capital and compute optimization |
| [module_6_equity_management.md](module_6_equity_management.md) | Trade execution and slippage logging |
| [module_7_scenarios_stress_testing.md](module_7_scenarios_stress_testing.md) | Crisis simulations |
| [module_8_reinforcement_learning.md](module_8_reinforcement_learning.md) | Policy learning via reward |
| [module_9_game_theory.md](module_9_game_theory.md) | Adversary detection and mitigation |
| [module_10_regime_recognition.md](module_10_regime_recognition.md) | Market regime detection |
| [module_11_alt_data.md](module_11_alt_data.md) | Alternative data signals |
| [module_12_seasonality.md](module_12_seasonality.md) | Calendar effects |
| [module_13_intermarket_analysis.md](module_13_intermarket_analysis.md) | Cross-asset context and hedges |
| [supporting_systems.md](supporting_systems.md) | Integration, context management and guardrails |

### Interaction outline
- Sentiment, fundamentals, technical, alt-data, seasonality and intermarket modules feed signals into Command & Control.
- Command & Control collaborates with Regime Recognition and Risk Management before Allocation decides weights.
- Allocation directs targets to Equity Management for execution.
- Scenario testing, reinforcement learning and game-theory modules analyze outcomes and refine future decisions.
- Supporting systems provide messaging, memory and safety checks across all modules.
