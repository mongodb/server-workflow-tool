# Default bashrc for Server development

export NINJA_STATUS='[%f/%t (%p) %es] '

function buildninjaic() {
    ./buildscripts/scons.py  \
        CCFLAGS='-gsplit-dwarf' \
        --variables-files=etc/scons/mongodbtoolchain_stable_gcc.vars \
        MONGO_VERSION=$(git describe --abbrev=0 | tail -c+2) \
        --ssl \
        ICECC=icecc CCACHE=ccache --ninja \
        build.ninja
}

alias cr="~/kernel-tools/codereview/upload.py --check-clang-format --check-eslint"
alias activate="source python3-venv/bin/activate"

# gdb setup
export PATH="/opt/mongodbtoolchain/gdb/bin:${PATH}"

# vim extension setup
export PATH="/opt/cmake/bin:/opt/rtags-2.38/bin:${PATH}"
export MONGO_REPO="$HOME/mongo"
