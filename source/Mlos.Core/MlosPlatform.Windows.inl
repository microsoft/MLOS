//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: MlosPlatform.Std.inl
//
// Purpose:
//      Provides a platform specific implementation for functions declared in
//      MlosPlatform.h
//
//      This file is expected to be included by the target application, not
//      Mlos.Core.  It is simply provided there as a typical/common reference
//      implementation.
//
//*********************************************************************

#pragma once

namespace Mlos
{
namespace Core
{
namespace Internal
{
//----------------------------------------------------------------------------
// NAME: MlosPlatformTerminateProcess
//
// PURPOSE:
//  Terminates the current process.
//
// NOTES:
//
void MlosPlatformTerminateProcess()
{
    ExitProcess(0);
}

//----------------------------------------------------------------------------
// NAME: MlosPlatformWait
//
// PURPOSE:
//  Suspends the execution of the current thread for millisecond intervals.
//
// NOTES:
//
void MlosPlatformWait(_In_ uint32_t milliseconds)
{
    Sleep(milliseconds);
}

//----------------------------------------------------------------------------
// NAME: MlosPlatformCreateThread
//
// PURPOSE:
//  Creates the thread.
//
// NOTES:
//
_Must_inspect_result_
HRESULT MlosPlatformCreateThread(
    _In_ void* (*routine)(void*),
    _In_ void* pParam,
    _Inout_ ThreadHandle& handle)
{
    HANDLE hThread = CreateThread(
        nullptr, // thread attributes
        0, // default stack size
        reinterpret_cast<LPTHREAD_START_ROUTINE>(routine),
        pParam,
        0, // creation flags
        nullptr); // thread id
    if (hThread == nullptr)
    {
        return HRESULT_FROM_WIN32(GetLastError());
    }

    // Copy the thread handle.
    //
    handle = static_cast<ThreadHandle>(hThread);

    return S_OK;
}

//----------------------------------------------------------------------------
// NAME: MlosPlatformCreateThread
//
// PURPOSE:
//  Creates the thread.
//
// NOTES:
//
_Must_inspect_result_
HRESULT MlosPlatformJoinThread(_In_ ThreadHandle handle)
{
    HANDLE hThread = static_cast<HANDLE>(handle);
    DWORD result = WaitForSingleObject(hThread, INFINITE);

    return result == WAIT_OBJECT_0 ? S_OK : HRESULT_FROM_WIN32(result == WAIT_FAILED ? GetLastError() : result);
}
}
}
}
