"""Check experiment inputs and the frozen baseline using only the Python standard library."""
from pathlib import Path
import hashlib
import json

folder = Path(__file__).resolve().parent
root = folder.parents[1]
manifest = json.loads((folder / 'data_manifest.json').read_text())
for name, expected in manifest['files'].items():
    actual = hashlib.sha256((root / name).read_bytes()).hexdigest()
    if actual != expected:
        raise SystemExit(f'Data checksum mismatch: {name}')
for name, expected in json.loads((folder / 'snapshot_hashes.json').read_text()).items():
    actual = hashlib.sha256((folder / 'source_snapshot' / name).read_bytes()).hexdigest()
    if actual != expected:
        raise SystemExit(f'Baseline checksum mismatch: {name}')
print('PASS: input data and frozen baseline checksums')
