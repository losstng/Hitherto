# Module 6 – Equity (Position) Management (Execution Law)

## Role
Executes trades to reach target exposures while controlling market impact and liquidity risk.

## Version 1: Autonomous
- Uses optimal execution models such as Almgren–Chriss to schedule orders.
- Applies inventory and liquidity constraints with adaptive speed adjustments.
- Logs fills and slippage for feedback.

## Version 2: Human–AI Hybrid
- Auto-execution handles routine orders; traders supervise and can halt.
- Humans direct venue selection and intervene under abnormal conditions.
- Execution notes feed back to refine algorithms.

## Order lifecycle
1. Order created with target size
2. Risk module validates exposure
3. Execution engine routes to venue and monitors fills
4. Fills and slippage logged for feedback

Logged slippage feeds back to Allocation and Risk modules.
