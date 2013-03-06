import subprocess
from time import time


class zfsrep(object):

  def __init__(self, rawconfig, src_host, dst_host):
    '''Parse config of filesystems to replicate.
       Get the current snapshots for each filesystem.
    '''

    self.rawconfig = rawconfig
    self.src_host = src_host
    self.dst_host = dst_host
    self.config = []

    # Strip the CRLF's from the list items
    for line in self.rawconfig:
      self.config.append(line.strip())

    # Create a list containing the filesystem names (format:  pool/filesystem)
    self.fsnames = dict()
    for i in self.config:
      fsname = i.split(':')
      #fsname = str(fsname[0] + '/' + fsname[1])      # removed because of old config file format
      self.fsnames[fsname[0]] = [fsname[1], fsname[2]]
      #self.fsnames.append(fsname[0])

    # SRC host: Create a dictionary containing KEY[filesystem]:VALUE[list of current snapshots) pairs
    self.src_snapmap = dict()
    self.src_snaps = []
    self.init_src_snaps = []        # keeps a list of initial snapshots if there are any
    for fs in self.fsnames.keys():
      src_snaps_output = subprocess.Popen(["zfs", "list", "-t", "snapshot", "-Hr", fs], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      for w in src_snaps_output.stdout.readlines():
        init_src_snap = self.src_snaps.append(w.strip().split('\t')[0])
        self.init_src_snaps.append(init_src_snap)
      self.src_snapmap[fs] = sorted(self.src_snaps)
      self.src_snaps = []          # clear the list again
     
    # DST host: Create a dictionary containing KEY[filesystem]:VALUE[list of current snapshots) pairs
    self.dst_snapmap = dict()
    dst_snaps = []
    for fs in self.fsnames.keys():
      dst_snaps_output = subprocess.Popen(["ssh", self.dst_host, "zfs", "list", "-t", "snapshot", "-Hr", fs], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      for x in dst_snaps_output.stdout.readlines():
        dst_snaps.append(x.strip().split('\t')[0])
      self.dst_snapmap[fs] = dst_snaps
      dst_snaps = []          # clear the list again

  def initialized(self):
    if len(self.init_src_snaps) == 0:
      snaps_exist = False
    else:
      snaps_exist = True
    return snaps_exist

  def create_snap(self, src_fs):
    '''return new_snap_name'''
    self.new_snap_name = '%s@zfsrep_%s' % (src_fs, self.timestamp)
    retcode = subprocess.call(["zfs", "snapshot", "%s@zfsrep_%s" % (src_fs, self.timestamp)])
    return self.new_snap_name 

  def send_init_snap(self, initial_snapname):
    subprocess.call("zfs send '%s' | ssh %s zfs recv -F '%s'" % (initial_snapname, self.dst_host, initial_snapname), shell=True)

  def send_incr_snap(self, old_snap, new_snap):
    subprocess.call("zfs send -i '%s' '%s' | ssh %s zfs recv -F '%s'" % (old_snap, new_snap, self.dst_host, new_snap), shell=True)

  def delete_src_snaps(self, snaplist):
    for oldsnap in snaplist:
      print "Deleting %s on %s" % (oldsnap, self.src_host)
      subprocess.call("zfs destroy %s" % oldsnap, shell=True) 
    print "\n"

  def delete_dst_snaps(self, snaplist):
    for oldsnap in snaplist:
      print "Deleting %s on %s" % (oldsnap, self.dst_host)
      subprocess.call("ssh %s zfs destroy %s" % (self.dst_host, oldsnap), shell=True)
    print "\n"
