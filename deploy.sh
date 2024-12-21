#!/usr/bin/env bash
rsync --filter=':- .gitignore' -azP ./ watrunner@glnsk.top:~/plan-to-ics/
