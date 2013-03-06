About
=====
ZFSREP automates the replication and management of ZFS volumes (raw) or filesystems (cooked) at block level using ZFS 'send' and 'recv'.


Requirements
============
Both the source and destination pools and volumes/filesystems need to already exist.
ZFSREP will take care of taking initial snapshots on the SRC host, so ideally there should be no existing snapshots on any pools/volumes/filesystems that you want ZFSREP to replicate.


zfsrep.conf file format: (a single volume/fs per line)
========================
poolname/fsname:max_src_snap_to_keep:max_dst_snaps_to_keep

or

poolname/volumename:max_src_snap_to_keep:max_dst_snaps_to_keep


Example:
--------
mybigdatapool/data1:2:5
mybigdatapool/data2:2:5
mylogpool/archive:1:10


Important Note:
===============
It is NOT permitted to have a snapshot keep count of zero(0), else incremental snapshots will NOT work!!!
