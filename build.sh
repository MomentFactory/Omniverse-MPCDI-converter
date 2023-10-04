# Copyright 2023 NVIDIA CORPORATION
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

set -e
CWD="$( cd "$( dirname "$0" )" && pwd )"

# default config is release
CLEAN=false
BUILD=false
GENERATE=false
STAGE=false
CONFIGURE=false
HELP=false
CONFIG=release
HELP_EXIT_CODE=0

DIRECTORIES_TO_CLEAN=(
    _install
    _build
    _repo
    src/usd-plugins/schema/omniExampleCodelessSchema/generated
    src/usd-plugins/schema/omniExampleSchema/generated
    src/usd-plugins/schema/omniMetSchema/generated
)

while [ $# -gt 0 ]
do
    if [[ "$1" == "--clean" ]]
    then
        CLEAN=true
    fi
    if [[ "$1" == "--generate" ]]
    then
        GENERATE=true
    fi
    if [[ "$1" == "--build" ]]
    then
        BUILD=true
    fi
    if [[ "$1" == "--prep-ov-install" ]]
    then
        STAGE=true
    fi
    if [[ "$1" == "--configure" ]]
    then
        CONFIGURE=true
    fi
    if [[ "$1" == "--debug" ]]
    then
        CONFIG=debug
    fi
    if [[ "$1" == "--help" ]]
    then
        HELP=true
    fi
    shift
done

if [[
        "$CLEAN" != "true"
        && "$GENERATE" != "true"
        && "$BUILD" != "true"
        && "$STAGE" != "true"
        && "$CONFIGURE" != "true"
        && "$HELP" != "true"
    ]]
then
    # default action when no arguments are passed is to do everything
    GENERATE=true
    BUILD=true
    STAGE=true
    CONFIGURE=true
fi

# requesting how to run the script
if [[ "$HELP" == "true" ]]
then
    echo "build.sh [--clean] [--generate] [--build] [--stage] [--configure] [--debug] [--help]"
    echo "--clean: Removes the following directories (customize as needed):"
    for dir_to_clean in "${DIRECTORIES_TO_CLEAN[@]}" ; do
        echo "      $dir_to_clean"
    done
    echo "--generate: Perform code generation of schema libraries"
    echo "--build: Perform compilation and installation of USD schema libraries"
    echo "--prep-ov-install: Preps the kit-extension by copying it to the _install directory and stages the"
    echo "      built USD schema libraries in the appropriate sub-structure"
    echo "--configure: Performs a configuration step after you have built and"
    echo "      staged the schema libraries to ensure the plugInfo.json has the right information"
    echo "--debug: Performs the steps with a debug configuration instead of release"
    echo "      (default = release)"
    echo "--help: Display this help message"
    exit $HELP_EXIT_CODE
fi

# do we need to clean?
if [[ "$CLEAN" == "true" ]]
then
    for dir_to_clean in "${DIRECTORIES_TO_CLEAN[@]}" ; do
        rm -rf "$CWD/$dir_to_clean"
    done
fi

# do we need to generate?
if [[ "$GENERATE" == "true" ]]
then
    # pull down NVIDIA USD libraries
    # NOTE: If you have your own local build, you can comment out this step
    $CWD/tools/packman/packman pull deps/usd-deps.packman.xml -p linux-$(arch) -t config=$CONFIG

    # generate the schema code and plug-in information
    # NOTE: this will pull the NVIDIA repo_usd package to do this work
    export CONFIG=$CONFIG
    $CWD/tools/packman/python.sh bootstrap.py usd --configuration $CONFIG
fi

# do we need to build?

# NOTE: Modify this build step if using a build system other than cmake (ie, premake)
if [[ "$BUILD" == "true" ]]
then
    # pull down target-deps to build dynamic payload which relies on CURL
    $CWD/tools/packman/packman pull deps/target-deps.packman.xml -p linux-$(arch) -t config=$CONFIG

    # Below is an example of using CMake to build the generated files
    cmake -B ./_build/cmake -DCMAKE_BUILD_TYPE=$CONFIG
    cmake --build ./_build/cmake --config $CONFIG --target install
fi

# do we need to configure? This will configure the plugInfo.json files
if [[ "$CONFIGURE" == "true" ]]
then
    $CWD/tools/packman/python.sh bootstrap.py usd --configure-pluginfo --configuration $CONFIG
fi

# do we need to stage?
if [[ "$STAGE" == "true" ]]
then
    mkdir -p $CWD/_install/linux-$(arch)/$CONFIG
    cp -rf $CWD/src/kit-extension/exts/omni.example.schema $CWD/_install/linux-$(arch)/$CONFIG/
    mkdir -p $CWD/_install/linux-$(arch)/$CONFIG/omni.example.schema/OmniExampleSchema
    mkdir -p $CWD/_install/linux-$(arch)/$CONFIG/omni.example.schema/OmniExampleCodelessSchema
    cp -rf $CWD/_install/linux-$(arch)/$CONFIG/omniExampleSchema/OmniExampleSchema/*.* $CWD/_install/linux-$(arch)/$CONFIG/omni.example.schema/OmniExampleSchema/
    cp -rf $CWD/_install/linux-$(arch)/$CONFIG/omniExampleSchema/include $CWD/_install/linux-$(arch)/$CONFIG/omni.example.schema/OmniExampleSchema/
    cp -rf $CWD/_install/linux-$(arch)/$CONFIG/omniExampleSchema/lib $CWD/_install/linux-$(arch)/$CONFIG/omni.example.schema/OmniExampleSchema/
    cp -rf $CWD/_install/linux-$(arch)/$CONFIG/omniExampleSchema/resources $CWD/_install/linux-$(arch)/$CONFIG/omni.example.schema/OmniExampleSchema/    
    cp -rf $CWD/_install/linux-$(arch)/$CONFIG/omniExampleCodelessSchema/* $CWD/_install/linux-$(arch)/$CONFIG/omni.example.schema/OmniExampleCodelessSchema/
fi