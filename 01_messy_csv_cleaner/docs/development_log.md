# Development Log

## 12 July 2026

Created the initial CSV cleaning script.

Implemented:
- blank-row removal
- duplicate detection
- name capitalisation
- lowercase email formatting
- date normalisation
- currency-symbol removal
- clean CSV export
- text summary export

Verified using the included sample data:
- 6 input rows
- 4 clean output rows
- 1 blank row removed
- 1 duplicate row removed

Added automated tests and supporting documentation.

## Next Objective

Add input validation for missing columns and malformed records.
