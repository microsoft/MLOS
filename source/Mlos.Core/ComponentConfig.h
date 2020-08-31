//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: ComponentConfig.h
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
class MlosContext;

//----------------------------------------------------------------------------
// NAME: ComponentConfig
//
// PURPOSE:
//  Represents component configuration stored in the target process.
//
// NOTES:
//
template<typename T>
class ComponentConfig : public T
{
public:
    using SharedConfigType = SharedConfig<T>;
    using TProxyObjectType = typename T::ProxyObjectType;

    ComponentConfig(MlosContext& mlosContext) noexcept
      : m_mlosContext(mlosContext),
        m_sharedConfig(nullptr)
    {}

    // Binds the component config located in the shared memory to the local component config.
    //
    void Bind(SharedConfigType* sharedConfig);

    // Updates the component config from the shared config.
    //
    void Update();

    // Compares the configs by the key.
    //
    bool CompareKey(SharedConfigHeader* sharedConfigHeader);

    // Gets the proxy object to the config located in the shared memory.
    //
    TProxyObjectType Proxy()
    {
        return TProxyObjectType(&m_sharedConfig->m_config);
    }

    // Sends the telemetry message.
    //
    template<typename TMessage>
    void SendTelemetryMessage(const TMessage& message) const;

private:
    // MlosContext.
    //
    MlosContext& m_mlosContext;

    // Pointer to the shared config instance stored in the shared memory.
    //
    SharedConfigType* m_sharedConfig;

    // Friend classes.
    //
    friend class MlosContext;

    friend class SharedConfigManager;
};
}
}
