from pathlib import Path

UPLOAD_DIR = Path("app/data/uploads")
TORRENT_DIR = Path("app/data/torrents")

DANGEROUS_CONTENT_TYPES = [
    "application/x-msdownload",     # .exe
    "application/x-msdos-program",  # .bat, .cmd
    "application/x-sh",             # .sh
    "application/x-python",         # .py
    "application/javascript",       # .js
    "application/x-php",            # .php
    "application/x-csh",            # .csh
    "text/html",                    # .html
    "text/javascript",              # .js
    "application/x-ruby",           # .rb
    "application/x-java",           # .jar
]