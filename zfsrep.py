#!/usr/bin/env python

# Program name:   zfsrep.py
# Author:			Wim Olivier - http://github.com/wimolivier/zfsrep - email: wimolivier@gmail.com
# Purpose:			Replicate ZFS filesystems from SRC server to DST server
# Version:			1.0

''' TODO:				
                     (1) monitor fs free space (put minfree field into config file) - MAYBE
                     (2) local logfile
                     (3) email alerts
'''

import os
import sys
import subprocess
from zfslib import *

if len(sys.argv) == 1:
  print "ZFSREP:\t\tReplicate ZFS volumes/filesystems incrementally over TCP/IP from a source host to a destination host using SSH.\n"
  print "Written by:\tWim Olivier - http://github.com/wimolivier/zfsrep"
  print "Requires:\tPython 2.4+\n"
  print "USAGE:\tpython zfsrep.pyc src_host dst_host\n"
  sys.exit(0)

timestamp = int(time())

logfile = open('/opt/zfsrep/zfsrep.log', 'w')

# Make sure it don't run more than once at a time
if os.path.exists('/tmp/zfsrep.pid'):
  print "ZFSREP is already running or a stale/old PID file exists.  Check /tmp/zfsrep.pid."
  sys.exit(1)
else:
  pid = os.getpid()
  pidfile = open('/tmp/zfsrep.pid', 'w')
  pidfile.write(str(pid))

# Close open files and remove pidfile
def cleanup():
  logfile.close()
  pidfile.close()
  os.remove('/tmp/zfsrep.pid')

# Establish src/dst hosts, read in the config file and create a object to work with
src_host = sys.argv[1]
dst_host = sys.argv[2]
configfile = open('/opt/zfsrep/zfsrep.conf').readlines()
rep = zfsrep(configfile, src_host, dst_host)
rep.timestamp = timestamp

# If not initialized yet, create initial snapshots, send them to DST, and exit the program
if rep.initialized() == False:
  print "No snapshots exist on SRC host: %s.  Creating initial snapshots now..." % src_host
  print "Will create initial snapshots on the following filesystems %r" % sorted(rep.src_snapmap.keys())
  for fs in sorted(rep.src_snapmap.keys()):
    initial_snapname = rep.create_snap(fs)
    print "Initial snapshot %s created on source fs %s" % (initial_snapname, fs)
    print "Sending snapshot %s to %s...\n" % (initial_snapname, dst_host)
    rep.send_init_snap(initial_snapname)
  print "DONE."
  cleanup()
  sys.exit(0)

# Take a snapshot for each SRC filesystem
print "Take new snaps..."
print "=" * 50
for fs in sorted(rep.src_snapmap.keys()):
  snap_name = rep.create_snap(fs)
  rep.src_snapmap[fs].append(snap_name)
  print "Taking snap %s" % rep.new_snap_name
print "\n"

# Send new snapshots to DR
print "Send new snaps to %s..." % dst_host
print "=" * 50
for fs in sorted(rep.src_snapmap.keys()):
  print "Sending incremental snapshot (diff) between snapshots %s and %s to %s" % (rep.src_snapmap[fs][-2], rep.src_snapmap[fs][-1], rep.dst_host)
  rep.send_incr_snap(rep.src_snapmap[fs][-2], rep.src_snapmap[fs][-1])
print "\n"

# Delete old snapshots on SRC host
print "Delete old snaps on %s" % src_host
print "=" * 50
for fs in sorted(rep.src_snapmap.keys()):
  src_max_snaps_to_keep = int(rep.fsnames[fs][0])
  print "Will delete these snaps of filesystem %s on %s: %r" % (fs, src_host, rep.src_snapmap[fs][:-src_max_snaps_to_keep])
  src_snaps_to_delete = rep.src_snapmap[fs][:-src_max_snaps_to_keep]
  rep.delete_src_snaps(src_snaps_to_delete)
print "\n"

# Delete old snapshots on DST host
print "Delete old snaps on %s" % dst_host
print "=" * 50
for fs in sorted(rep.dst_snapmap.keys()):
  if int(rep.fsnames[fs][1]) < 2:
    dst_max_snaps_to_keep = int(rep.fsnames[fs][1])
  else:
    dst_max_snaps_to_keep = int(rep.fsnames[fs][1]) - 1
  print "Will delete these snaps of filesystem %s on %s: %r" % (fs, dst_host, rep.dst_snapmap[fs][:-dst_max_snaps_to_keep])
  dst_snaps_to_delete = rep.dst_snapmap[fs][:-dst_max_snaps_to_keep]
  rep.delete_dst_snaps(dst_snaps_to_delete)
print "\n"

cleanup()
