import sys
from pathlib import Path

GOC = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(GOC / "chung"), str(GOC / "master")]
