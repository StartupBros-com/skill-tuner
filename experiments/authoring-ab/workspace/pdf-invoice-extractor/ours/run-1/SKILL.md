---
name: invoice-lines
description: Extract line items from invoice or receipt PDFs into CSV. Use whenever a user wants tabular data pulled out of one.
---

## Extract

Run the bundled script against the PDF:

```
python scripts/extract.py <path-to-pdf>
```

It writes CSV to stdout with columns `vendor,date,sku,qty,unit_price,total`. Redirect to a file if the user wants one saved.

## Gotchas

- **Scanned PDFs** — `extract.py` reads text layers only; a scanned (image-only) PDF has none, and the script exits with code 3. Check the exit code. On exit 3, OCR the PDF first (e.g. `ocrmypdf`) and re-run extract.py against the OCR'd file, not the original.
- **Multi-currency invoices** — pass `--currency <code>` (e.g. `--currency EUR`) when the invoice states amounts in a non-USD currency, so unit_price and total are tagged correctly. Without it, the script assumes USD and a mixed-currency document will produce wrong totals silently.
- **Total cross-check** — after extraction, sum the `total` column and compare it against the invoice's own stated total (usually printed near the document's bottom). If they match within rounding, extraction is complete. If they don't, re-check for parsing errors (merged or missing rows) and flag the mismatch to the user before reporting the extraction as done.