//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: GlobalDispatchTable.h
//
// Purpose:
//      <description>
//
// Notes:
//      <special-instructions>
//
//*********************************************************************

#pragma once

// Include SmartCache codegen files.
//
// Note: this expects out/Mlos.CodeGen.out/ to be listed in the default include
// search path.
//
#include "SmartCache/SettingsProvider_gen_base.h"
#include "SmartCache/SettingsProvider_gen_callbacks.h"
#include "SmartCache/SettingsProvider_gen_dispatch.h"

// Base indexes for all included dispatch tables.
//
constexpr uint32_t SmartCache::ObjectDeserializationHandler::DispatchTableBaseIndex()
{
    return static_cast<uint32_t>(Mlos::Core::ObjectDeserializationHandler::DispatchTableElementCount());
}

// Note: As additional settings registries are included in the same project the
// DispatchTableBaseIndex()s should be added together for each prior component
// corresponding to the DispatchTables that are concatenated below.
// See SmartSharedChannel/GlobalDispatchTable.h for an example.

// Registers each of the code generated messages for the channel message handler
// reader loops.
//
// Note: messages still need to have a Callback setup for it so that application
// specific code is executed when its messages are received.
// See Also: SmartCache/Main.cpp
//
constexpr auto GlobalDispatchTable()
{
    auto globalDispatchTable = Mlos::Core::DispatchTable<0>()
        .concatenate(Mlos::Core::ObjectDeserializationHandler::DispatchTable)
        .concatenate(SmartCache::ObjectDeserializationHandler::DispatchTable);

    return globalDispatchTable;
}
