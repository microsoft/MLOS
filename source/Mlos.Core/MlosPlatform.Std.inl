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
// Notes:
//      Since these functions need to be externally visible for Mlos.Core to
//      link against, they should not be marked "inline".
//
//*********************************************************************

#pragma once

#include <chrono>
#include <thread>

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
void MlosPlatformWait(uint32_t milliseconds)
{
    std::this_thread::sleep_for(std::chrono::milliseconds(milliseconds));
}
}
}
}
