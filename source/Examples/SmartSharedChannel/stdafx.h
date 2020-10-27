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

#include <iostream>
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

void AssertFailed(
    _In_z_ char const* message,
    _In_z_ char const* file,
    _In_ uint32_t line);

// Macros.
//
#define UNUSED(x) (void)x
#define RTL_ASSERT(expression) (void)((!!(expression)) || (AssertFailed((#expression), (__FILE__), (uint32_t)(__LINE__)), 0) )
