## create ics files 

Files:

- `create_ics.py` - used to download data from ID and outputs calendar into OUTPUT
- `update.sh` - read IDs from `list.txt` and write resulting ical files to `./calendars/`
  - `list.txt` - list of IDs (1 ID per line)
- `plan-to-ics.service`, `schedule-plan-to-ics.timer` - systemd services to run `create_ics.py` automatically every day


### quickstart

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# replace $ID and $OUTFILE with your values
python3 create_ics.py --id $ID --output $OUTFILE
```

Supported python versions: `3.10`, `3.11`, `3.12`
