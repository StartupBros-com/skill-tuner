---
name: invoice-lines
description: Extracting line items from invoice or receipt PDFs into CSV. Use when a user wants tabular data (quantities, prices, SKUs) out of an invoice or receipt PDF.
---

Extract line items from invoice/receipt PDFs into CSV via `scripts/extract.py` (pdfplumber-based).

## Steps

1. Run `python scripts/extract.py <pdf_path>`, capturing stdout and the exit code. Done when you have either a CSV or a nonzero exit code.
2. Exit code 3 means the PDF has no text layer (it's scanned). OCR the file (e.g. `ocrmypdf`) and rerun step 1 against the OCR'd PDF. Done when the script exits 0.
3. If line items on the invoice carry more than one currency symbol or code, rerun with `--currency <ISO-code>` set to the currency you want extracted — the script cannot infer currency from a mixed page and will misparse amounts if left unset.
4. Sum the CSV's `total` column and compare it to the invoice's own printed grand total. Done when the two match. If they don't, a row is misparsed (merged cells, skipped line, wrong currency) — find and fix it before handing back the CSV.

## Output

CSV columns: `vendor,date,sku,qty,unit_price,total`.