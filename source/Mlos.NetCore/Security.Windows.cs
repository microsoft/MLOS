// -----------------------------------------------------------------------
// <copyright file="Security.Windows.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.ComponentModel;
using System.Runtime.InteropServices;

namespace Mlos.Core.Windows
{
    /// <summary>
    /// Security helper class.
    /// </summary>
    /// <remarks>
    /// Windows only.
    /// </remarks>
    internal static class Security
    {
        /// <summary>
        /// Gets the current user security identifier.
        /// </summary>
        /// <returns></returns>
        internal static SecurityIdentifierSafePtr GetCurrentUserSid()
        {
            using ProcessTokenSafeHandle currentProcessHandle = Native.GetCurrentProcess();

            if (!Native.OpenProcessToken(currentProcessHandle, Native.AccessRights.TokenQuery, out AccessTokenSafeHandle tokenHandle))
            {
                throw new Win32Exception(Marshal.GetLastWin32Error());
            }

            using AccessTokenSafeHandle scopedTokenHandle = tokenHandle;

            // Get the token user.
            //
            if (!Native.GetTokenInformation(tokenHandle, Native.TokenInformationClass.TokenUser, IntPtr.Zero, 0, out uint returnLength))
            {
                if (Marshal.GetLastWin32Error() != Native.ErrorInsufficientBuffer)
                {
                    throw new Win32Exception(Marshal.GetLastWin32Error());
                }
            }

            using LocalAllocSafePtr tokenUserPtr = Native.LocalAlloc(Native.LocalMemoryFlags.Fixed | Native.LocalMemoryFlags.ZeroInit, returnLength);
            if (tokenUserPtr.IsInvalid)
            {
                throw new Win32Exception(Marshal.GetLastWin32Error());
            }

            if (!Native.GetTokenInformation(tokenHandle, Native.TokenInformationClass.TokenUser, tokenUserPtr.DangerousGetHandle(), returnLength, out returnLength))
            {
                throw new Win32Exception(Marshal.GetLastWin32Error());
            }

            Native.TOKEN_USER tokenUser = Marshal.PtrToStructure<Native.TOKEN_USER>(tokenUserPtr.DangerousGetHandle());

            uint userSidLength = Native.GetLengthSid(tokenUser.User.Sid);

            SecurityIdentifierSafePtr currentUserSidPtr = Native.AllocSecurityIdentifier(Native.LocalMemoryFlags.Fixed | Native.LocalMemoryFlags.ZeroInit, userSidLength);
            if (currentUserSidPtr.IsInvalid)
            {
                throw new Win32Exception(Marshal.GetLastWin32Error());
            }

            if (!Native.CopySid(userSidLength, currentUserSidPtr, tokenUser.User.Sid))
            {
                currentUserSidPtr.Dispose();
                throw new Win32Exception(Marshal.GetLastWin32Error());
            }

            return currentUserSidPtr;
        }

        /// <summary>
        /// Gets the current user security identifier as a string.
        /// </summary>
        internal static string CurrentUserSidString
        {
            get
            {
                using (SecurityIdentifierSafePtr currentUserSid = GetCurrentUserSid())
                {
                    if (!Native.ConvertSidToStringSid(currentUserSid.DangerousGetHandle(), out string currentUserSidString))
                    {
                        throw new Win32Exception(Marshal.GetLastWin32Error());
                    }

                    return currentUserSidString;
                }
            }
        }

        /// <summary>
        /// Creates a default security descriptor.
        /// </summary>
        /// <returns></returns>
        internal static SecurityDescriptorSafePtr CreateDefaultSecurityDescriptor()
        {
            string currentUserSid = CurrentUserSidString;

            // Create a security descriptor.
            // General Access for current user.
            // https://itconnect.uw.edu/wares/msinf/other-help/understanding-sddl-syntax/
            //
            string securityDescriptorStr = $"D:P(A;;GA;;;{currentUserSid})";

            return CreateSecurityDescriptorFromString(securityDescriptorStr);
        }

        /// <summary>
        /// Creates a security descriptor from the security descriptor string.
        /// </summary>
        /// <param name="securityDescriptorString"></param>
        /// <returns></returns>
        internal static SecurityDescriptorSafePtr CreateSecurityDescriptorFromString(string securityDescriptorString)
        {
            if (!Native.ConvertStringSecurityDescriptorToSecurityDescriptor(
                securityDescriptorString,
                stringSDRevision: 1,
                out SecurityDescriptorSafePtr securityDescriptor,
                out int _))
            {
                throw new ArgumentException("Invalid security descriptor string", new Win32Exception(Marshal.GetLastWin32Error()));
            }

            return securityDescriptor;
        }

        /// <summary>
        /// Check if handle has been created by authorized user.
        /// </summary>
        /// <param name="handle"></param>
        /// <remarks>
        /// Authorized users:
        ///  - built in administrators,
        ///  - current user.
        /// </remarks>
        internal static void VerifyHandleOwner(SafeHandle handle)
        {
            // Get the security descriptor for given handle.
            //
            int result = Native.GetSecurityInfo(
                handle,
                Native.SecurityObjectType.SecurityFileObject,
                Native.SecurityInformation.OwnerSecurityInformation,
                sidOwner: IntPtr.Zero,
                sidGroup: IntPtr.Zero,
                dacl: IntPtr.Zero,
                sacl: IntPtr.Zero,
                out SecurityDescriptorSafePtr handleSecurityDescriptor);
            using SecurityDescriptorSafePtr scopedHandleSecurityDescriptor = handleSecurityDescriptor;
            if (result != Native.ErrorSuccess)
            {
                throw new Win32Exception(result);
            }

            if (!Native.GetSecurityDescriptorOwner(handleSecurityDescriptor, out IntPtr handleOwnerSid, out bool ownerDefaulted1))
            {
                throw new Win32Exception(Marshal.GetLastWin32Error());
            }

            // Allow access, if owner is local system.
            //
            if (Native.IsWellKnownSid(handleOwnerSid, Native.WellKnownSidType.WinLocalSystemSid))
            {
                return;
            }

            // Allow access, if owner is builtin administator.
            //
            if (Native.IsWellKnownSid(handleOwnerSid, Native.WellKnownSidType.WinBuiltinAdministratorsSid))
            {
                return;
            }

            // Allow acces, if current user is the owner.
            //
            using SecurityIdentifierSafePtr currentOwnerSecuryIdentifier = GetCurrentUserSid();
            if (Native.EqualSid(currentOwnerSecuryIdentifier.DangerousGetHandle(), handleOwnerSid))
            {
                return;
            }

            throw new UnauthorizedAccessException();
        }
    }
}
