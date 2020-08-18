//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: MlosContext.cpp
//
// Purpose:
//      <description>
//
// Notes:
//      <special-instructions>
//
//*********************************************************************

#include "Mlos.Core.h"

namespace Mlos
{
namespace Core
{
#pragma warning( disable : 4355)

//----------------------------------------------------------------------------
// NAME: MlosContext constructor.
//
// PURPOSE:
//  Creates MlosContext.
//
//
// NOTES:
//  From shared memory view creates communication channels.
//
MlosContext::MlosContext(
    Internal::GlobalMemoryRegion& globalMemoryRegion,
    ISharedChannel& controlChannel,
    ISharedChannel& telemetryChannel,
    ISharedChannel& feedbackChannel) noexcept
  : m_sharedConfigManager(*this),
    m_globalMemoryRegion(globalMemoryRegion),
    m_controlChannel(controlChannel),
    m_telemetryChannel(telemetryChannel),
    m_feedbackChannel(feedbackChannel)
{
}

#pragma warning( default : 4355)

//----------------------------------------------------------------------------
// NAME: MlosContext::RegisterSettingsAssembly
//
// PURPOSE:
//  Registers the settings assembly with Mlos.Agent.
//
// RETURNS:
//  HRESULT.
//
// NOTES:
//
HRESULT MlosContext::RegisterSettingsAssembly(
    const char* assemblyFileName,
    uint32_t assemblyDispatchTableBaseIndex)
{
#ifdef _WIN64
    HMODULE hModule = GetModuleHandleW(nullptr);
    if (hModule == nullptr)
    {
        return HRESULT_FROM_WIN32(GetLastError());
    }

    char szApplicationFullPath[MAX_PATH];
    constexpr size_t cchApplicationFullPath = _countof(szApplicationFullPath);

    if (!GetModuleFileNameA(hModule, szApplicationFullPath, cchApplicationFullPath))
    {
        return HRESULT_FROM_WIN32(GetLastError());
    }
#else
    char* szApplicationFullPath = nullptr;
#endif

    uint32_t assemblyIndex = m_globalMemoryRegion.RegisteredSettingsAssemblyCount;

    // Check if there is already a config for the given assembly index.
    //
    ComponentConfig<Internal::RegisteredSettingsAssemblyConfig> registeredSettingAssembly(*this);
    registeredSettingAssembly.AssemblyIndex = assemblyIndex;

    HRESULT hr = m_sharedConfigManager.Lookup(registeredSettingAssembly);

    if (SUCCEEDED(hr))
    {
        // Config is present.
        //
        return hr;
    }

    // Register assembly information as a config.
    //
    registeredSettingAssembly.DispatchTableBaseIndex = assemblyDispatchTableBaseIndex;
    registeredSettingAssembly.ApplicationFilePath = szApplicationFullPath;
    registeredSettingAssembly.AssemblyFileName = assemblyFileName;

    hr = RegisterComponentConfig(registeredSettingAssembly);

    if (SUCCEEDED(hr))
    {
        // Increase number of settings assemblies.
        //
        ++m_globalMemoryRegion.RegisteredSettingsAssemblyCount;

        // Send message to Mlos.Agent to load the settings asembly.
        //
        Internal::RegisterAssemblyRequestMessage registerAssemblyRequestMsg = { 0 };
        registerAssemblyRequestMsg.AssemblyIndex = assemblyIndex;

        m_controlChannel.SendMessage(registerAssemblyRequestMsg);
    }

    return hr;
}

//----------------------------------------------------------------------------
// NAME: MlosContext::ControlChannel
//
// PURPOSE:
//  Returns the control channel instance.
//
// RETURNS:
//
// NOTES:
//
Mlos::Core::ISharedChannel& MlosContext::ControlChannel() const
{
    return m_controlChannel;
}

//----------------------------------------------------------------------------
// NAME: MlosContext::FeedbackChannel
//
// PURPOSE:
//  Returns the feedback channel instance.
//
// RETURNS:
//
// NOTES:
//
Mlos::Core::ISharedChannel& MlosContext::FeedbackChannel() const
{
    return m_feedbackChannel;
}

//----------------------------------------------------------------------------
// NAME: MlosContext::TerminateControlChannel
//
// PURPOSE:
//  Terminate the control channel.
//
// RETURNS:
//
// NOTES:
//  Sends a message to terminate the Mlos.Agent control channel reader threads.
//
void MlosContext::TerminateControlChannel()
{
    // Terminate the channel to avoid deadlocks if the buffer is full, and there is no active reader thread.
    //
    m_controlChannel.Sync.TerminateChannel = true;
    m_controlChannel.SendMessage(TerminateReaderThreadRequestMessage());
}

//----------------------------------------------------------------------------
// NAME: MlosContext::TerminateFeedbackChannel
//
// PURPOSE:
//  Sends a message to terminate the feedback channel reader threads.
//
// RETURNS:
//
// NOTES:
//
void MlosContext::TerminateFeedbackChannel()
{
    m_feedbackChannel.Sync.TerminateChannel = true;
    m_feedbackChannel.SendMessage(TerminateReaderThreadRequestMessage());
    m_feedbackChannel.NotifyExternalReader();

    while (m_feedbackChannel.Sync.ActiveReaderCount.load() != 0)
    {
        // Wait before trying again.
        //
        MlosPlatform::SleepMilliseconds(100);
    }
}

//----------------------------------------------------------------------------
// NAME: MlosContext::IsControlChannelActive
//
// PURPOSE:
//  Checks if the control channel is still active.
//
// RETURNS:
//
// NOTES:
//
bool MlosContext::IsControlChannelActive()
{
    return !(m_controlChannel.Sync.TerminateChannel);
}

//----------------------------------------------------------------------------
// NAME: MlosContext::IsFeedbackChannelActive
//
// PURPOSE:
//  Checks if the feedback channel is still active.
//
// RETURNS:
//
// NOTES:
//
bool MlosContext::IsFeedbackChannelActive()
{
    return !(m_feedbackChannel.Sync.TerminateChannel);
}

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
HRESULT InternalMlosContextInitializer::Initialize()
{
    const size_t SharedMemorySize = 65536;

    HRESULT hr = m_globalMemoryRegionView.CreateOrOpen("Test_Mlos.GlobalMemory", SharedMemorySize);
    if (FAILED(hr))
    {
        return hr;
    }

    hr = m_controlChannelMemoryMapView.CreateOrOpen("Test_SharedChannelMemory", SharedMemorySize);
    if (FAILED(hr))
    {
        return hr;
    }

    hr = m_feedbackChannelMemoryMapView.CreateOrOpen("Test_FeedbackChannelMemory", SharedMemorySize);
    if (FAILED(hr))
    {
        return hr;
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

//----------------------------------------------------------------------------
// NAME: InterProcessMlosContextInitializer::Constructor.
//
// PURPOSE:
//  Move constructor.
//
// NOTES:
//
InterProcessMlosContextInitializer::InterProcessMlosContextInitializer(InterProcessMlosContextInitializer&& initializer) noexcept
  : m_globalMemoryRegionView(std::move(initializer.m_globalMemoryRegionView)),
    m_controlChannelMemoryMapView(std::move(initializer.m_controlChannelMemoryMapView)),
    m_feedbackChannelMemoryMapView(std::move(initializer.m_feedbackChannelMemoryMapView)),
    m_controlChannelPolicy(std::move(initializer.m_controlChannelPolicy)),
    m_feedbackChannelPolicy(std::move(initializer.m_feedbackChannelPolicy))
{
}

//----------------------------------------------------------------------------
// NAME: InterProcessMlosContextInitializer::Initialize
//
// PURPOSE:
//  Opens the shared memory and synchronization primitives used for the communication channel.
//
// NOTES:
//
HRESULT InterProcessMlosContextInitializer::Initialize()
{
    // #TODO const as codegen, pass a config struct ?
    //
    const size_t SharedMemorySize = 65536;

    HRESULT hr = m_globalMemoryRegionView.CreateOrOpen("Host_Mlos.GlobalMemory", SharedMemorySize);
    if (FAILED(hr))
    {
        return hr;
    }

    hr = m_controlChannelMemoryMapView.CreateOrOpen("Host_Mlos.ControlChannel", SharedMemorySize);
    if (FAILED(hr))
    {
        return hr;
    }

    hr = m_feedbackChannelMemoryMapView.CreateOrOpen("Host_Mlos.FeedbackChannel", SharedMemorySize);
    if (FAILED(hr))
    {
        return hr;
    }

    hr = m_controlChannelPolicy.m_notificationEvent.CreateOrOpen("Global\\ControlChannel_Event");
    if (FAILED(hr))
    {
        return hr;
    }

    hr = m_feedbackChannelPolicy.m_notificationEvent.CreateOrOpen("Global\\FeedbackChannel_Event");
    if (FAILED(hr))
    {
        return hr;
    }

    return hr;
}

//----------------------------------------------------------------------------
// NAME: InterProcessMlosContext::Constructor
//
// PURPOSE:
//  Creates InterProcessMlosContext.
//
// NOTES:
//
InterProcessMlosContext::InterProcessMlosContext(InterProcessMlosContextInitializer&& initializer) noexcept
  : MlosContext(initializer.m_globalMemoryRegionView.MemoryRegion(), m_controlChannel, m_controlChannel, m_feedbackChannel),
    m_contextInitializer(std::move(initializer)),
    m_controlChannel(
        m_contextInitializer.m_globalMemoryRegionView.MemoryRegion().ControlChannelSynchronization,
        m_contextInitializer.m_controlChannelMemoryMapView,
        std::move(m_contextInitializer.m_controlChannelPolicy)),
    m_feedbackChannel(
        m_contextInitializer.m_globalMemoryRegionView.MemoryRegion().FeedbackChannelSynchronization,
        m_contextInitializer.m_feedbackChannelMemoryMapView,
        std::move(m_contextInitializer.m_feedbackChannelPolicy))
{
}
}
}
