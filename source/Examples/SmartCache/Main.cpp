//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: Main.cpp
//
// Purpose:
//      <description>
//
// Notes:
//      <special-instructions>
//
//*********************************************************************

#include "stdafx.h"

using namespace Mlos::Core;
using namespace SmartCache;

// Include codegen files.
//
#include "GlobalDispatchTable.h"

#include "SmartCacheImpl.h"

void CheckHR(HRESULT hr)
{
    if (FAILED(hr))
    {
        throw std::exception();
    }
}

int
__cdecl
main(
    __in int argc,
    __in char* argv[])
{
    UNUSED(argc);
    UNUSED(argv);

    // Create MlosContext.
    //
    Mlos::Core::InterProcessMlosContextInitializer mlosContextInitializer;
    HRESULT hr = mlosContextInitializer.Initialize();
    CheckHR(hr);

    Mlos::Core::InterProcessMlosContext mlosContext(std::move(mlosContextInitializer));

    // Register Mlos.SmartCache Settings assembly.
    //
    hr = mlosContext.RegisterSettingsAssembly(
        "SmartCache.SettingsRegistry.dll",
        SmartCache::ObjectDeserializationHandler::DispatchTableBaseIndex());
    CheckHR(hr);

    // Create shared component configuration.
    //
    Mlos::Core::ComponentConfig<SmartCache::SmartCacheConfig> config(mlosContext);

    // Initialize config with default values.
    //
    config.CacheSize = 31;
    config.TelemetryBitMask = 0xffffffff;

    // Create an intelligent component.
    //
    SmartCacheImpl<uint64_t, FibonacciValue> cache(config);

    uint64_t result;
    for (int i = 0; i < 10; i++)
    {
        result = fibonacci(i, cache);
    }

    // Terminate the agent.
    //
    mlosContext.TerminateControlChannel();
}
