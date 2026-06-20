import json
import os
import fcntl
import tempfile
from pathlib import Path


DATA_FILE = os.path.expanduser("~/.tea_shop.json")


def _get_default_data():
    return {
        "teas": {},
        "sales": [],
        "restocks": []
    }


def load_data():
    if not os.path.exists(DATA_FILE):
        return _get_default_data()
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return _get_default_data()
        data.setdefault("teas", {})
        data.setdefault("sales", [])
        data.setdefault("restocks", [])
        return data
    except (json.JSONDecodeError, IOError):
        return _get_default_data()


def save_data(data):
    dir_path = os.path.dirname(DATA_FILE)
    os.makedirs(dir_path, exist_ok=True)

    fd = os.open(DATA_FILE, os.O_WRONLY | os.O_CREAT, 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        tmp_fd, tmp_path = tempfile.mkstemp(dir=dir_path, suffix=".tmp")
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, DATA_FILE)
        except Exception:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def atomic_update(updater):
    fd = os.open(DATA_FILE, os.O_RDWR | os.O_CREAT, 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)

        try:
            os.lseek(fd, 0, os.SEEK_SET)
            raw = b""
            while True:
                chunk = os.read(fd, 4096)
                if not chunk:
                    break
                raw += chunk
            content = raw.decode("utf-8")
            if content:
                data = json.loads(content)
            else:
                data = _get_default_data()
        except (json.JSONDecodeError, OSError):
            data = _get_default_data()

        if not isinstance(data, dict):
            data = _get_default_data()
        data.setdefault("teas", {})
        data.setdefault("sales", [])
        data.setdefault("restocks", [])

        result = updater(data)

        new_content = json.dumps(data, ensure_ascii=False, indent=2)
        os.lseek(fd, 0, os.SEEK_SET)
        os.ftruncate(fd, 0)
        os.write(fd, new_content.encode("utf-8"))
        os.fsync(fd)

        return result
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)
