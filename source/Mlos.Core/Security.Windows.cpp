//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: Security.Windows.cpp
//
// Purpose:
//      <description>
//
// Notes:
//      <special-instructions>
//
//*********************************************************************

#include "Mlos.Core.h"

namespace Mlos
{
namespace Core
{
//----------------------------------------------------------------------------
// NAME: Security::GetCurrentUserSecurityIdentifierString
//
// PURPOSE:
//  Gets the current user security identifier.
//
// RETURNS:
//  HRESULT.
//
_Check_return_
HRESULT Security::GetCurrentUserSid(_Out_ PSID& currentUserSid)
{
    HRESULT hr = S_OK;
    HANDLE tokenHandle = INVALID_HANDLE_VALUE;
    PTOKEN_USER tokenUser = nullptr;
    DWORD currentUserSidLength = 0;

    currentUserSid = nullptr;

    if (!OpenProcessToken(GetCurrentProcess(), TOKEN_QUERY, &tokenHandle))
    {
        hr = HRESULT_FROM_WIN32(GetLastError());
    }

    // Obtain the size of the user information from the token.
    //
    DWORD tokenSize = 0;

    if (SUCCEEDED(hr))
    {
        if (!GetTokenInformation(tokenHandle, TokenUser, nullptr, 0, &tokenSize))
        {
            DWORD lastError = GetLastError();
            if (lastError != ERROR_INSUFFICIENT_BUFFER)
            {
                hr = HRESULT_FROM_WIN32(lastError);
            }
        }
    }

    // Allocate the memory for user token.
    //
    if (SUCCEEDED(hr))
    {
        tokenUser = reinterpret_cast<PTOKEN_USER>(LocalAlloc(LMEM_FIXED | LMEM_ZEROINIT, tokenSize));
        if (tokenUser == nullptr)
        {
            hr = E_OUTOFMEMORY;
        }
    }

    // Retrieve the user information from the token.
    //
    if (SUCCEEDED(hr))
    {
        if (!GetTokenInformation(tokenHandle, TokenUser, tokenUser, tokenSize, &tokenSize))
        {
            hr = HRESULT_FROM_WIN32(GetLastError());
        }
    }

    // Convert user security identifier to string format.
    //
    if (SUCCEEDED(hr))
    {
        currentUserSidLength = GetLengthSid(tokenUser->User.Sid);

        currentUserSid = reinterpret_cast<PSID>(LocalAlloc(LMEM_FIXED | LMEM_ZEROINIT, currentUserSidLength));
        if (currentUserSid == nullptr)
        {
            hr = E_OUTOFMEMORY;
        }
    }

    if (SUCCEEDED(hr))
    {
        if (!CopySid(currentUserSidLength, currentUserSid, tokenUser->User.Sid))
        {
            hr = HRESULT_FROM_WIN32(GetLastError());
        }
    }

    LocalFree(tokenUser);
    CloseHandle(tokenHandle);

    return hr;
}

//----------------------------------------------------------------------------
// NAME: Security::GetCurrentUserSecurityIdentifierString
//
// PURPOSE:
//  Gets the current user security identifier as a string.
//
// RETURNS:
//  HRESULT.
//
_Check_return_
HRESULT Security::GetCurrentUserSidString(_Out_ wchar_t*& currentUserSidString)
{
    HRESULT hr = S_OK;
    PSID currentUserSid = nullptr;

    currentUserSidString = nullptr;

    hr = GetCurrentUserSid(currentUserSid);

    // Convert user security identifier to string format.
    //
    if (SUCCEEDED(hr))
    {
        if (!ConvertSidToStringSidW(currentUserSid, &currentUserSidString))
        {
            hr = HRESULT_FROM_WIN32(GetLastError());
        }
    }

    return hr;
}

//----------------------------------------------------------------------------
// NAME: Security::CreateDefaultSecurityDescriptor
//
// PURPOSE:
//  Creates a default security descriptor.
//
// RETURNS:
//  HRESULT.
//
_Check_return_
HRESULT Security::CreateDefaultSecurityDescriptor(_Out_ PSECURITY_DESCRIPTOR& securityDescriptor)
{
    const int maxSDDLStringLength = 1024;

    LPWSTR currentUserSidString = nullptr;
    WCHAR securityDescriptorString[maxSDDLStringLength] = { 0 };

    HRESULT hr = Security::GetCurrentUserSidString(currentUserSidString);

    if (SUCCEEDED(hr))
    {
        // Create a security descriptor.
        // General Access for current user.
        // https://itconnect.uw.edu/wares/msinf/other-help/understanding-sddl-syntax/
        //
        hr = StringCchPrintfW(
            securityDescriptorString,
            _countof(securityDescriptorString),
            L"D:P(A;;GA;;;%s)",
            currentUserSidString);
    }

    if (SUCCEEDED(hr))
    {
        hr = CreateSecurityDescriptorFromString(securityDescriptorString, securityDescriptor);
    }

    LocalFree(currentUserSidString);

    return hr;
}

//----------------------------------------------------------------------------
// NAME: Security::CreateSecurityDescriptorFromString
//
// PURPOSE:
//  Creates a security descriptor from the security descriptor string.
//
// RETURNS:
//  HRESULT.
//
_Check_return_
HRESULT Security::CreateSecurityDescriptorFromString(
    _In_ const wchar_t* const securityDescriptorString,
    _Out_ PSECURITY_DESCRIPTOR& securityDescriptor)
{
    HRESULT hr = S_OK;

    if (!ConvertStringSecurityDescriptorToSecurityDescriptorW(
        securityDescriptorString,
        SDDL_REVISION_1 /* StringSDRevision */,
        &securityDescriptor,
        nullptr /* SecurityDescriptorSize */))
    {
        hr = HRESULT_FROM_WIN32(GetLastError());
    }

    return hr;
}

//----------------------------------------------------------------------------
// NAME: Security::VerifyHandleOwner
//
// PURPOSE:
//  Checks if handle has been created by authorized user.
//
// Authorized users:
//  - local system,
//  - built in administrators,
//  - current user.
//
// RETURNS:
//  HRESULT.
//
_Check_return_
HRESULT Security::VerifyHandleOwner(HANDLE handle)
{
    PSECURITY_DESCRIPTOR securityDescriptor = nullptr;
    PSID handleOwnerSid = nullptr;
    PSID currentUserSid = nullptr;
    HRESULT hr = S_OK;

    bool isAuthorized = false;

    // Get the security descriptor for given handle.
    //
    int result = GetSecurityInfo(
        handle,
        SE_FILE_OBJECT,
        OWNER_SECURITY_INFORMATION,
        &handleOwnerSid /* sidOwner */,
        nullptr /* sidGroup */,
        nullptr /* dacl */,
        nullptr /* sacl */,
        &securityDescriptor);
    if (result != ERROR_SUCCESS)
    {
        hr = HRESULT_FROM_WIN32(result);
    }

    if (!isAuthorized && SUCCEEDED(hr))
    {
        isAuthorized = IsWellKnownSid(handleOwnerSid, WELL_KNOWN_SID_TYPE::WinLocalSystemSid);
    }

    if (!isAuthorized && SUCCEEDED(hr))
    {
        isAuthorized = IsWellKnownSid(handleOwnerSid, WELL_KNOWN_SID_TYPE::WinBuiltinAdministratorsSid);
    }

    if (!isAuthorized && SUCCEEDED(hr))
    {
        hr = GetCurrentUserSid(currentUserSid);
    }

    if (!isAuthorized && SUCCEEDED(hr))
    {
        isAuthorized = EqualSid(handleOwnerSid, currentUserSid);
    }

    // Free allocated memory.
    //
    LocalFree(securityDescriptor);
    LocalFree(currentUserSid);

    if (!isAuthorized && SUCCEEDED(hr))
    {
        hr = E_ACCESSDENIED;
    }

    return hr;
}
}
}
