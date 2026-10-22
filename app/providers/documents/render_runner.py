"""Private launcher for source-owned Word documents, with fixed export options."""

import os
import resource
import sys
from pathlib import Path


def main():
    binary, source, output, profile = sys.argv[1:]
    for limit, value in (
        (resource.RLIMIT_AS, 1024 * 1024 * 1024),
        (resource.RLIMIT_CPU, 60),
        (resource.RLIMIT_FSIZE, 10 * 1024 * 1024),
        (resource.RLIMIT_CORE, 0),
    ):
        resource.setrlimit(limit, (value, value))
    args = [
        binary,
        "--headless",
        "--nologo",
        "--nodefault",
        "--norestore",
        "--nolockcheck",
        "--unaccept=all",
        "-env:UserInstallation=" + Path(profile).as_uri(),
        "--convert-to",
        "pdf:writer_pdf_Export",
        "--outdir",
        output,
        source,
    ]
    os.execve(
        binary,
        args,
        {
            "PATH": "/usr/bin:/bin",
            "LANG": "C.UTF-8",
            "HOME": str(Path(profile).parent),
            "TMPDIR": str(Path(profile).parent),
            "OMP_THREAD_LIMIT": "1",
        },
    )


if __name__ == "__main__":
    main()
