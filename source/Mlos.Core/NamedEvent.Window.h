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

    NamedEvent(NamedEvent&& namedEvent) noexcept;

    ~NamedEvent();

    // Creates or opens a named event object.
    //
    _Must_inspect_result_
    HRESULT CreateOrOpen(_In_z_ const char* const namedEventName) noexcept;

    // Opens an existing named event object.
    //
    _Must_inspect_result_
    HRESULT Open(_In_z_ const char* const namedEventName) noexcept;

    // Closes a named event object.
    //
    void Close();

    // Sets the named event object to the signaled state.
    //
    _Must_inspect_result_
    HRESULT Signal();

    // Waits until the named event object is in the signaled state.
    //
    _Must_inspect_result_
    HRESULT Wait();

    // Gets a value that indicates whether the handle is invalid.
    //
    bool IsInvalid();

    // Indicates if we should cleanup OS resources when closing the shared memory map view.
    // No-op on Windows.
    //
    bool CleanupOnClose;

private:
    HANDLE m_hEvent;
};
}
}
