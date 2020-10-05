//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: SharedConfigManager.cpp
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
// NAME: SharedConfigManager::Contructor
//
// PURPOSE:
//
// RETURNS:
//
// NOTES:
//
SharedConfigManager::SharedConfigManager(MlosContext& mlosContext) noexcept
  : m_mlosContext(mlosContext),
    CleanupOnClose(false)
{
}

//----------------------------------------------------------------------------
// NAME: SharedConfigManager::Destructor
//
// PURPOSE:
//
// RETURNS:
//
// NOTES:
//
SharedConfigManager::~SharedConfigManager()
{
    m_sharedConfigMemRegionView.CleanupOnClose |= CleanupOnClose;
}

//----------------------------------------------------------------------------
// NAME: SharedConfigManager::RegisterSharedConfigMemoryRegion
//
// PURPOSE:
//  Creates a shared config memory region and registers it with the agent.
//
// RETURNS:
//  HRESULT.
//
// NOTES:
//
HRESULT SharedConfigManager::RegisterSharedConfigMemoryRegion()
{
    // Create (allocate and register) shared config memory region.
    // See Also: Mlos.Agent/MainAgent.cs
    // #TODO now it can be configurable.
    //
    const char* const appConfigSharedMemoryName = "Host_Mlos.Config.SharedMemory";

    const size_t SharedMemorySize = 65536;

    HRESULT hr = m_mlosContext.CreateMemoryRegion(appConfigSharedMemoryName, SharedMemorySize, m_sharedConfigMemRegionView);
    if (FAILED(hr))
    {
        return hr;
    }

    Internal::SharedConfigMemoryRegion& sharedConfigMemoryRegion = m_sharedConfigMemRegionView.MemoryRegion();

    // Register shared memory region.
    //
    ComponentConfig<Internal::RegisteredMemoryRegionConfig> registeredMemoryRegion(m_mlosContext);

    registeredMemoryRegion.MemoryRegionIndex = sharedConfigMemoryRegion.MemoryHeader.MemoryRegionId;
    registeredMemoryRegion.SharedMemoryMapName = appConfigSharedMemoryName;
    registeredMemoryRegion.MemoryRegionSize = SharedMemorySize;

    // Register memory map region in the global shared region.
    //
    hr = SharedConfigManager::CreateOrUpdateFrom(
        m_mlosContext.m_globalMemoryRegion.SharedConfigDictionary,
        registeredMemoryRegion);

    // Register a shared config memory region.
    //
    Internal::RegisterSharedConfigMemoryRegionRequestMessage msg = { 0 };
    msg.MemoryRegionId = sharedConfigMemoryRegion.MemoryHeader.MemoryRegionId;

    m_mlosContext.SendControlMessage(msg);

    return hr;
}
}
}
