from pathlib import Path
import re


PIN = re.compile(r"^\s*([A-Za-z0-9_.-]+)==([^\s;]+)")


def _normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _pins(path: str) -> dict[str, str]:
    result = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        match = PIN.match(line)
        if match:
            result[_normalize(match.group(1))] = match.group(2)
    return result


def _assert_locked(expected: dict[str, str], lock_path: str) -> None:
    locked = _pins(lock_path)
    mismatches = {
        name: {"expected": version, "locked": locked.get(name)}
        for name, version in expected.items()
        if locked.get(name) != version
    }
    assert not mismatches, (
        f"{lock_path} is stale; regenerate it for Python 3.10: {mismatches}"
    )


def test_runtime_direct_dependencies_match_lock() -> None:
    _assert_locked(_pins("requirements.txt"), "requirements.lock")


def test_development_direct_dependencies_match_lock() -> None:
    expected = _pins("requirements.txt") | _pins("requirements-dev.txt")
    _assert_locked(expected, "requirements-dev.lock")
