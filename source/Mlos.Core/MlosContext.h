//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: MlosContext.h
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
// NAME: MlosContext
//
// PURPOSE:
//  Provides the main entrypoint for an application component to interact with an
//  (external) agent over shared memory channels.
//
//  Application components use this class to
//  1. Register their settings assembly so the external agent can process the
//  application component messages.
//  2. Send different types of messages (e.g. control, telemetry, etc.)
//
// NOTES:
//
class MlosContext
{
protected:
    MlosContext(
        Internal::GlobalMemoryRegion& globalMemoryRegion,
        ISharedChannel& controlChannel,
        ISharedChannel& telemetryChannel,
        ISharedChannel& feedbackChannel) noexcept;

public:
    // Registers the settings assembly.
    //
    HRESULT RegisterSettingsAssembly(
        const char* assemblyFileName,
        uint32_t assemblyDispatchTableBaseIndex);

    // Registers the component config.
    //
    template<typename T>
    HRESULT RegisterComponentConfig(ComponentConfig<T>& componentConfig);

    ISharedChannel& ControlChannel() const;

    ISharedChannel& FeedbackChannel() const;

    template<typename TMessage>
    void SendControlMessage(TMessage& message);

    template<typename TMessage>
    void SendFeedbackMessage(TMessage& message);

    template<typename TMessage>
    void SendTelemetryMessage(const TMessage& message) const;

    void TerminateControlChannel();

    void TerminateFeedbackChannel();

    bool IsControlChannelActive();

    bool IsFeedbackChannelActive();

protected:
    // Creates a shared memory view and registers it with Mlos Agent.
    //
    template<typename T>
    HRESULT CreateMemoryRegion(
        const char* const sharedMemoryName,
        size_t memoryRegionSize,
        _Out_ SharedMemoryRegionView<T>& sharedMemoryRegionView);

    // Shared config manager.
    //
    SharedConfigManager m_sharedConfigManager;

    // Global memory region.
    //
    Internal::GlobalMemoryRegion& m_globalMemoryRegion;

    // Channel used to send the control messages (register assembly, register shared config).
    //
    ISharedChannel& m_controlChannel;

    // Channel used to send the telemetry messages.
    //
    ISharedChannel& m_telemetryChannel;

    // Feedback channel used to receive messages from the Mlos.Agent.
    //
    ISharedChannel& m_feedbackChannel;

    // Friend classes.
    //
    friend class SharedConfigManager;

    template<typename T>
    friend class ComponentConfig;
};
}
}
