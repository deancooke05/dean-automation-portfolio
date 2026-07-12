# Product 005 — Versioned Backup Tool

![Cooke Automation Systems](../brand/logo.svg)

Creates verified ZIP backups with a SHA-256 manifest.

## Why it exists

This product removes a repetitive administrative step while keeping the workflow transparent and reviewable. It runs locally and does not transmit customer data.

## Run the demonstration

From the portfolio root:

```bash
python3 05_folder_backup_tool/run.py
```

Results are written to the product's `outputs` folder. File-changing products use preview mode unless `--apply` is explicitly supplied.

## Product standard

- Local-first and privacy-conscious
- Clear input and output contracts
- Safe defaults
- Reusable Python implementation
- Automated portfolio test coverage
- Shared Cooke Automation Systems visual identity

Version 1.0.0
