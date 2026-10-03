"""Forward testing falsifies (D22, ADR-0014, ADR-0023, ADR-0031, ADR-0032):
a window declared as (minimum trades, maximum duration), run in wall-clock
time from entry into FORWARD, before approval, executing real orders at
minimum size through the proposal path. Passing means no defect was found
— not that the edge is confirmed."""
