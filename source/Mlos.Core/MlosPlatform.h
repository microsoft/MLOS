//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: MlosPlatform.h
//
// Purpose:
//      Declares some functions to allow platform specific implementation of
//      various OS related functions.
//
// Notes:
//      This is included by Mlos.Core, whereas their implementation is expected
//      to be provided by the target application linking with Mlos.Core.
//
// See Also:
//      MlosPlatform.Std.inl
//
//*********************************************************************

#pragma once

namespace Mlos
{
namespace Core
{
namespace Internal
{
// External implementation.
//
extern void MlosPlatformTerminateProcess();
extern void MlosPlatformWait(uint32_t milliseconds);
}

//----------------------------------------------------------------------------
// NAME: MlosPlatform
//
// PURPOSE:
//
// NOTES:
//
class MlosPlatform
{
public:
    // Terminate the current process.
    //
    static inline void TerminateProcess()
    {
        Mlos::Core::Internal::MlosPlatformTerminateProcess();
    }

    // Suspends the execution of the current thread for millisecond intervals.
    //
    static inline void SleepMilliseconds(uint32_t milliseconds)
    {
        Mlos::Core::Internal::MlosPlatformWait(milliseconds);
    }
};
}
}
