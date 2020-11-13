//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: MlosContext.inl
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
// NAME: MlosContext::CreateMemoryRegion
//
// PURPOSE:
//  Creates a shared memory view and registers it with Mlos.Agent.
//
// RETURNS:
//  HRESULT.
//
// NOTES:
//  Function opens or creates a shared memory view.
//
template<typename T>
_Must_inspect_result_
HRESULT MlosContext::CreateMemoryRegion(
    _In_z_ const char* const sharedMemoryName,
    _In_ size_t memoryRegionSize,
    _Out_ SharedMemoryRegionView<T>& sharedMemoryRegionView)
{
    // Create region view, initialize it on create.
    //
    HRESULT hr = sharedMemoryRegionView.CreateOrOpen(sharedMemoryName, memoryRegionSize);
    if (FAILED(hr))
    {
        return hr;
    }

    // Initialize memory region if we created a new mapping, Otherwise assume Mlos.Agent has initialized it.
    //
    T& memoryRegion = sharedMemoryRegionView.MemoryRegion();

    const bool createdNewRegion = (hr == S_OK);
    if (createdNewRegion)
    {
        // Update region index counter if created a new one.
        //
        memoryRegion.MemoryHeader.MemoryRegionId.Index = ++m_globalMemoryRegion.GlobalMemoryRegionIndex;
    }

    return S_OK;
}

//----------------------------------------------------------------------------
// NAME: MlosContext::RegisterComponentConfig
//
// PURPOSE:
//  Registers the component config. If the shared config already exists update the local config instance.
//
// RETURNS:
//  HRESULT.
//
// NOTES:
//
template<typename T>
_Must_inspect_result_
HRESULT MlosContext::RegisterComponentConfig(_Inout_ ComponentConfig<T>& componentConfig)
{
    // Create or find existing shared configuration.
    //
    return m_sharedConfigManager.CreateOrUpdateFrom(componentConfig);
}

//----------------------------------------------------------------------------
// NAME: MlosContext::SendControlMessage
//
// PURPOSE:
//  Sends the message using control channel.
//
// RETURNS:
//
// NOTES:
//
template<typename TMessage>
void MlosContext::SendControlMessage(_In_ TMessage& message)
{
    m_controlChannel.SendMessage(message);
}

//----------------------------------------------------------------------------
// NAME: MlosContext::SendFeedbackMessage
//
// PURPOSE:
//  Sends the message using feedback channel.
//
// RETURNS:
//
// NOTES:
//
template<typename TMessage>
void MlosContext::SendFeedbackMessage(_In_ TMessage& message)
{
    m_feedbackChannel.SendMessage(message);
}

//----------------------------------------------------------------------------
// NAME: MlosContext::SendTelemetryMessage
//
// PURPOSE:
//  Sends the message using telemetry channel.
//
// RETURNS:
//
// NOTES:
//
template<typename TMessage>
void MlosContext::SendTelemetryMessage(_In_ const TMessage& message) const
{
    m_telemetryChannel.SendMessage(message);
}

//----------------------------------------------------------------------------
// NAME: MlosContextFactory::Create
//
// PURPOSE:
//  Creates a MlosContext instance.
//
// RETURNS:
//
// NOTES:
//
template<typename TMlosContext>
_Must_inspect_result_
HRESULT MlosContextFactory<TMlosContext>::Create()
{
    typename TMlosContext::InitializerType initializer;
    HRESULT hr = initializer.Initialize();

    if (SUCCEEDED(hr))
    {
        // Create Mlos context.
        //
        m_context.Initialize(std::move(initializer));
    }

    return hr;
}
}
}
