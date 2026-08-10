---
name: invoice-lines
description: Extracting line items from invoice or receipt PDFs into CSV. Use when the user wants tabular data (SKUs, quantities, prices, totals) pulled out of a PDF invoice or receipt.
---

Extract line items from an invoice/receipt PDF into CSV using the bundled `scripts/extract.py` (pdfplumber-based).

## Steps

1. Run `python scripts/extract.py <pdf_path>`. It writes CSV to stdout with columns `vendor,date,sku,qty,unit_price,total`.
   - **Exit code 3** means the PDF has no text layer (scanned image). OCR it first (e.g. `ocrmypdf <pdf_path> <ocr_path>`), then re-run extract.py on the OCR'd file. Don't retry the original path — it will exit 3 again.
   - **Multi-currency invoice** (line items priced in more than one currency): add `--currency <code>` (e.g. `--currency EUR`) so amounts on that page aren't misread as the wrong currency.
2. Sum the `total` column and compare it against the invoice's own stated total (e.g. "Total Due", "Grand Total" printed on the document). They must match. If they don't, don't hand off the CSV silently — tell the user the sums disagree and by how much; it usually means a missed, duplicated, or misparsed line.
3. Return the CSV (or write it to the path the user asked for).