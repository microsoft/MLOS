//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: GlobalDispatchTable.h
//
// Purpose:
//  This file adds the code generated files for this smart component's settings
//  and messages.  Once the messages structures are defined, the message
//  processing loop needs to be made aware of them by concatenating them into
//  the GlobalDispatchTable (a lookup table that tells the message processing
//  loop which callback to execute for which message type).
//  Note that this is a compile time constant operation for effeciency.
//
// Notes:
//  This is expected to be included *after* Mlos.Core.h and *before*
//  Mlos.Core.inl.  See stdafx.h for an example.
//
//*********************************************************************

#pragma once

// Include the codegen files from the SmartCache settings registry.
//
// Note: this expects out/Mlos.CodeGen.out/ to be listed in the default include
// search path for the compiler.
//
// Note: the codegen files for Mlos::Core are expected to have been included
// before these (typically via inclusion of Mlos.Core.h in stdafx.h).
//
#include "SmartCache/SettingsProvider_gen_base.h"
#include "SmartCache/SettingsProvider_gen_callbacks.h"
#include "SmartCache/SettingsProvider_gen_dispatch.h"

// Each settings registry codegen output includes its own dispatch (lookup)
// table that associates a message type (by id) with a function pointer variable
// to its message handler callback.
//
// For the message processing loop to know how to handle all the message types,
// it needs to combine (concatenate) all of the individual dispatch tables into
// a single global one (the GlobalDispatchTable).
//
// To do that we first need to compute the absolute lookup location of each
// message type by offsetting it from its local table's base index location in
// the global table.
//
// The resulting global dispatch table looks something like this (lower addresses on the left):
//
// +----------------------------------------------------+----------------------------------------------------+
// | Mlos::Core::MsgType_0 ... Mlos::Core::MsgType_N    | SmartCache::MsgType_0 ... SmartCache::MsgType_M    |
// +----------------------------------------------------+----------------------------------------------------+
// | Relative Mlos::Core message dispatch table indices | Relative SmartCache message dispatch table indices |
// +----------------------------------------------------+----------------------------------------------------+
// | 0                    ... N-1                       | 0                    ... M                         |
// +----------------------------------------------------+----------------------------------------------------+
// | Global dispatch table indices                      | Global dispatch table indices                      |
// +----------------------------------------------------+----------------------------------------------------+
// | 0                    ... N-1                       | N                  ... N+M-1                       |
// +----------------------------------------------------+----------------------------------------------------+
//

// Compute the base index offset for each settings registry's local dispatch
// table within the global dispatch table.
//
constexpr uint32_t SmartCache::ObjectDeserializationHandler::DispatchTableBaseIndex()
{
    // Since the settings registry codegen for Mlos::Core were included first,
    // the SmartCache dispatch table starts after that one.
    //
    // If additional settings registries were included here, they would
    // similarly add the previously included settings registry
    // DispatchTableElementCounts to compute their own relative starting offset.
    //
    // See SmartSharedChannel/GlobalDispatchTable.h for an example.
    //
    return static_cast<uint32_t>(Mlos::Core::ObjectDeserializationHandler::DispatchTableElementCount());
}

// Concatenate all of the local settings registry dispatch tables together to
// form the global dispatch table, fixing up their individual message ids
// relative to their new location within the global dispatch table.
//
// This effectively registers each of the code generated messages for the
// channel message reader loops to be able to process.
//
// Note: messages still need to have a handler function assigned to their
// Callback function pointer so that application specific code can be executed
// when its messages are received.
//
// See SmartCache/Main.cpp for an example.
//
constexpr auto GlobalDispatchTable()
{
    auto globalDispatchTable = Mlos::Core::DispatchTable<0>()
        .concatenate(Mlos::Core::ObjectDeserializationHandler::DispatchTable)
        .concatenate(SmartCache::ObjectDeserializationHandler::DispatchTable);

    return globalDispatchTable;
}
