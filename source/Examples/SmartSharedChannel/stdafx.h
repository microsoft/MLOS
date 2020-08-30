//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: stdafx.h
//
// Purpose:
//      <description>
//
// Notes:
//      <special-instructions>
//
//*********************************************************************

#pragma once

// Mlos.Core.
//
#include "Mlos.Core.h"

// Global dispatch table.
//
#include "GlobalDispatchTable.h"

// Mlos.Core.
//
#include "Mlos.Core.inl"

#include <future>
#include <vector>

using namespace Mlos::Core;
using namespace SmartSharedChannel;

// Configs declarations.
//
extern StaticSingleton<ComponentConfig<SharedChannelConfig>> g_SharedChannelConfig;
extern StaticSingleton<ComponentConfig<MicrobenchmarkConfig>> g_MicrobenchmarkConfig;

// Functions declarations.
//
void CheckHR(HRESULT hr);
HRESULT RegisterSmartConfigs(MlosContext& mlosContext);
uint64_t RunSharedChannelBenchmark(
    const SharedChannelConfig& sharedChannelConfig,
    const MicrobenchmarkConfig& microbenchmarkConfig);
