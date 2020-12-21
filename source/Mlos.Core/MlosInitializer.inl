//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: MlosInitializer.inl
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
// NAME: MlosInitializer::CreateContext
//
// PURPOSE:
//  Creates a Mlos context instance.
//
// RETURNS:
//
// NOTES:
//
template<typename TMlosContext>
template<typename... TArgs>
_Must_inspect_result_
HRESULT MlosInitializer<TMlosContext>::CreateContext(_In_ TArgs&&... args)
{
    // Create context.
    //
    return TMlosContext::Create(m_context, std::forward<TArgs>(args)...);
}

//----------------------------------------------------------------------------
// NAME: MlosInitializer::MlosContext
//
// PURPOSE:
//  Gets the Mlos context.
//
// RETURNS:
//  Returns created Mlos context.
// NOTES:
//
template<typename TMlosContext>
TMlosContext& MlosInitializer<TMlosContext>::MlosContext()
{
    return m_context;
}
}
}

