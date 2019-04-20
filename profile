export EDITOR=nano
export PATH=$HOME/bin:$PATH

# Setup virtualenvwrapper.
export VIRTUALENVWRAPPER_PYTHON=$(which python3)
[ -f /usr/local/bin/virtualenvwrapper.sh ] && source /usr/local/bin/virtualenvwrapper.sh
