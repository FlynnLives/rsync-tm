
# rsync-tm

A simple python script to maintain daily and monthly backups similar to [TimeMachine](https://en.wikipedia.org/wiki/Time_Machine_(macOS)) using [rsync](https://en.wikipedia.org/wiki/Rsync)

Makes daily and monthly snapshots a specific path, hard linked to save space when files don't change.

Features:

* Work's on Mac and Linux, should work on Windows, but not tested
* Daily and monthly parameters can be easily changed
* Each snapshot is created as a temp dir and then renamed only upon success
* The script fails if it's currently already running
* Errors will not pass silently
* The entire script is crash safe; just re-run to retry

## Configuration

**`SNAP_DEST_DIR`**

* Should be on a different drive for redundancy. This can be set to a mounted usb drive, NFS mount, or mounted network path

**`SNAP_SOURCE_DIR`**

* This is the path you are wanting to backup, a trailing slash is required for it to backup properly

**`SNAP_DAILY_PREFIX`**

* You can use this to set the prefix on daily backups

**`SNAP_MONTHLY_PREFIX`**

* You can use this to set the prefix on monthly backups

**`SNAP_MAX_DAILY`**

* The number of daily backups you wish to keep, set to 7 by default

**`SNAP_MAX_MONTHLY`**

* The number of monthly backups you wish to keep, set to 12 by default

**`SNAP_TMP`**

* The temporary directory for your backup, copies to **`SNAP_DEST_DIR\snapshot_tmp`** 

**`SNAP_MIRROR`** - 

**`SNAP_RSYNC_CMD`**

* Calls rsync and passes additional variables to rsync to incrementally mirror **`SNAP_DEST_DIR`** to **`SNAP_SOURCE_DIR`**
* Has a number of exclusions to assist in not backing up annoyances/temporary files

## Usage
The first time you should run the script manually **`python rsync-tm.py`** Do not pass any arguments to the script as this may cause undesired operation
After you are happy with the script you should setup a crontab so it runs automatically 

## Crontab 
You can setup crontab to run this script for you automatically. This works on MacOS and Linux

As yourself open a terminal and type **`crontab -e`**

	0 0 * * * /usr/bin/python /Users/username/scripts/rsync-tm.py >/Volumes/backup/backup-$(date +%Y-%m-%d).log 2>&1
	
This will run the script every day at **Midnight** and pipe the output to the backup drive. It is recommended to use the full path to **python**, you can find this by running **`which python`**. You can of course change the path of the script and output log location to wherever you would like