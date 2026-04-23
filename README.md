# dt - Natural Language Data Transformer CLI

Transform structured data using plain English. Pipe data in, describe what you want, get results out.

```bash
cat sales.csv | dt - "group by region, sum revenue, sort descending"
dt data.json "filter where age > 30" --out csv
dt contacts.csv "remove empty rows, dedupe on email" --preview
```

**The gap it fills:** `jq` is JSON-only with hard syntax. `awk`/`mlr` require learning query languages. PandasAI is a Python library, not a CLI. `dt` is pipe-friendly, format-agnostic, and plain English.

## How It Works

1. Input data is read from stdin or a file, format auto-detected
2. Only the **schema** (column names, types) and 3 sample rows are sent to the LLM
3. The LLM generates Polars transformation code
4. Code is **validated via AST analysis** (blocks dangerous imports/calls) before execution
5. Results are output in your chosen format

**Your data stays local.** Only the schema and a small sample leave your machine.

## Install

```bash
pip install dt-cli
```

Requires Python 3.11+.

## Quick Start

```bash
# Set your API key (Claude is the default backend)
export ANTHROPIC_API_KEY=your-key

# Transform a CSV
dt sales.csv "group by region, calculate total and average revenue"

# Pipe from stdin
cat data.json | dt - "filter where status is active" --out csv

# Convert between formats
dt data.csv "keep all rows" --out json
dt data.json "keep all rows" --out yaml

# Preview first 10 rows
dt big_dataset.csv "sort by date descending" --preview

# See what code was generated
dt data.csv "pivot by quarter" --show-code

# Use a local model (no API key needed)
dt data.csv "rename columns to snake_case" --backend ollama --model codellama
```

## Supported Formats

| Format | Read | Write | Auto-detect |
|--------|------|-------|-------------|
| CSV    | Yes  | Yes   | Extension + content |
| TSV    | Yes  | Yes   | Extension + content |
| JSON   | Yes  | Yes   | Extension + content |
| JSONL  | Yes  | Yes   | Extension + content |
| YAML   | Yes  | Yes   | Extension + content |
| XML    | Yes  | Yes   | Extension + content |
| Excel  | Yes  | Yes   | Extension |

## Saved Aliases

Create reusable named transforms:

```bash
# Save an alias
dt alias save clean-contacts "remove empty rows, normalize phone numbers, dedupe on email"

# Use it
dt contacts.csv "clean-contacts"

# List all aliases
dt alias list

# Delete one
dt alias delete clean-contacts
```

## Caching

Generated code is cached by (instruction + schema hash). Repeat the same transform on data with the same structure and it runs instantly with no API call.

```bash
dt cache stats    # see cache size
dt cache clear    # clear it
```

## Options

```
dt [SOURCE] INSTRUCTION [OPTIONS]

Arguments:
  SOURCE       File path or "-" for stdin (default: -)
  INSTRUCTION  Plain English transform description

Options:
  -f, --format    Input format (csv, json, yaml, xml, tsv, jsonl, excel)
  -o, --out       Output format (default: same as input)
  -b, --backend   LLM backend: claude or ollama (default: claude)
  -m, --model     Model name override
  -p, --preview   Show only first 10 rows
  --show-code     Print generated Polars code to stderr
  --no-cache      Skip cache lookup and storage
  --no-sample     Don't send sample rows to LLM (privacy mode)
  -V, --version   Show version
```

## Security

- **AST validation** blocks `import os`, `subprocess`, `open()`, `exec()`, `eval()`, and other dangerous operations before any generated code runs
- **No personal data** sent to LLM by default - only column names, types, and 3 sample rows. Use `--no-sample` for zero rows
- **API keys** read from environment variables only, never stored by the tool
- **No elevated permissions** required

## LLM Backends

### Claude (default)
```bash
export ANTHROPIC_API_KEY=your-key
dt data.csv "transform instruction"
```

### Ollama (local, offline)
```bash
# Install Ollama and pull a model first
ollama pull qwen2.5-coder:7b

dt data.csv "transform instruction" --backend ollama
dt data.csv "transform instruction" --backend ollama --model codellama
```

## Development

```bash
git clone https://github.com/jlldavies/dt.git
cd dt
pip install -e ".[dev]"
pytest                          # 160 tests
pytest --cov=dt                 # with coverage (>90%)
```

## License

MIT
