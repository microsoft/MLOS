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
private:
    void Initialize(const TProxy& initConfig)
    {
        static_assert(sizeof(SharedConfigHeader) == 32, "SharedConfigHeader has incorrect size.");

        m_header.ConfigId = 1;
        m_header.CodegenTypeIndex = TypeMetadataInfo::CodegenTypeIndex<TProxy>();

        // #TODO hacky, we assume the header has been updated
        // m_header.Address = { 0 };
        // #TODO remove address, not needed
        m_config = initConfig;
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
