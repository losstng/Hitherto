# Module 0 – Command & Control (Overseer + Regimes)

## Role
Central orchestrator that selects strategy playbooks based on market regime, fuses signals from other modules, and applies risk vetoes before actions are executed.

## Version 1: Autonomous
- Uses statistical regime classifiers (HMM/Bayesian change-point).
- Dynamically weights modules per regime and fuses signals via ensemble methods.
- Enforces a two-key rule with the Risk module before issuing policy proposals.

## Version 2: Human–AI Hybrid
- AI proposes regime changes; humans confirm or override.
- Playbooks co-created with human strategists.
- High-impact decisions require human review prior to execution.

## Inputs/Outputs
- **Inputs:** regime probabilities, aggregated signals from sentiment, fundamentals, technical, alt-data and seasonality modules, plus risk verdicts.
- **Outputs:** playbook directives and execution commands dispatched to Allocation and Equity Management.

### Example regime switch message
```json
{
  "type": "regime_switch",
  "from": "bull",
  "to": "bear",
  "confidence": 0.82
}
```
