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
//
#define _Must_inspect_result_ __attribute__((warn_unused_result))
#define _Out_
#define _In_
#define _Inout_
#define _In_opt_
#define _In_opt_z_
#define _In_z_
#define _In_reads_(x)
#define _In_reads_bytes_(x)
#define _In_reads_z_(x)

#define SUCCEEDED(x) (x >= 0)
#define FAILED(x) (x < 0)
#define S_OK 0
#define S_FALSE 1
#define E_OUTOFMEMORY (-ENOMEM)
#define E_NOT_SET (-ENOENT)
#define HRESULT_FROM_ERRNO(x) (-x)

#endif

// Define macros.
//
#define MLOS_RETAIL_ASSERT(result) if (!(result)) { Mlos::Core::MlosPlatform::TerminateProcess(); }
#define MLOS_UNUSED_ARG(x) (void)(x)
#define MLOS_IGNORE_HR(x) (void)(x)

#ifdef _MSC_VER
#define MLOS_SELECTANY_ATTR __declspec(selectany)
#elif __clang__
#define MLOS_SELECTANY_ATTR __attribute__((weak))
#elif __GNUC__
#define MLOS_SELECTANY_ATTR __attribute__((weak))
#else
#warning Unhandled compiler.
#endif

#include "MlosPlatform.h"

namespace MlosCore = ::Mlos::Core;
namespace MlosInternal = ::Mlos::Core::Internal;

#include "BytePtr.h"

#include "Hash.h"
#include "FNVHashFunction.h"
#include "PropertyProxy.h"
#include "ObjectDeserializationCallback.h"
#include "StringTypes.h"
#include "ObjectSerialization.h"
#include "ObjectSerializationStringPtr.h"
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

#ifdef _WIN64
#include "Security.Windows.h"
#include "SharedMemoryMapView.Windows.h"
#include "NamedEvent.Window.h"
#else
#include "SharedMemoryMapView.Linux.h"
#include "NamedEvent.Linux.h"
#include "FileDescriptorExchange.Linux.h"
#endif

#include "UniqueString.h"
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
#include "AlignedInstance.h"
#include "AlignedVector.h"
#include "MlosContext.h"
#include "MlosInitializer.h"
#include "InternalMlosContext.h"
#include "InterProcessMlosContext.h"

// Implementation.
//
#include "MlosContext.inl"
#include "MlosInitializer.inl"
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

// Depending on OS, we are using different Mlos context implementation.
// Define a default Mlos context factory.
//
#ifdef _WIN64
using DefaultMlosInitializer = Mlos::Core::MlosInitializer<Mlos::Core::InterProcessMlosContext>;
#else
#include "FileWatchEvent.Linux.h"
#include "AnonymousMemoryMlosContext.Linux.h"
using DefaultMlosInitializer = Mlos::Core::MlosInitializer<Mlos::Core::AnonymousMemoryMlosContext>;
#endif

// Restore min/max macros.
//
#pragma pop_macro("min")
#pragma pop_macro("max")
