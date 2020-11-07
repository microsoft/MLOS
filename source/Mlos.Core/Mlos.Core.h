//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: Mlos.Core.h
//
// Purpose:
//      <description>
//
// Notes:
//      <special-instructions>
//
//*********************************************************************

#pragma once

#include <cstdint>
#include <cassert>
#include <stddef.h>
#include <limits>
#include <atomic>
#include <array>
#include <functional>
#include <type_traits>
#include <string.h>
#include <cwchar>

// Undefine MIN MAX macros.
//
#pragma push_macro("min")
#pragma push_macro("max")
#undef min
#undef max

#ifdef _WIN64

// Windows. Do not define MIN and MAX macros.
//
#define NOMINMAX
#include <windows.h>
#include <sddl.h>
#include <strsafe.h>
#include <aclapi.h>
#else

// Linux.
//
#include <errno.h>
typedef int32_t HRESULT;
typedef unsigned char byte;

constexpr int32_t INVALID_FD_VALUE = -1;

// Ignore some SAL annotations in Linux

#define _Check_return_
#define _Out_
#define _In_
#define _In_z_

#define SUCCEEDED(x) (x >= 0)
#define FAILED(x) (x < 0)
#define S_OK 0
#define S_FALSE 1
#define E_OUTOFMEMORY (-ENOMEM)
#define E_NOT_SET (-ENOENT)
#define HRESULT_FROM_ERRNO(errno) (-errno)

#endif

// Define macros.
//
#define MLOS_RETAIL_ASSERT(result) { if (!result) Mlos::Core::MlosPlatform::TerminateProcess(); }
#define MLOS_UNUSED_ARG(x) (void)x

#include "MlosPlatform.h"

#include "BytePtr.h"

#ifdef _WIN64
#include "Security.Windows.h"
#include "SharedMemoryMapView.Windows.h"
#include "NamedEvent.Window.h"
#else
#include "SharedMemoryMapView.Linux.h"
#include "NamedEvent.Linux.h"
#endif

#include "Hash.h"
#include "FNVHashFunction.h"
#include "PropertyProxy.h"
#include "ObjectDeserializationCallback.h"
#include "StringTypes.h"
#include "ObjectSerialization.h"
#include "Utils.h"

#include "PropertyProxyStringPtr.h"

#ifdef _STRING_VIEW_
#include "PropertyProxyStringView.h"
#include "ObjectSerializationStringView.h"
#endif

// Include Mlos.Core codegen files.
//
#include "Mlos.Core/SettingsProvider_gen_base.h"
#include "Mlos.Core/SettingsProvider_gen_callbacks.h"
#include "Mlos.Core/SettingsProvider_gen_dispatch.h"

#include "SharedMemoryRegionView.h"
#include "SharedMemoryRegionView.inl"

// Include shared channel implementation.
//
#include "SharedChannel.h"
#include "SharedChannelPolicies.h"

// Mlos.Core memory regions and Mlos.Core messages.
//
#include "ProbingPolicy.h"
#include "SharedConfig.h"
#include "ComponentConfig.h"
#include "ArenaAllocator.h"
#include "GlobalMemoryRegion.h"
#include "SharedConfigMemoryRegion.h"
#include "SharedConfigManager.h"
#include "SharedConfigDictionaryLookup.h"

// Include Mlos Client API.
//
#include "MlosContext.h"
#include "InternalMlosContext.h"
#include "InterProcessMlosContext.h"
#include "StaticSingleton.h"
#include "StaticVector.h"

// Implementation.
//
#include "MlosContext.inl"
#include "MlosContext.inl"
#include "ComponentConfig.inl"
#include "SharedChannel.inl"
#include "SharedConfigDictionaryLookup.inl"
#include "SharedConfigManager.inl"

// Mlos.Core assembly is always registered first.
//
namespace Mlos
{
namespace Core
{
namespace ObjectDeserializationHandler
{
constexpr uint32_t DispatchTableBaseIndex() { return 0; }
}
}
}

// Restore min/max macros.
//
#pragma pop_macro("min")
#pragma pop_macro("max")
