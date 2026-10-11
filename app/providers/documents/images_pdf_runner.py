"""Bound image decoding/PDF generation in a private worker child process."""

import resource
import sys
from pathlib import Path


def main():
    directory, orientation, count = sys.argv[1:]
    count = int(count)
    if not 1 <= count <= 5 or orientation not in {"auto", "portrait", "landscape"}:
        raise ValueError("invalid internal arguments")
    for limit, value in (
        (resource.RLIMIT_AS, 512 * 1024 * 1024),
        (resource.RLIMIT_CPU, 25),
        (resource.RLIMIT_FSIZE, 10 * 1024 * 1024),
        (resource.RLIMIT_CORE, 0),
    ):
        resource.setrlimit(limit, (value, value))
    from app.builders.images_pdf import build

    root = Path(directory)
    data = [root.joinpath(f"{index}.image").read_bytes() for index in range(count)]
    root.joinpath("result.pdf").write_bytes(build(data, orientation=orientation))


if __name__ == "__main__":
    main()
