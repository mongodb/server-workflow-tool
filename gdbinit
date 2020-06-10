add-auto-load-safe-path /
 
set pagination off
set print object on
 
set print static-members off
set print pretty on
#set print elements 0

# include venv in the Python path
python
import os, subprocess, sys
try:
    # Execute a Python using the user's shell and pull out the sys.path (for site-packages)
    paths = subprocess.check_output('python -c "import os,sys;print(os.linesep.join(sys.path).strip())"',shell=True).decode("utf-8").split()
    # Extend GDB's Python's search path
    sys.path.extend(paths)
except Exception as e:
    print("Failed to include venv Python path" + str(e))
end

# register boost pretty printers
python
import sys, pathlib
try:
    sys.path.insert(1, os.path.join(pathlib.Path.home(), 'Boost-Pretty-Printer'))
    import boost
    boost.register_printers(boost_version=(1,60,0))
    print("Loaded boost pretty printers")
except Exception as e:
    print("Failed to load the boost pretty printers: " + str(e))
end
