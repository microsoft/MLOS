//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: NamedEvent.Linux.cpp
//
// Purpose:
//      <description>
//
// Notes:
//      <special-instructions>
//
//*********************************************************************

#include "Mlos.Core.h"

#include <sys/stat.h>
#include <fcntl.h>
#include <stdlib.h>

using namespace Mlos::Core;

namespace Mlos
{
namespace Core
{
//----------------------------------------------------------------------------
// NAME: NamedEvent::Constructor.
//
NamedEvent::NamedEvent() noexcept
  : m_semaphore(SEM_FAILED),
    m_namedEventName(nullptr)
{
}

//----------------------------------------------------------------------------
// NAME: NamedEvent::Constructor.
//
// PURPOSE:
//  Move constructor.
//
NamedEvent::NamedEvent(_In_ NamedEvent&& namedEvent) noexcept
  : m_semaphore(std::exchange(namedEvent.m_semaphore, SEM_FAILED)),
    m_namedEventName(std::exchange(namedEvent.m_namedEventName, nullptr))
{
}

//----------------------------------------------------------------------------
// NAME: NamedEvent::CreateOrOpen
//
// PURPOSE:
//  Creates or opens a named event object.
//
// RETURNS:
//  HRESULT.
//
_Must_inspect_result_
HRESULT NamedEvent::CreateOrOpen(_In_z_ const char* namedEventName) noexcept
{
    HRESULT hr = S_OK;

    m_namedEventName = strdup(namedEventName);
    if (m_namedEventName == nullptr)
    {
        return E_OUTOFMEMORY;
    }

    m_semaphore = sem_open(namedEventName, O_CREAT, S_IRUSR | S_IWUSR, 0);
    if (m_semaphore == SEM_FAILED)
    {
        hr = HRESULT_FROM_ERRNO(errno);
    }

    return hr;
}

//----------------------------------------------------------------------------
// NAME: NamedEvent::Open
//
// PURPOSE:
//  Opens a named event object.
//
// RETURNS:
//  HRESULT.
//
_Must_inspect_result_
HRESULT NamedEvent::Open(_In_z_ const char* namedEventName) noexcept
{
    return CreateOrOpen(namedEventName);
}

//----------------------------------------------------------------------------
// NAME: NamedEvent::Destructor.
//
NamedEvent::~NamedEvent()
{
    Close();
}

//----------------------------------------------------------------------------
// NAME: NamedEvent::Close
//
// PURPOSE:
//  Closes a named event object.
//
void NamedEvent::Close(_In_ bool cleanupOnClose)
{
    if (m_semaphore != SEM_FAILED)
    {
        sem_close(m_semaphore);
        m_semaphore = SEM_FAILED;

        if (cleanupOnClose)
        {
            if (m_namedEventName != nullptr)
            {
                sem_unlink(m_namedEventName);
            }
        }
    }

    if (m_namedEventName != nullptr)
    {
        free(m_namedEventName);
        m_namedEventName = nullptr;
    }
}

//----------------------------------------------------------------------------
// NAME: NamedEvent::Signal
//
// PURPOSE:
//  Sets the named event object to the signaled state.
//
// RETURNS:
//  HRESULT.
//
_Must_inspect_result_
HRESULT NamedEvent::Signal()
{
    if (sem_post(m_semaphore) == -1)
    {
        return HRESULT_FROM_ERRNO(errno);
    }

    return S_OK;
}

//----------------------------------------------------------------------------
// NAME: NamedEvent::Wait
//
// PURPOSE:
//  Waits until the named event object is in the signaled state.
//
// RETURNS:
//  HRESULT.
//
_Must_inspect_result_
HRESULT NamedEvent::Wait()
{
    if (sem_wait(m_semaphore) == -1)
    {
        return HRESULT_FROM_ERRNO(errno);
    }

    return S_OK;
}
}
}
