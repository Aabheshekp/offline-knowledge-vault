from pathlib import Path
import os
ROOT=Path(__file__).resolve().parents[2]
LIBRARY_ROOT=Path(os.getenv("VAULT_LIBRARY_ROOT",ROOT/"data"/"library")).resolve()
DB_PATH=Path(os.getenv("VAULT_DB_PATH",ROOT/"data"/"vault.sqlite3"))
CHUNK_SIZE=int(os.getenv("VAULT_CHUNK_SIZE","1100"))
CHUNK_OVERLAP=int(os.getenv("VAULT_CHUNK_OVERLAP","160"))
