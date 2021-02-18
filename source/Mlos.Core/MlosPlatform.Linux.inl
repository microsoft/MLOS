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

#include <chrono>
#include <thread>
#include <pthread.h>

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
    std::terminate();
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
    std::this_thread::sleep_for(std::chrono::milliseconds(milliseconds));
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
    pthread_t pthread;

    int result = pthread_create(
        &pthread,
        nullptr,
        routine,
        pParam);
    if (result != 0)
    {
        return HRESULT_FROM_ERRNO(result);
    }

    // Copy the thread handle.
    //
    handle = reinterpret_cast<ThreadHandle>(pthread);

    return S_OK;
}

//----------------------------------------------------------------------------
// NAME: MlosPlatformJoinThread
//
// PURPOSE:
//  Joins the thread.
//
// NOTES:
//
_Must_inspect_result_
HRESULT MlosPlatformJoinThread(_In_ ThreadHandle handle)
{
    int result = pthread_join(reinterpret_cast<pthread_t>(handle), nullptr);
    if (result != 0)
    {
        return HRESULT_FROM_ERRNO(result);
    }

    return S_OK;
}
}
}
}
