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
    componentConfig.m_mlosContext = this;

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
}
}
