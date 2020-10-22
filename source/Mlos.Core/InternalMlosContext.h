//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: InternalMlosContext.h
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
//----------------------------------------------------------------------------
// NAME: InternalMlosContextInitializer
//
// PURPOSE:
//  Helper class used to initialize shared memory for TestMlosContext.
//
// NOTES:
//
class InternalMlosContextInitializer
{
public:
    InternalMlosContextInitializer() {}

    _Check_return_
    HRESULT Initialize();

    InternalMlosContextInitializer(InternalMlosContextInitializer&& initializer) noexcept;

    InternalMlosContextInitializer(const InternalMlosContextInitializer&) = delete;

    InternalMlosContextInitializer& operator=(const InternalMlosContextInitializer&) = delete;

private:
    // Global shared memory region.
    //
    SharedMemoryRegionView<Internal::GlobalMemoryRegion> m_globalMemoryRegionView;

    // Named shared memory for Telemetry and Control Channel.
    //
    SharedMemoryMapView m_controlChannelMemoryMapView;

    // Named shared memory for Feedback Channel.
    //
    SharedMemoryMapView m_feedbackChannelMemoryMapView;

    friend class InternalMlosContext;
};

//----------------------------------------------------------------------------
// NAME: InternalMlosContext
//
// PURPOSE:
//  Simple implementation of MlosContext.
//  Single channel used to send control and telemetry messages.
//  Channel does not use OS synchronization primitive, sender and receiver thread should be running inside the same process.
//
// NOTES:
//  Intended to use only in the test.
//
class InternalMlosContext : public MlosContext
{
public:
    InternalMlosContext(InternalMlosContextInitializer&&) noexcept;

private:
    InternalMlosContextInitializer m_contextInitializer;

    TestSharedChannel m_controlChannel;

    TestSharedChannel m_feedbackChannel;
};
}
}
