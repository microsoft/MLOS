//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: NamedEvent.Window.h
//
// Purpose:
//      <description>
//
// Notes:
//      <special-instructions>
//
//*********************************************************************

#pragma once

namespace Mlos
{
namespace Core
{
class NamedEvent
{
public:
    NamedEvent() noexcept;

    NamedEvent(_In_ NamedEvent&& namedEvent) noexcept;

    ~NamedEvent();

    // Creates or opens a named event object.
    //
    _Must_inspect_result_
    HRESULT CreateOrOpen(_In_z_ const char* namedEventName) noexcept;

    // Opens an existing named event object.
    //
    _Must_inspect_result_
    HRESULT Open(_In_z_ const char* namedEventName) noexcept;

    // Closes a named event object.
    //
    void Close(_In_ bool cleanupOnClose = false);

    // Sets the named event object to the signaled state.
    //
    _Must_inspect_result_
    HRESULT Signal();

    // Waits until the named event object is in the signaled state.
    //
    _Must_inspect_result_
    HRESULT Wait() const;

    // Gets a value that indicates whether the handle is invalid.
    //
    bool IsInvalid() const;

private:
    HANDLE m_hEvent;
};
}
}
