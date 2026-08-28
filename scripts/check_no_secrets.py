from __future__ import annotations
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
patterns=[re.compile(r'sk-ant-[A-Za-z0-9_-]{16,}'),re.compile(r'github_pat_[A-Za-z0-9_]{16,}')]
for path in ROOT.rglob('*'):
    if not path.is_file() or any(x in path.parts for x in ('.git','.venv','__pycache__','.pytest_cache')): continue
    if path.suffix.lower() not in {'.py','.md','.txt','.json','.yml','.yaml','.example','.gitignore'} and path.name not in {'.gitignore'}: continue
    text=path.read_text(encoding='utf-8',errors='ignore')
    if any(p.search(text) for p in patterns): raise SystemExit(f'SECRET CHECK FAIL: {path.relative_to(ROOT)}')
print('SECRET CHECK PASS')
