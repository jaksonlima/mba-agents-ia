import sys
from pathlib import Path

# Calcula o caminho da raiz do projeto (sobe 2 níveis a partir de ticket_receptionist)
project_root = str(Path(__file__).resolve().parents[2])

# Adiciona a raiz ao Python se ela ainda não estiver lá
if project_root not in sys.path:
    sys.path.append(project_root)