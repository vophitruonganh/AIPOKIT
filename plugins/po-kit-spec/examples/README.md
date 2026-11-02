# Examples
- `expense-tracker/`: a tiny synthetic English spec (markdown + config) that builds a 15-page SRS. It is invented sample data, not crawled from any product. Use it to see the expected structure and to smoke-test the scripts:
  `python3 scripts/build_srs.py examples/expense-tracker/md out.docx "" examples/expense-tracker/config.json`
  (It is minimal on purpose, so `spec_lint.py` will report the blocks it leaves out.)
