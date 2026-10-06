# jsonpeek

CLI tool to inspect JSON structure and content.

## Installation

```bash
pip install -e .
```

## Usage

```bash
# Inspect a JSON file
jsonpeek data.json

# Show keys at root
jsonpeek data.json --keys

# Navigate to nested path
jsonpeek data.json --path "data.items[0]"

# Count types recursively
jsonpeek data.json --types

# Read from stdin
cat data.json | jsonpeek
```

## Features

- Navigate nested JSON with dot notation and array indices
- Show structure overview with depth control
- Count type occurrences
- Inspect keys at any path

## Examples

```bash
# Show structure
$ jsonpeek users.json
Type: list
Length: 100

list[100] of dict(8 keys):
  id: int: 1
  name: str: 'Alice Smith'
  email: str: 'alice@example.com'

# Navigate to specific user
$ jsonpeek users.json --path "[5].name"
Type: str
str: 'Bob Jones'

# Count all types
$ jsonpeek data.json --types
  str: 245
  int: 189
  dict: 42
  list: 18
  bool: 12
  null: 3
```

## License

MIT
