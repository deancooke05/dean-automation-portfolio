# Cooke Automation Systems

![Cooke Automation Systems](brand/logo.svg)

Twenty practical automation products designed to remove repetitive work, improve data quality and make everyday business processes easier to manage.

This catalogue is developed independently by Dean Cooke alongside an MEng Aerospace Engineering with Pilot Studies degree at UWE Bristol. Every product is built around clear scope, safe defaults, local processing, documented examples and verifiable outputs.

## Product catalogue

| No. | Product | Outcome |
|---:|---|---|
| 001 | [Messy CSV Cleaner](01_messy_csv_cleaner) | Turns inconsistent customer data into a reliable CSV export |
| 002 | [Excel Report Generator](02_excel_report_generator) | Produces a polished executive workbook from raw sales data |
| 003 | [Smart File Organiser](03_file_organiser) | Plans and applies safe organisation by file type |
| 004 | [Invoice Renamer](04_invoice_renamer) | Creates consistent, searchable invoice filenames |
| 005 | [Versioned Backup Tool](05_folder_backup_tool) | Creates verified ZIP backups with integrity manifests |
| 006 | [Price Tracker Analyser](06_price_tracker_demo) | Explains price movement from offline tracking exports |
| 007 | [Tender Opportunity Scorer](07_tenderscout_case_study) | Ranks tender opportunities against business criteria |
| 008 | [Duplicate File Finder](08_duplicate_file_finder) | Finds duplicates using cryptographic content hashes |
| 009 | [Document Pack Builder](09_document_pack_builder) | Combines documents into a structured review pack |
| 010 | [Image Library Auditor](10_image_library_auditor) | Produces image renaming and integrity manifests |
| 011 | [Log Insight Analyser](11_log_insight_analyser) | Summarises severity and repeated application errors |
| 012 | [Data Quality Auditor](12_data_quality_auditor) | Identifies missing values and duplicate records |
| 013 | [Quote Builder](13_quote_builder) | Calculates itemised quotes, tax and final totals |
| 014 | [Expense Categoriser](14_expense_categoriser) | Applies transparent business expense rules |
| 015 | [Inventory Reorder Planner](15_inventory_reorder_planner) | Calculates reorder points and purchase quantities |
| 016 | [Schedule Conflict Checker](16_schedule_conflict_checker) | Detects overlapping events before booking problems occur |
| 017 | [Folder Change Monitor](17_folder_change_monitor) | Creates and compares cryptographic folder snapshots |
| 018 | [Client Handover Packager](18_client_handover_packager) | Validates and packages delivery folders with checksums |
| 019 | [Service SLA Dashboard](19_service_sla_dashboard) | Summarises ticket resolution and SLA performance |
| 020 | [Client Lead Ranker](20_client_lead_ranker) | Prioritises enquiries by fit, urgency and budget |

## Design language

The catalogue uses the Cooke Automation Systems visual identity: deep navy, warm gold, pearl white and restrained steel-grey typography. The aim is quiet confidence rather than decorative complexity.

## Safety and privacy

- Local-first processing; no customer data is transmitted by the tools.
- File-changing products preview their actions by default.
- Example data is synthetic.
- Outputs are auditable JSON, CSV, ZIP or Excel files.
- Automated tests cover the shared calculation and validation engine.

## Verification

From the repository root:

```bash
python3 -m unittest discover -s tests -v
python3 -m unittest discover -s 01_messy_csv_cleaner/tests -v
(cd 02_excel_report_generator && python3 -m unittest discover -s tests -v)
```

## Freelance services

The products support clearly scoped Fiverr and Upwork services including Python automation, Excel and CSV processing, reporting, file organisation, operational analysis and reusable workflow tools.
