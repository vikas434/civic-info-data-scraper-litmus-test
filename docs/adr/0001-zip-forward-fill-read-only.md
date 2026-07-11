# ZIP code is forward-filled in memory only, never written back to the workbook

The input workbook intentionally leaves the ZIP cell blank for all rows after the first in each ZIP Group, so that the sheet stays clean when uploaded to Google Sheets. The system forward-fills the ZIP value in memory at read time to correctly group rows, but never writes a ZIP value back to any cell. This prevents the workbook from accumulating repeated ZIP values across runs.
