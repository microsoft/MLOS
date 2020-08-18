//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: Security.Windows.h
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
class Security
{
private:
    // Gets the current user security identifier.
    //
    _Check_return_
    static HRESULT GetCurrentUserSid(_Out_ PSID& currentUserSid);

    // Gets the current user security identifier as a string.
    //
    _Check_return_
    static HRESULT GetCurrentUserSidString(_Out_ wchar_t*& currentUserSidString);

public:
    // Creates a default security descriptor.
    //
    _Check_return_
    static HRESULT CreateDefaultSecurityDescriptor(_Out_ PSECURITY_DESCRIPTOR& securityDescriptor);

    // Function converts a string-format security descriptor into a valid, functional security descriptor.
    //
    _Check_return_
    static HRESULT CreateSecurityDescriptorFromString(
        _In_ const wchar_t* const securityDescriptorString,
        _Out_ PSECURITY_DESCRIPTOR& securityDescriptor);

    // Checks if handle has been created by authorized user.
    //
    _Check_return_
    static HRESULT VerifyHandleOwner(HANDLE handle);
};
}
}
