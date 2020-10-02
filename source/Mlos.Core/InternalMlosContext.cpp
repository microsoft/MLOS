//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: InternalMlosContext.cpp
//
// Purpose:
//      <description>
//
// Notes:
//      <special-instructions>
//
//*********************************************************************

#include "Mlos.Core.h"
#include "Mlos.Core.inl"

namespace Mlos
{
namespace Core
{
//----------------------------------------------------------------------------
// NAME: InternalMlosContextInitializer::Constructor.
//
// PURPOSE:
//  Move constructor.
//
// NOTES:
//
InternalMlosContextInitializer::InternalMlosContextInitializer(InternalMlosContextInitializer&& initializer) noexcept
  : m_globalMemoryRegionView(std::move(initializer.m_globalMemoryRegionView)),
    m_controlChannelMemoryMapView(std::move(initializer.m_controlChannelMemoryMapView)),
    m_feedbackChannelMemoryMapView(std::move(initializer.m_feedbackChannelMemoryMapView))
{
}

//----------------------------------------------------------------------------
// NAME: InternalMlosContextInitializer::Initialize
//
// PURPOSE:
//  Opens the shared memory used for the communication channel.
//
// NOTES:
//
_Check_return_
HRESULT InternalMlosContextInitializer::Initialize()
{
    const size_t SharedMemorySize = 65536;

    HRESULT hr = S_OK;

    if (SUCCEEDED(hr))
    {
        hr = m_globalMemoryRegionView.CreateNew("Test_Mlos.GlobalMemory", SharedMemorySize);
    }

    if (SUCCEEDED(hr))
    {
        hr = m_controlChannelMemoryMapView.CreateNew("Test_SharedChannelMemory", SharedMemorySize);
    }

    if (SUCCEEDED(hr))
    {
        hr = m_feedbackChannelMemoryMapView.CreateNew("Test_FeedbackChannelMemory", SharedMemorySize);
    }

    if (FAILED(hr))
    {
        // Close all the shared maps if we fail to create one.
        //
        m_globalMemoryRegionView.Close();
        m_controlChannelMemoryMapView.Close();
        m_feedbackChannelMemoryMapView.Close();
    }

    return hr;
}

//----------------------------------------------------------------------------
// NAME: InternalMlosContext::Constructor
//
// PURPOSE:
//  Creates InternalMlosContext.
//
// NOTES:
//
InternalMlosContext::InternalMlosContext(InternalMlosContextInitializer&& initializer) noexcept
  : MlosContext(initializer.m_globalMemoryRegionView.MemoryRegion(), m_controlChannel, m_controlChannel, m_feedbackChannel),
    m_contextInitializer(std::move(initializer)),
    m_controlChannel(
        m_contextInitializer.m_globalMemoryRegionView.MemoryRegion().ControlChannelSynchronization,
        m_contextInitializer.m_controlChannelMemoryMapView),
    m_feedbackChannel(
        m_contextInitializer.m_globalMemoryRegionView.MemoryRegion().FeedbackChannelSynchronization,
        m_contextInitializer.m_feedbackChannelMemoryMapView)
{
}
}
}
