//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: ComponentConfig.inl
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
// NAME: ComponentConfig<T>::Bind
//
// PURPOSE:
//  Binds the component config located in the shared memory to the local component config.
//
// NOTES:
//
template<typename T>
void ComponentConfig<T>::Bind(SharedConfigType* sharedConfig)
{
    m_sharedConfig = sharedConfig;
}

//----------------------------------------------------------------------------
// NAME: ComponentConfig<T>::Update
//
// PURPOSE:
//  Copy shared memory config to the local config instance.
//
// NOTES:
//
template<typename T>
void ComponentConfig<T>::Update()
{
    // #TODO, not fully implemented.
    // - take a snapshot
    // - if current version does not match snapshot version try again.
    //
    *static_cast<T*>(this) = m_sharedConfig->m_config;
}

//----------------------------------------------------------------------------
// NAME: ComponentConfig<T>::CompareKey
//
// PURPOSE:
//  Compares component config with the shared memory config by the key.
//
// NOTES:
//
template<typename T>
bool ComponentConfig<T>::CompareKey(SharedConfigHeader* sharedConfigHeader)
{
    return TypeMetadataInfo::CompareKey<T>(
        *this,
        (reinterpret_cast<const ComponentConfig<T>::SharedConfigType*>(sharedConfigHeader))->m_config);
}

//----------------------------------------------------------------------------
// NAME: ComponentConfig<T>::SendTelemetryMessage
//
// PURPOSE:
//  Sends the message using telemetry channel.
//
// RETURNS:
//
// NOTES:
//
template<typename T>
template<typename TMessage>
void ComponentConfig<T>::SendTelemetryMessage(const TMessage& message) const
{
    // #TODO
    // - add object as parameter
    // - update current configuration id.
    //
    m_mlosContext.m_telemetryChannel.SendMessage(message);
}
}
}
