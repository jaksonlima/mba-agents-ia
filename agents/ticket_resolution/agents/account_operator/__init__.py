import sys
from pathlib import Path

project_root = str(Path(__file__).resolve().parents[2])

if project_root not in sys.path:
    sys.path.append(project_root)

from ...account_operator import agent
