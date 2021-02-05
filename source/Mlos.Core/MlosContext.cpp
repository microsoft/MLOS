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
#include "Mlos.Core.inl"

namespace Mlos
{
namespace Core
{
//----------------------------------------------------------------------------
// NAME: MlosContext constructor.
//
// PURPOSE:
//  Creates MlosContext.
//
// NOTES:
//  The constructor creates communication channels from shared memory views.
//
MlosContext::MlosContext(
    _In_ Internal::GlobalMemoryRegion& globalMemoryRegion,
    _In_ ISharedChannel& controlChannel,
    _In_ ISharedChannel& telemetryChannel,
    _In_ ISharedChannel& feedbackChannel) noexcept
  : m_sharedConfigManager(),
    m_globalMemoryRegion(globalMemoryRegion),
    m_controlChannel(controlChannel),
    m_telemetryChannel(telemetryChannel),
    m_feedbackChannel(feedbackChannel)
{
    // Mlos.NetCore is always registered first.
    // That indicates the mlos context is created.
    //
    globalMemoryRegion.RegisteredSettingsAssemblyCount.store(1);
}

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
    _In_z_ const char* assemblyFileName,
    _In_ uint32_t assemblyDispatchTableBaseIndex)
{
    const uint32_t assemblyIndex = m_globalMemoryRegion.RegisteredSettingsAssemblyCount;

    // Check if there is already a config for the given assembly index.
    //
    ComponentConfig<Internal::RegisteredSettingsAssemblyConfig> registeredSettingAssembly;
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
    registeredSettingAssembly.AssemblyFileName = assemblyFileName;

    // Register settings assembly in the global shared region.
    //
    hr = SharedConfigManager::CreateOrUpdateFrom(
        m_globalMemoryRegion.SharedConfigDictionary,
        registeredSettingAssembly);

    if (SUCCEEDED(hr))
    {
        // Increase number of settings assemblies.
        //
        ++m_globalMemoryRegion.RegisteredSettingsAssemblyCount;

        // Send message to Mlos.Agent to load the settings assembly.
        //
        Internal::RegisterSettingsAssemblyRequestMessage msg = { 0 };
        msg.AssemblyIndex = assemblyIndex;

        m_controlChannel.SendMessage(msg);
    }

    return hr;
}

//----------------------------------------------------------------------------
// NAME: MlosContext::RegisterSharedMemory
//
// PURPOSE:
//  Registers a shared memory map in the global memory region.
//
// RETURNS:
//  HRESULT.
//
// NOTES:
//
_Must_inspect_result_
HRESULT MlosContext::RegisterSharedMemory(
    _In_ Internal::MemoryRegionId memoryRegionId,
    _In_z_ const char* sharedMemoryName,
    _In_ size_t memoryRegionSize)
{
    ComponentConfig<Internal::RegisteredMemoryRegionConfig> registeredMemoryRegion;

    registeredMemoryRegion.MemoryRegionId = memoryRegionId;
    registeredMemoryRegion.SharedMemoryMapName = sharedMemoryName;
    registeredMemoryRegion.MemoryRegionSize = memoryRegionSize;

    HRESULT hr = SharedConfigManager::CreateOrUpdateFrom(
        m_globalMemoryRegion.SharedConfigDictionary,
        registeredMemoryRegion);

    return hr;
}

//----------------------------------------------------------------------------
// NAME: MlosContext::RegisterNamedEvent
//
// PURPOSE:
// Registers a named event in the global memory region.
//
// RETURNS:
//  HRESULT.
//
// NOTES:
//
_Must_inspect_result_
HRESULT MlosContext::RegisterNamedEvent(
    _In_ Internal::MemoryRegionId memoryRegionId,
    _In_z_ const char* name)
{
    ComponentConfig<Internal::RegisteredNamedEventConfig> registeredNamedEvent;

    registeredNamedEvent.MemoryRegionId = memoryRegionId;
    registeredNamedEvent.Name = name;

    HRESULT hr = SharedConfigManager::CreateOrUpdateFrom(
        m_globalMemoryRegion.SharedConfigDictionary,
        registeredNamedEvent);

    return hr;
}

//----------------------------------------------------------------------------
// NAME: MlosContext::ControlChannel
//
// PURPOSE:
//  Gets the shared config memory region.
//
// RETURNS:
//
// NOTES:
//
SharedMemoryRegionView<Internal::SharedConfigMemoryRegion>& MlosContext::SharedConfigMemoryRegionView()
{
    return m_sharedConfigManager.m_sharedConfigMemoryRegionView;
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
bool MlosContext::IsControlChannelActive() const
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
bool MlosContext::IsFeedbackChannelActive() const
{
    return !(m_feedbackChannel.Sync.TerminateChannel);
}
}
}
