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
// NAME: SharedConfigManager::Constructor
//
// PURPOSE:
//
// RETURNS:
//
// NOTES:
//
SharedConfigManager::SharedConfigManager() noexcept
  : CleanupOnClose(false)
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
    m_sharedConfigMemoryRegionView.Close(CleanupOnClose);
}

//----------------------------------------------------------------------------
// NAME: SharedConfigManager::AssignSharedConfigMemoryRegion
//
// PURPOSE:
//
// RETURNS:
//
// NOTES:
//
void SharedConfigManager::AssignSharedConfigMemoryRegion(
    _In_ SharedMemoryRegionView<Internal::SharedConfigMemoryRegion>&& sharedConfigMemoryRegionView)
{
    m_sharedConfigMemoryRegionView.Assign(std::move(sharedConfigMemoryRegionView));
}
}
}
