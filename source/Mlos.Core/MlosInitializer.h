//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: MlosInitializer.h
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
// NAME: MlosInitializer
//
// PURPOSE:
//  Creates a Mlos context instance.
//
// NOTES:
//
template<typename TMlosContext>
class MlosInitializer
{
public:
    MlosInitializer() = default;

    template<typename... TArgs>
    _Must_inspect_result_
    HRESULT CreateContext(_In_ TArgs&&... args);

    // Gets the context.
    //
    TMlosContext& MlosContext();

private:
    AlignedInstance<TMlosContext> m_context;
};
}
}
