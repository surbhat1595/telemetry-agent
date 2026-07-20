#!/usr/bin/env python3
"""Build a .deb without GNU tar (Resolute openat2/ENOSYS workaround)."""

from __future__ import annotations

import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path


def under(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def add_tree(tar: tarfile.TarFile, root: Path, exclude: Path | None = None) -> None:
    for path in sorted(root.rglob("*")):
        if exclude is not None and (path == exclude or under(path, exclude)):
            continue
        arcname = "./" + path.relative_to(root).as_posix()
        tar.add(path, arcname=arcname, recursive=False)


def parse_control(control: Path) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in control.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith(" "):
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip()
    return fields


def main() -> int:
    pkg_dir = Path("debian/percona-telemetry-agent")
    control_dir = pkg_dir / "DEBIAN"
    control_file = control_dir / "control"
    if not control_file.is_file():
        print(f"missing {control_file}", file=sys.stderr)
        return 1

    fields = parse_control(control_file)
    name = fields["Package"]
    version = fields["Version"]
    arch = fields.get("Architecture") or subprocess.check_output(
        ["dpkg", "--print-architecture"], text=True
    ).strip()
    deb_name = f"{name}_{version}_{arch}.deb"
    out_deb = Path("..") / deb_name

    with tempfile.TemporaryDirectory(prefix="resolute-deb-") as tmp:
        tmpdir = Path(tmp)
        (tmpdir / "debian-binary").write_text("2.0\n", encoding="utf-8")

        control_tar = tmpdir / "control.tar.gz"
        with tarfile.open(control_tar, "w:gz", format=tarfile.GNU_FORMAT) as tar:
            add_tree(tar, control_dir)

        data_tar = tmpdir / "data.tar.gz"
        with tarfile.open(data_tar, "w:gz", format=tarfile.GNU_FORMAT) as tar:
            add_tree(tar, pkg_dir, exclude=control_dir)

        if out_deb.exists():
            out_deb.unlink()
        # `ar` does not use GNU tar's openat2 path
        subprocess.check_call(
            ["ar", "rD", str(out_deb.resolve()), "debian-binary", "control.tar.gz", "data.tar.gz"],
            cwd=tmpdir,
        )

    print(f"built {out_deb} without GNU tar")
    return 0


if __name__ == "__main__":
    sys.exit(main())
