# Product 003 — Smart File Organiser

![Cooke Automation Systems](../brand/logo.svg)

A preview-first file organisation tool that classifies mixed folders, handles filename collisions safely and records every action in an auditable manifest.

## The problem

Downloads, project handovers and shared folders quickly become difficult to navigate. Manual sorting is slow, inconsistent and risky when files share a name or need to be moved rather than copied.

## The product

Product 003 turns a mixed folder into a clear structure without hiding what it intends to do. Preview mode is the default. An applied run produces a JSON manifest, CSV audit report, branded HTML report and—when move mode is selected—an undo path.

## Key features

- Friendly categories for documents, spreadsheets, images, video, audio, archives and source code
- Custom category rules through JSON configuration
- Copy or move workflows
- Recursive folder support
- Collision-safe filenames such as `report_2.pdf`
- SHA-256 integrity hash for every source file
- Preview-first operation; changes require `--apply`
- Reversible move operations using the completed manifest
- Branded, responsive HTML summary
- Local processing with no network access

## Demonstration

From this product folder:

```bash
python3 run.py --clean-demo-output
```

This creates a non-destructive preview from `sample_messy_folder`.

To create an organised copy:

```bash
python3 run.py --clean-demo-output --apply
```

To organise another folder:

```bash
python3 run.py "/path/to/messy-folder" \
  --destination "/path/to/organised-folder" \
  --mode copy \
  --recursive \
  --apply
```

Move mode can be reversed:

```bash
python3 run.py --undo outputs/completed_manifest.json
```

## Outputs

| File | Purpose |
|---|---|
| `preview_manifest.json` | Exact proposed actions before execution |
| `completed_manifest.json` | Executed actions and undo source |
| `audit_report.csv` | Reviewable record for Excel or another system |
| `organisation_report.html` | Branded executive summary and audit table |
| `organised_files/` | Demonstration output when `--apply` is used |

## Testing

```bash
python3 -m unittest discover -s tests -v
```

Tests cover classification, copy behaviour, collision handling, move rollback and unsafe destination rejection.

## Safety notes

- Preview is always the default.
- Hidden files are ignored.
- Existing destination files are never overwritten.
- Undo refuses to overwrite a restored source path.
- Copy mode intentionally has no undo operation because the originals remain unchanged.

Version 1.0.0 — Cooke Automation Systems
