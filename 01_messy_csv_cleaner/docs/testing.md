# Testing

Run from the project folder:

```bash
python3 -m unittest discover -s tests -v
```

## Current Checks
- name normalisation
- email normalisation
- supported date formats
- unsupported date preservation
- blank-row detection

## Known Limitations
- Duplicate detection uses customer ID and email.
- Invalid dates are preserved.
- Missing columns are not yet reported clearly.
- Excel files are not yet supported.
