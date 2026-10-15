"""Encrypted account keys on the current server; never tracked in Git."""
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from cryptography.fernet import Fernet, InvalidToken

ROOT = Path(__file__).parent / '.studio-data'

def cipher():
    ROOT.mkdir(exist_ok=True)
    path = ROOT / 'vault.key'
    try:
        with path.open('xb') as f:
            f.write(Fernet.generate_key())
        os.chmod(path, 0o600)
    except FileExistsError:
        pass
    return Fernet(path.read_bytes())

@contextmanager
def connect():
    ROOT.mkdir(exist_ok=True)
    db = sqlite3.connect(ROOT / 'keys.sqlite3', timeout=10)
    db.execute('CREATE TABLE IF NOT EXISTS keys (owner TEXT, provider TEXT, secret BLOB, PRIMARY KEY(owner,provider))')
    try:
        with db:
            yield db
    finally:
        db.close()

def save(owner, provider, key):
    if not owner:
        raise ValueError('Missing account')
    token = cipher().encrypt(key.encode())
    with connect() as db:
        db.execute('INSERT OR REPLACE INTO keys VALUES (?,?,?)', (owner, provider, token))

def load(owner):
    if not owner:
        return {}
    result = {}
    crypt = cipher()
    with connect() as db:
        for provider, token in db.execute('SELECT provider,secret FROM keys WHERE owner=?', (owner,)):
            try:
                result[provider] = crypt.decrypt(token).decode()
            except (InvalidToken, UnicodeError):
                continue
    return result
