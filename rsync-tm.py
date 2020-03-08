#!/usr/bin/python

import fcntl
import os
import shutil
import subprocess
import sys
import time

SNAP_DEST_DIR = "/Volumes/backup/username"
SNAP_SOURCE_DIR = "/Users/username/" # Trailing slash *required* to select contents
SNAP_DAILY_PREFIX = "snapshot_day_"
SNAP_MONTHLY_PREFIX = "snapshot_month_"
SNAP_MAX_DAILY = 7
SNAP_MAX_MONTHLY = 12
SNAP_TMP = os.path.join(SNAP_DEST_DIR, "snapshot_tmp")
SNAP_MIRROR = os.path.join(SNAP_DEST_DIR, "mirror")
SNAP_RSYNC_CMD = [
        "rsync",                    # rsync makes this all work
        "-rlptgo",                  # Recursive, symlinks, perms, times, group, owner
        "-v",                       # Verbose
        "--delete",                 #deletes old backups
        "--exclude .thumbnails",    #no need to back these up
        "--exclude .cache",         #inflates backups
        "--exclude .gvfs",          #GNOME VFS - Can cause issues and inflate backups of unwated data
        "--exclude .AppleDouble",   #MacOS Annoyance
        "--exclude __MACOSX"        #MacOS Annoyance
        "--exclude .DS_Store"       #MacOS Annoyance
        SNAP_SOURCE_DIR
        SNAP_MIRROR]

#Return list of snapshot dir paths, sorted as newest first, oldest last.
#@prefix: filter only snapshot dirs that start with this string
def _get_snapshots(prefix):
    ret = []
    for name in os.listdir(SNAP_DEST_DIR):
        if name.startswith(prefix):
            path = os.path.join(SNAP_DEST_DIR, name)
            ret.append(path)
    ret.sort(reverse=True)
    return ret

#Write to stdout and flush it, so our output isn't mixed with subprocesses
def _print(msg):
    sys.stdout.write(msg + "\n")
    sys.stdout.flush()

#Delete all but @nr_keep newest snapshots, with their prefix matching @prefix
def _delete_old_snapshots(prefix, nr_keep):
    snapshots = _get_snapshots(prefix)
    snapshots_keep = snapshots[0:nr_keep]
    snapshots_delete = snapshots[nr_keep:]
    for snap in snapshots_keep:
        _print("keeping snapshot      %s" % snap)
    for snap in snapshots_delete:
        _print("deleting old snapshot %s" % snap)
        _delete_directory(snap)

# Blow away a directory. Don't fail if there are read-only subdirectories.
# Fix potential permission problems. (Read-only files aren't a problem for rmtree)
def _delete_directory(path):
    DIR_PERMS = 0755
    for (a,b,c) in os.walk(path):
        os.chmod(a, DIR_PERMS)
    shutil.rmtree(path)

#The snapshot dir names are ascii-sortable. Year, month, and day are fixed length fields.
#This is crash-safe and easier than trying to shuffle .1, .2, .3 dirs on every rotation.
def _get_daily_snapshot_name():
    dt = time.strftime("%Y-%m-%d", time.localtime())
    name = SNAP_DAILY_PREFIX + dt
    return os.path.join(SNAP_DEST_DIR, name)
def _get_monthly_snapshot_name():
    dt = time.strftime("%Y-%m", time.localtime())
    name = SNAP_MONTHLY_PREFIX + dt
    return os.path.join(SNAP_DEST_DIR, name)

#Create or update the SNAP_MIRROR dir using rsync
def _update_mirror():
    _print("Updating base archive: %s" % SNAP_MIRROR)
    args = SNAP_RSYNC_CMD
    _print("Running %s" % args)
    p = subprocess.Popen(args)
    rc = p.wait()
    if rc != 0:
        raise Exception("rsync failed")

#cp -al SNAP_MIRROR to a new snapshot. snap: full path name of snapshot
#Do nothing if @snap already exists. Use a tmp dir (SNAP_TMP) and rename it when successful, for failure safety
def _create_snapshot(snap):
    # Clean up any previous failure
    if os.path.exists(SNAP_TMP):
        _delete_directory(SNAP_TMP)
    if os.path.exists(snap):
        _print("snapshot %s already exists" % snap)
        return
    _print("Linking new snapshot: %s" % snap)
    args = ["cp", "-al", SNAP_MIRROR, SNAP_TMP]
    p = subprocess.Popen(args)
    rc = p.wait()
    if rc != 0:
        raise Exception("cp failed")
    # Success: atomically rename it to an official snapshot
    os.rename(SNAP_TMP, snap)

# Open @path and lock it exlusively. Raises: IOError on failure.
# Return: file object, which you must maintain a reference to (if it is closed, the lock is released).
def _lock_file_exclusively(path):
    _print("Locking file %s" % path)
    lock_file = open(path)
    fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    return lock_file

# Ensure this script is not running concurrently.
# This is a safety feature if cron is calling it too quickly.
def main():
    lock_file = _lock_file_exclusively(sys.argv[0])
    _update_mirror()
    _create_snapshot(_get_daily_snapshot_name())
    _create_snapshot(_get_monthly_snapshot_name())
    _delete_old_snapshots(SNAP_DAILY_PREFIX, SNAP_MAX_DAILY)
    _delete_old_snapshots(SNAP_MONTHLY_PREFIX, SNAP_MAX_MONTHLY)

if __name__ == "__main__":
    main()