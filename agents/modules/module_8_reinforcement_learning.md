# Module 8 – Reinforcement Learning (Policy Learner under Law)

## Role
Learns execution and timing policies that maximize reward while respecting risk constraints.

## Version 1: Autonomous
- Trains on historical data with risk-sensitive objectives.
- Suggests timing adjustments or trade refinements with confidence scores.
- Actions are always gated by risk checks before application.

## Version 2: Human–AI Hybrid
- Reward shaped with human priorities and demonstrations.
- Humans review and rate policy suggestions during deployment.
- Gradual autonomy increases as the agent proves reliable.
