from pathlib import Path
import sys

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE.parent))

from cooke_systems.studio import launch


if __name__ == "__main__":
    launch("020", BASE)
