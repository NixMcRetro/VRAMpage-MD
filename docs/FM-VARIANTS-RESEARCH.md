# FM Engine and Chip-Mode Research

Research in progress, 28 October 2026 (UTC). Scope: distinguish the existing
emulation engine switch from chip-output modes, identify useful selector behavior
and verify checkpoint constraints. No production or release changes.

The initial pinned-source audit finds that `config.ym3438` chooses MAME versus
Nuked OPN2, not simply a physical YM2612 versus YM3438. Chip-output modes and
status-read behavior are separate. The current checkpoint implementation rejects
the Nuked backend. A source-verified report and bounded native probe are being
prepared before selecting any public control.
