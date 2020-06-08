add-auto-load-safe-path /
 
set pagination off
set print object on
set scheduler-locking on
 
set print static-members off
set print pretty on
#set print elements 0

source .gdbinit

# set pretty printers
python
import os, sys, glob
pp = glob.glob("/opt/mongodbtoolchain/v3/share/gcc-*/python/libstdcxx/v6/printers.py")
printers = pp[0]
path = os.path.dirname(os.path.dirname(os.path.dirname(printers)))
sys.path.insert(0, path)
from libstdcxx.v6 import register_libstdcxx_printers
register_libstdcxx_printers(gdb.current_objfile())
print("Loaded libstdc++ pretty printers from '%s'" % printers)
end

# register boost pretty printers
python
import sys, pathlib
sys.path.insert(1, os.path.join(pathlib.Path.home(), 'Boost-Pretty-Printer'))
import boost
boost.register_printers(boost_version=(1,60,0))
print("Loaded boost pretty printers")
end
