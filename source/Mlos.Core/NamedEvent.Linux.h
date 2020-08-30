//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: NamedEvent.Linux.h
//
// Purpose:
//      <description>
//
// Notes:
//      <special-instructions>
//
//*********************************************************************

#pragma once

#include <semaphore.h>

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
    _Check_return_
    HRESULT CreateOrOpen(const char* const namedEventName) noexcept;

    // Opens a named event object.
    //
    _Check_return_
    HRESULT Open(const char* const namedEventName) noexcept;

    // Sets the named event object to the signaled state.
    //
    _Check_return_
    HRESULT Signal();

    // Waits until the named event object is in the signaled state.
    //
    _Check_return_
    HRESULT Wait();

private:
    sem_t* m_semaphore;
};

}
}
