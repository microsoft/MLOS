//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: NamedEvent.Window.cpp
//
// Purpose:
//      <description>
//
// Notes:
//      <special-instructions>
//
//*********************************************************************

#include "Mlos.Core.h"

using namespace Mlos::Core;

namespace Mlos
{
namespace Core
{
//----------------------------------------------------------------------------
// NAME: NamedEvent::Constructor.
//
NamedEvent::NamedEvent() noexcept
  : m_hEvent(nullptr),
    CleanupOnClose(false)
{
}

//----------------------------------------------------------------------------
// NAME: NamedEvent::Constructor.
//
// PURPOSE:
//  Move constructor.
//
NamedEvent::NamedEvent(NamedEvent&& namedEvent) noexcept
  : m_hEvent(std::exchange(namedEvent.m_hEvent, nullptr)),
    CleanupOnClose(std::exchange(namedEvent.CleanupOnClose, false))
{
}

//----------------------------------------------------------------------------
// NAME: NamedEvent::Destructor.
//
NamedEvent::~NamedEvent()
{
    Close();
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
_Check_return_
HRESULT NamedEvent::CreateOrOpen(const char* const namedEventName) noexcept
{
    PSECURITY_DESCRIPTOR securityDescriptor = nullptr;

    HRESULT hr = Security::CreateDefaultSecurityDescriptor(securityDescriptor);

    if (SUCCEEDED(hr))
    {
        SECURITY_ATTRIBUTES securityAttributes = { 0 };
        securityAttributes.nLength = sizeof(SECURITY_ATTRIBUTES);
        securityAttributes.bInheritHandle = false;
        securityAttributes.lpSecurityDescriptor = securityDescriptor;

        m_hEvent = CreateEventA(
            &securityAttributes,
            FALSE /* bManualReset */,
            FALSE /* bInitialState */,
            namedEventName);
        if (m_hEvent == nullptr)
        {
            hr = HRESULT_FROM_WIN32(GetLastError());
        }

        LocalFree(securityDescriptor);
    }

    if (SUCCEEDED(hr))
    {
        hr = Security::VerifyHandleOwner(m_hEvent);
    }

    if (FAILED(hr))
    {
        Close();
    }

    return hr;
}

//----------------------------------------------------------------------------
// NAME: NamedEvent::Open
//
// PURPOSE:
//  Opens an existing named event object.
//
// RETURNS:
//  HRESULT.
//
_Check_return_
HRESULT NamedEvent::Open(const char* const namedEventName) noexcept
{
    HRESULT hr = S_OK;

    m_hEvent = OpenEventA(
        EVENT_ALL_ACCESS /* dwDesiredAccess */,
        FALSE /* bInheritHandle */,
        namedEventName);
    if (m_hEvent == nullptr)
    {
        hr = HRESULT_FROM_WIN32(GetLastError());
    }

    if (SUCCEEDED(hr))
    {
        hr = Security::VerifyHandleOwner(m_hEvent);
    }

    if (FAILED(hr))
    {
        Close();
    }

    return hr;
}

//----------------------------------------------------------------------------
// NAME: NamedEvent::Close
//
// PURPOSE:
//  Closes a named event object.
//
void NamedEvent::Close()
{
    // Windows OS will remove the named event once the last process using it will terminate, just reset the flag.
    //
    CleanupOnClose = false;

    CloseHandle(m_hEvent);
    m_hEvent = nullptr;
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
_Check_return_
HRESULT NamedEvent::Signal()
{
    BOOL result = SetEvent(m_hEvent);

    return result != FALSE ? S_OK : HRESULT_FROM_WIN32(GetLastError());
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
_Check_return_
HRESULT NamedEvent::Wait()
{
    DWORD result = WaitForSingleObject(m_hEvent, INFINITE);

    return (result == WAIT_OBJECT_0) ? S_OK : HRESULT_FROM_WIN32(result == WAIT_FAILED ? GetLastError() : result);
}

//----------------------------------------------------------------------------
// NAME: NamedEvent::IsInvalid
//
// RETURNS:
//  Gets a value that indicates whether the handle is invalid.
//
bool NamedEvent::IsInvalid()
{
    return m_hEvent == nullptr;
}
}
}
