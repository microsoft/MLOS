//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: SharedConfig.h
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
// SharedConfig.
//  Represents component configuration stored in the shared memory.
//
template<typename TProxy>
class SharedConfig
{
public:
    // Initializes the shared config from the component one.
    //
    void InitializeFromDefaultConfig(const TProxy& defaultConfig)
    {
        static_assert(sizeof(SharedConfigHeader) == 32, "SharedConfigHeader has incorrect size.");

        m_header.ConfigId = 1;
        m_header.CodegenTypeIndex = TypeMetadataInfo::CodegenTypeIndex<TProxy>();

        // Copy given config to the shared memory.
        //
        ObjectSerialization::Serialize(BytePtr(&m_config), defaultConfig);
    }

private:
    SharedConfigHeader m_header;
    TProxy m_config;

    // Friend classes.
    //
    template<typename>
    friend class ComponentConfig;

    friend class MlosContext;
    friend class SharedConfigManager;
};
}
}
