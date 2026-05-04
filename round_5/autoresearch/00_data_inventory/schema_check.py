"""Schema check for ROUND_5 raw data.

Verifies that prices_round_5_day_{2,3,4}.csv and trades_round_5_day_{2,3,4}.csv
load cleanly, share the expected columns, and have plausible row counts.

Writes a machine-readable summary to stdout and updates inventory.md.
Run from this directory: `python schema_check.py`.
"""
# TODO: implement once utils/data_loader.py is wired in.