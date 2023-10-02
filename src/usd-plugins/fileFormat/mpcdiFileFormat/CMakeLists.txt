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
set(PXR_PLUGIN_PLATFORM $<$<PLATFORM_ID:Windows>:windows>$<$<PLATFORM_ID:Linux>:linux>$<$<PLATFORM_ID:Darwin>:macos>)
set(PXR_PLUGIN_ARCH x86_64)
set(PXR_PLUGIN_CONFIG $<$<CONFIG:Debug>:debug>$<$<CONFIG:Release>:release>)

set(CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH} ${CMAKE_CURRENT_LIST_DIR}/../../../../_repo/repo_usd/templates/cmake)

include(PxrPlugin)
set(PXR_PLUGIN_USD_INCLUDE_DIR ${CMAKE_CURRENT_LIST_DIR}/../../../../_build/usd-deps/nv-usd/${PXR_PLUGIN_CONFIG}/include)
set(PXR_PLUGIN_BOOST_INCLUDE_DIR ${CMAKE_CURRENT_LIST_DIR}/../../../../_build/usd-deps/nv-usd/${PXR_PLUGIN_CONFIG}/include/boost)
set(PXR_PLUGIN_PYTHON_INCLUDE_DIR ${CMAKE_CURRENT_LIST_DIR}/../../../../_build/usd-deps/python/include)
set(PXR_PLUGIN_USD_LIBRARY_DIR ${CMAKE_CURRENT_LIST_DIR}/../../../../_build/usd-deps/nv-usd/${PXR_PLUGIN_CONFIG}/lib)
set(PXR_PLUGIN_PYTHON_LIBRARY_DIR ${CMAKE_CURRENT_LIST_DIR}/../../../../_build/usd-deps/python/libs)


set(PXR_PLUGIN_PLUGIN_DIR ${CMAKE_CURRENT_LIST_DIR})
set(PXR_PLUGIN_INSTALL_ROOT ${CMAKE_CURRENT_LIST_DIR}/../../../../_install/${PXR_PLUGIN_PLATFORM}-${PXR_PLUGIN_ARCH}/${PXR_PLUGIN_CONFIG}/mpcdiFileFormat)
set(PXR_PLUGIN_INCLUDE_DIR ${CMAKE_CURRENT_LIST_DIR}/../../../../_install/${PXR_PLUGIN_PLATFORM}-${PXR_PLUGIN_ARCH}/${PXR_PLUGIN_CONFIG}/mpcdiFileFormat/include/mpcdiFileFormat)
set(PXR_PLUGIN_LIB_DIR ${CMAKE_CURRENT_LIST_DIR}/../../../../_install/${PXR_PLUGIN_PLATFORM}-${PXR_PLUGIN_ARCH}/${PXR_PLUGIN_CONFIG}/mpcdiFileFormat/lib)
set(PXR_PLUGIN_MODULE_DIR ${CMAKE_CURRENT_LIST_DIR}/../../../../_install/${PXR_PLUGIN_PLATFORM}-${PXR_PLUGIN_ARCH}/${PXR_PLUGIN_CONFIG}/mpcdiFileFormat/MpcdiFileFormat)
set(PXR_PLUGIN_RESOURCES_DIR ${CMAKE_CURRENT_LIST_DIR}/../../../../_install/${PXR_PLUGIN_PLATFORM}-${PXR_PLUGIN_ARCH}/${PXR_PLUGIN_CONFIG}/mpcdiFileFormat/resources)

# optional if the USD libraries have a prefix
set(PXR_LIBRARY_PREFIX )

pxr_plugin(mpcdiFileFormat 
    USD_LIBRARIES
        arch
        tf
        plug
        vt
        gf
        sdf
        js
        pcp
        usdGeom
        usd
        usdLux

    INCLUDE_DIRS
        # these get passed as arguments to cmake when configuring
        # as e.g. cmake -DUSD_INCLUDE_DIR="" .
        ${PXR_PLUGIN_USD_INCLUDE_DIR}
        ${PXR_PLUGIN_BOOST_INCLUDE_DIR}
        ${PXR_PLUGIN_PYTHON_INCLUDE_DIR}
        ${CMAKE_CURRENT_LIST_DIR}/../../../../_build/usd-deps/nv_usd/${PXR_PLUGIN_CONFIG}/include/tbb

    LIBRARY_DIRS
        # these get passed as arguments to cmake when configuring
        # as e.g. cmake -DUSD_LIBRARY_DIR="" .
        ${PXR_PLUGIN_USD_LIBRARY_DIR}
        ${PXR_PLUGIN_PYTHON_LIBRARY_DIR}
        

    
    PUBLIC_HEADERS
        api.h
        iMpcdiDataProvider.h
        mpcdiDataProviderFactory.h

    PRIVATE_HEADERS
        mpcdiData.cpp
        mpcdiPluginManager.h
        mpcdiFileFormat.h
        tinyxml2.h

    CPP_FILES
        mpcdiData.cpp
        mpcdiDataProviderFactory.cpp
        iMpcdiDataProvider.cpp
        mpcdiPluginManager.cpp
        mpcdiFileFormat.cpp
        tinyxml2.cpp

    RESOURCE_FILES
        plugInfo.json

)