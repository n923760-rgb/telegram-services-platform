"""Private POSIX child launcher, not a customer-facing command interface."""

import os
import resource
import sys


def main():
    source, target, language, *data_dir = sys.argv[1:]
    if language not in {"ara", "eng", "ara+eng"} or len(data_dir) > 1:
        raise ValueError("invalid internal arguments")
    for limit, value in (
        (resource.RLIMIT_AS, 512 * 1024 * 1024),
        (resource.RLIMIT_CPU, 20),
        (resource.RLIMIT_FSIZE, 2 * 1024 * 1024),
        (resource.RLIMIT_CORE, 0),
    ):
        resource.setrlimit(limit, (value, value))
    args = ["/usr/bin/tesseract", source, target, "-l", language, "--oem", "1", "--psm", "3"]
    if data_dir:
        args.extend(["--tessdata-dir", data_dir[0]])
    args.extend(["-c", "tessedit_create_tsv=1"])
    os.execve(args[0], args, {"PATH": "/usr/bin:/bin", "OMP_THREAD_LIMIT": "1", "LANG": "C.UTF-8"})


if __name__ == "__main__":
    main()
