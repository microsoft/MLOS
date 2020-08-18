//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: ObjectDeserializationCallback.h
//
// Purpose:
//      <description>
//
// Notes:
//      <special-instructions>
//
//*********************************************************************

#pragma once
#include <array>

using std::size_t;

// User defined deserialization object callbacks.
//
namespace ObjectDeserializationCallback
{
template<typename T>
void Deserialize(T&&);
}

namespace Mlos
{
namespace Core
{
struct DispatchEntry
{
    uint64_t CodegenTypeHash;
    bool (*Callback)(BytePtr&&, int frameLength);
};

// Concatenate dispatch tables.
// Allows to build as constexpr a global dispatcher table by combining individual tables.
//
// Mlos::Core::DispatchTable<0>()
//      .concatenate(Mlos::Core::Channel::ObjectDeserializationHandler::DispatchTable);
//      .concatenate(TestApp::SettingsMessageTypes::ObjectDeserializationHandler::DispatchTable)
//
template<size_t N>
class DispatchTable : public std::array<::Mlos::Core::DispatchEntry, N>
{
public:
    template<size_t N1>
    constexpr DispatchTable<N + N1> concatenate(
        const ::Mlos::Core::DispatchEntry (&arr)[N1])
    {
        DispatchTable<N + N1> result = {};

        for (size_t i = 0; i < N; ++i)
        {
            result[i] = (*this)[i];
        }

        for (size_t i = 0; i < N1; ++i)
        {
            result[i + N] = arr[i];
        }

        return result;
    }
};
}
}
