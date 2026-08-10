---
name: invoice-lines
description: Extract line items from invoice and receipt PDFs into CSV. Use whenever a user wants tabular data (line items, quantities, prices, totals) pulled out of a PDF invoice or receipt.
---

## Extract

Run `scripts/extract.py <pdf_path>`. It writes CSV to stdout with columns `vendor,date,sku,qty,unit_price,total`.

If the invoice uses a non-USD currency or mixes currencies across line items, add `--currency <code>` (e.g. `--currency EUR`) so amounts parse against the right currency instead of as bare numbers.

## When extraction fails

Exit code 3 means the PDF has no extractable text layer — it's a scanned image, not real text. OCR it first (e.g. `ocrmypdf <in.pdf> <out.pdf>`), then run `extract.py` on the OCR'd file.

## Before returning results

Sum the `total` column and compare it against the total stated on the invoice itself. Extraction is complete only when the two match; a mismatch means a line was split, merged, or missed, and the CSV needs re-checking against the PDF before it's handed back.