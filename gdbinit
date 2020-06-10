add-auto-load-safe-path /
 
set pagination off
set print object on
 
set print static-members off
set print pretty on
#set print elements 0

source .gdbinit

# register boost pretty printers
python
import sys, pathlib
sys.path.insert(1, os.path.join(pathlib.Path.home(), 'Boost-Pretty-Printer'))
import boost
boost.register_printers(boost_version=(1,60,0))
print("Loaded boost pretty printers")
end
