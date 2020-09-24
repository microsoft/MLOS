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

private:
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

    HRESULT Initialize();

    InternalMlosContextInitializer(InternalMlosContextInitializer&& initializer) noexcept;

    InternalMlosContextInitializer(const InternalMlosContextInitializer&) = delete;

    InternalMlosContextInitializer& operator=(const InternalMlosContextInitializer&) = delete;

public:
    // Global shared memory region.
    //
    SharedMemoryRegionView<Internal::GlobalMemoryRegion> m_globalMemoryRegionView;

    // Named shared memory for Telemetry and Control Channel.
    //
    SharedMemoryMapView m_controlChannelMemoryMapView;

    // Named shared memory for Feedback Channel.
    //
    SharedMemoryMapView m_feedbackChannelMemoryMapView;
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

//----------------------------------------------------------------------------
// NAME: InterProcessMlosContextInitializer
//
// PURPOSE:
//  Helper class used to initialize shared memory for inter-process MlosContexts.
//
// NOTES:
//
class InterProcessMlosContextInitializer
{
public:
    InterProcessMlosContextInitializer() {}

    HRESULT Initialize();

    InterProcessMlosContextInitializer(InterProcessMlosContextInitializer&& initializer) noexcept;

    InterProcessMlosContextInitializer(const InterProcessMlosContextInitializer&) = delete;

    InterProcessMlosContextInitializer& operator=(const InterProcessMlosContextInitializer&) = delete;

public:
    // Global shared memory region.
    //
    SharedMemoryRegionView<Internal::GlobalMemoryRegion> m_globalMemoryRegionView;

    // Named shared memory for Telemetry and Control Channel.
    //
    SharedMemoryMapView m_controlChannelMemoryMapView;

    // Named shared memory for Feedback Channel.
    //
    SharedMemoryMapView m_feedbackChannelMemoryMapView;

    // Channel policy for control channel.
    //
    InterProcessSharedChannelPolicy m_controlChannelPolicy;

    // Channel policy for feedback channel.
    //
    InterProcessSharedChannelPolicy m_feedbackChannelPolicy;
};

//----------------------------------------------------------------------------
// NAME: InterProcessMlosContext
//
// PURPOSE:
//  Implementation of an inter-process MlosContext.
//
class InterProcessMlosContext : public MlosContext
{
public:
    InterProcessMlosContext(InterProcessMlosContextInitializer&&) noexcept;

private:
    InterProcessMlosContextInitializer m_contextInitializer;

    InterProcessSharedChannel m_controlChannel;

    InterProcessSharedChannel m_feedbackChannel;

    NamedEvent m_controlChannelNamedEvent;

    NamedEvent m_feedbackChannelNamedEvent;
};
}
}
