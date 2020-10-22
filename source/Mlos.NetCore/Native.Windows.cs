// -----------------------------------------------------------------------
// <copyright file="Native.Windows.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Runtime.InteropServices;
using System.Security.Permissions;

using Microsoft.Win32.SafeHandles;

namespace Mlos.Core.Windows
{
    /// <summary>
    /// Windows PInvoke functions.
    /// </summary>
    internal static unsafe class Native
    {
        private const string AdvapiLib = "advapi32";
        private const string KernelLib = "kernel32";
        private const string UserLib = "user32";

        internal const int SddlRevision1 = 1;

        internal const uint Infinite = 0xFFFFFFFF;

        internal const int ErrorSuccess = 0;
        internal const int ErrorInsufficientBuffer = 122;

        /// <summary>
        /// Represents invalid pointer (void *) -1.
        /// </summary>
        internal static IntPtr InvalidPointer = IntPtr.Subtract(IntPtr.Zero, 1);

        #region WinAPI

        /// <summary>
        /// Creates or opens a named or unnamed file mapping object for a specified file.
        /// </summary>
        /// <param name="fileHandle"></param>
        /// <param name="fileMappingAttributes"></param>
        /// <param name="fileMapProtect"></param>
        /// <param name="maximumSizeHigh"></param>
        /// <param name="maximumSizeLow"></param>
        /// <param name="name"></param>
        /// <returns></returns>
        [DllImport(KernelLib, SetLastError = true, CharSet = CharSet.Unicode)]
        internal static extern SharedMemorySafeHandle CreateFileMapping(
            IntPtr fileHandle,
            ref SECURITY_ATTRIBUTES fileMappingAttributes,
            FileMapProtection fileMapProtect,
            uint maximumSizeHigh,
            uint maximumSizeLow,
            string name);

        /// <summary>
        /// Opens a named file mapping object.
        /// </summary>
        /// <param name="desiredAccess"></param>
        /// <param name="inheritHandle"></param>
        /// <param name="name"></param>
        /// <returns></returns>
        [DllImport(KernelLib, SetLastError = true, CharSet = CharSet.Unicode)]
        internal static extern SharedMemorySafeHandle OpenFileMapping(
            MemoryMappedFileAccess desiredAccess,
            bool inheritHandle,
            string name);

        /// <summary>
        /// Maps a view of a file mapping into the address space of a calling process.
        /// </summary>
        /// <param name="fileMapping"></param>
        /// <param name="desiredAccess"></param>
        /// <param name="fileOffsetHigh"></param>
        /// <param name="fileOffsetLow"></param>
        /// <param name="numberOfBytesToMap"></param>
        /// <returns></returns>
        [DllImport(KernelLib, SetLastError = true)]
        internal static extern MemoryMappingSafeHandle MapViewOfFile(
            SharedMemorySafeHandle fileMapping,
            MemoryMappedFileAccess desiredAccess,
            int fileOffsetHigh,
            int fileOffsetLow,
            int numberOfBytesToMap);

        /// <summary>
        /// Closes an open object handle.
        /// </summary>
        /// <param name="handle"></param>
        /// <returns></returns>
        [DllImport(KernelLib, SetLastError = true)]
        internal static extern bool CloseHandle(IntPtr handle);

        /// <summary>
        /// Retrieves information about a range of pages within the virtual address space of a specified process.
        /// </summary>
        /// <param name="hProcess"></param>
        /// <param name="lpAddress"></param>
        /// <param name="lpBuffer"></param>
        /// <param name="dwLength"></param>
        /// <returns></returns>
        [DllImport(KernelLib, SetLastError = true)]
        internal static extern int VirtualQueryEx(IntPtr hProcess, IntPtr lpAddress, out MEMORY_BASIC_INFORMATION lpBuffer, uint dwLength);

        /// <summary>
        /// Unmaps a mapped view of a file from the calling process's address space.
        /// </summary>
        /// <param name="lpBaseAddress"></param>
        /// <returns></returns>
        [DllImport(KernelLib, SetLastError = true)]
        internal static extern bool UnmapViewOfFile(IntPtr lpBaseAddress);

        /// <summary>
        /// Creates or opens a named or unnamed event object.
        /// </summary>
        /// <param name="fileMappingAttributes"></param>
        /// <param name="manualReset"></param>
        /// <param name="initialState"></param>
        /// <param name="name"></param>
        /// <returns></returns>
        [DllImport(KernelLib, CharSet = CharSet.Unicode, SetLastError = true)]
        internal static extern EventSafeHandle CreateEvent(
            ref SECURITY_ATTRIBUTES fileMappingAttributes,
            bool manualReset,
            bool initialState,
            string name);

        [DllImport(KernelLib, CharSet = CharSet.Unicode, SetLastError = true)]
        internal static extern EventSafeHandle OpenEvent(EventAccess desiredAccess, bool inheritHandle, string lpName);

        [DllImport(KernelLib, SetLastError = true)]
        internal static extern bool SetEvent(EventSafeHandle hEvent);

        [DllImport(KernelLib, SetLastError = true)]
        internal static extern int WaitForSingleObject(EventSafeHandle handle, uint milliseconds);

        [DllImport(AdvapiLib, CharSet = CharSet.Unicode, SetLastError = true, ExactSpelling = false)]
        internal static extern bool ConvertStringSecurityDescriptorToSecurityDescriptor(
              [In] string stringSecurityDescriptor,
              [In] uint stringSDRevision,
              [Out] out SecurityDescriptorSafePtr securityDescriptor,
              [Out] out int securityDescriptorSize);

        [DllImport(AdvapiLib, CharSet = CharSet.Unicode, SetLastError = true, ExactSpelling = false)]
        internal static extern bool ConvertSecurityDescriptorToStringSecurityDescriptor(
              [In] SecurityDescriptorSafePtr securityDescriptor,
              [In] uint stringSDRevision,
              [In] SecurityInformation securityInformation,
              [Out] out string stringSecurityDescriptor,
              [Out] out uint stringSecurityDescriptorLength);

        [DllImport(KernelLib, SetLastError = true)]
        internal static extern ProcessTokenSafeHandle GetCurrentProcess();

        [DllImport(AdvapiLib, PreserveSig = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        public static extern bool OpenProcessToken(
            ProcessTokenSafeHandle processHandle,
            AccessRights desiredAccess,
            out AccessTokenSafeHandle tokenHandle);

        [DllImport(AdvapiLib, CharSet = CharSet.Unicode, SetLastError = true, ExactSpelling = false)]
        internal static extern bool GetTokenInformation(
            [In] AccessTokenSafeHandle tokenHandle,
            [In] TokenInformationClass tokenInformationClass,
            [In] IntPtr tokenInformation,
            [In] uint tokenInformationLength,
            [Out] out uint returnLength);

        [DllImport(UserLib, CharSet = CharSet.Unicode, SetLastError = true, ExactSpelling = false)]
        internal static extern bool GetUserObjectSecurity(
            [In] IntPtr handle,
            ref SecurityInformation securityInformation,
            [Out] IntPtr securityDescriptor,
            [In] uint securityDescriptorSize,
            [Out] out uint lengthNeeded);

        [DllImport(AdvapiLib, CharSet = CharSet.Unicode, SetLastError = true)]
        internal static extern bool ConvertSidToStringSid(IntPtr pSid, out string strSid);

        [DllImport(KernelLib)]
        internal static extern LocalAllocSafePtr LocalAlloc(LocalMemoryFlags localMemFlags, uint uBytes);

        [DllImport(KernelLib, EntryPoint = "LocalAlloc")]
        internal static extern SecurityDescriptorSafePtr AllocSecurityDescriptor(LocalMemoryFlags localMemFlags, uint uBytes);

        [DllImport(KernelLib, EntryPoint = "LocalAlloc")]
        internal static extern SecurityIdentifierSafePtr AllocSecurityIdentifier(LocalMemoryFlags localMemFlags, uint uBytes);

        [DllImport(AdvapiLib, EntryPoint = "GetSecurityInfo", SetLastError = true)]
        internal static extern int GetSecurityInfo(
            [In] SafeHandle handle,
            [In] SecurityObjectType objectType,
            [In] SecurityInformation securityInformation,
            [In] IntPtr sidOwner,
            [In] IntPtr sidGroup,
            [In] IntPtr dacl,
            [In] IntPtr sacl,
            [Out] out SecurityDescriptorSafePtr securityDescriptor);

        [DllImport(AdvapiLib, SetLastError = true)]
        internal static extern bool GetSecurityDescriptorOwner(
            SecurityDescriptorSafePtr pSecurityDescriptor,
            out IntPtr owner,
            out bool ownerDefaulted);

        [DllImport(AdvapiLib, SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        internal static extern bool EqualSid(IntPtr sid1, IntPtr sid2);

        /// <summary>
        /// Copies a security identifier (SID) to a buffer.
        /// </summary>
        /// <param name="destinationSidLength"></param>
        /// <param name="destinationSid"></param>
        /// <param name="sourceSid"></param>
        /// <returns></returns>
        [DllImport(AdvapiLib, SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        internal static extern bool CopySid(uint destinationSidLength, SecurityIdentifierSafePtr destinationSid, IntPtr sourceSid);

        /// <summary>
        /// Compares a SID to a well-known SID and returns true if they match.
        /// </summary>
        /// <param name="sid"></param>
        /// <param name="type"></param>
        /// <returns></returns>
        [DllImport(AdvapiLib, EntryPoint = "IsWellKnownSid", CallingConvention = CallingConvention.Winapi, SetLastError = true)]
        internal static extern bool IsWellKnownSid(IntPtr sid, WellKnownSidType type);

        /// <summary>
        /// Returns the length, in bytes, of a valid security identifier (SID).
        /// </summary>
        /// <param name="sid"></param>
        /// <returns></returns>
        [DllImport(AdvapiLib)]
        internal static extern uint GetLengthSid(IntPtr sid);

        [DllImport(KernelLib, PreserveSig = true)]
        internal static extern IntPtr LocalFree(IntPtr hMem);
        #endregion

        #region Win32 structures
        [StructLayoutAttribute(LayoutKind.Sequential)]
        internal struct MEMORY_BASIC_INFORMATION
        {
            public IntPtr BaseAddress;
            public IntPtr AllocationBase;
            public AllocationProtectEnum AllocationProtect;
            public IntPtr RegionSize;
            public StateEnum State;
            public AllocationProtectEnum Protect;
            public TypeEnum Type;
        }

        [StructLayoutAttribute(LayoutKind.Sequential)]
        internal struct SECURITY_DESCRIPTOR
        {
            public byte Revision;
            public byte Size;
            public short Control;
            public IntPtr Owner;
            public IntPtr Group;
            public IntPtr Sacl;
            public IntPtr Dacl;
        }

        /// <summary>
        /// Used to store security information for creating file handles.
        /// </summary>
        [StructLayout(LayoutKind.Sequential)]
        internal struct SECURITY_ATTRIBUTES
        {
            public uint Length;
            public IntPtr SecurityDescriptor;
            public bool InheritHandle;
        }

        internal struct TOKEN_USER
        {
            public SID_AND_ATTRIBUTES User;
        }

        [StructLayout(LayoutKind.Sequential)]
        internal struct SID_AND_ATTRIBUTES
        {
            public IntPtr Sid;
            public int Attributes;
        }
        #endregion

        #region Enums
        [Flags]
        internal enum SecurityInformation : uint
        {
            OwnerSecurityInformation = 0x00000001,
            GroupSecurityInformation = 0x00000002,
            DAclSecurityInformation = 0x00000004,
            SAclSecurityInformation = 0x00000008,
            AttributeSecurityInformation = 0x00000020,
            ScopeSecurityInformation = 0x00000040,
            UnprotectedSAclSecurityInformation = 0x10000000,
            UnprotectedDAclSecurityInformation = 0x20000000,
            ProtectedSAclSecurityInformation = 0x40000000,
            ProtectedDAclSecurityInformation = 0x80000000,
        }

        [Flags]
        internal enum EventAccess : uint
        {
            StandardRightsRequired = 0x000F0000,
            Synchronize = 0x00100000,
            EvenyModifyState = 0x0002,
            EventAllAccess = StandardRightsRequired | Synchronize | 0x3,
        }

        [Flags]
        internal enum MemoryMappedFileAccess : uint
        {
            SectionQuery = 0x0001,
            SectionMapWrite = 0x0002,
            SectionMapRead = 0x0004,
            SectionMapExecute = 0x0008,
            SectionExtendSize = 0x0010,
            SectionMapExecuteExplicit = 0x0020,
            StandardRightsRequired = 0x000F0000,
            SectionAllAccess = StandardRightsRequired | SectionQuery | SectionMapWrite | SectionMapRead | SectionMapExecute | SectionExtendSize,
            FileMapWrite = SectionMapWrite,
            FileMapRead = SectionMapRead,
            FileMapAllAccess = SectionAllAccess,
        }

        [Flags]
        internal enum FileMapProtection : uint
        {
            PageReadonly = 0x02,
            PageReadWrite = 0x04,
            PageWriteCopy = 0x08,
            PageExecuteRead = 0x20,
            PageExecuteReadWrite = 0x40,
            SectionCommit = 0x8000000,
            SectionImage = 0x1000000,
            SectionNoCache = 0x10000000,
            SectionReserve = 0x4000000,
        }

        [Flags]
        internal enum AllocationProtectEnum : uint
        {
            PageExecute = 0x00000010,
            PageExecuteRead = 0x00000020,
            PageExecuteReadWrite = 0x00000040,
            PageExecuteWriteCopy = 0x00000080,
            PageNoAccess = 0x00000001,
            PageReadOnly = 0x00000002,
            PageReadWrite = 0x00000004,
            PageWriteCopy = 0x00000008,
            PageGuard = 0x00000100,
            PageNoCache = 0x00000200,
            PageWriteCombine = 0x00000400,
        }

        [Flags]
        internal enum AccessRights : uint
        {
            Delete = 0x00010000,
            ReadControl = 0x00020000,
            Synchronize = 0x00100000,
            StandardRightsAll = 0x001F0000,
            StandardRightsRequired = 0x000F0000,

            EventModifyState = 0x0002,
            EventAllAccess = 0x001F0003,

            TokenAssignPrimary = 0x0001,
            TokenDuplicate = 0x0002,
            TokenImpersonate = 0x0004,
            TokenQuery = 0x0008,
            TokenQuerySource = 0x0010,
            TokenAdjustPrivileges = 0x0020,
            TokenAdjustGroups = 0x0040,
            TokenAdjustDefaukt = 0x0080,
            TokenAdjustSessionId = 0x0100,
        }

        [Flags]
        internal enum StateEnum : uint
        {
            MemCommit = 0x1000,
            MemFree = 0x10000,
            MemReserve = 0x2000,
        }

        [Flags]
        internal enum TypeEnum : uint
        {
            MemImage = 0x1000000,
            MemMapped = 0x40000,
            MemPrivate = 0x20000,
        }

        [Flags]
        internal enum LocalMemoryFlags
        {
            Fixed = 0x0000,
            Moveable = 0x0002,
            NoCompact = 0x0010,
            NoDiscard = 0x0020,
            ZeroInit = 0x0040,
            Modify = 0x0080,
            Discardable = 0x0F00,
            ValidFlags = 0x0F72,
            InvalidHandle = 0x8000,
            LHnd = Moveable | ZeroInit,
            LPtr = Fixed | ZeroInit,
            NonZeroLHnd = Moveable,
            NonZeroLPtr = Fixed,
        }

        internal enum TokenInformationClass : uint
        {
            TokenUser = 1,
            TokenGroups,
            TokenPrivileges,
            TokenOwner,
            TokenPrimaryGroup,
            TokenDefaultDacl,
            TokenSource,
            TokenType,
            TokenImpersonationLevel,
            TokenStatistics,
            TokenRestrictedSids,
            TokenSessionId,
            TokenGroupsAndPrivileges,
            TokenSessionReference,
            TokenSandBoxInert,
            TokenAuditPolicy,
            TokenOrigin,
        }

        internal enum SecurityObjectType
        {
            SecurityUnknownObjectType = 0,
            SecurityFileObject,
            SecurityService,
            SecurityPrinter,
            SecurityRegistryKey,
            SecurityLMShare,
            SecurityKernelObject,
            SecurityWindowObject,
            SecurityDirectoryServiceObject,
            SecurityDirectoryServiceObjectAll,
            SecurityProviderDefinedObject,
            SecurityWmiGuidObject,
            SecurityRegistryWow6432Key,
        }

        internal enum WellKnownSidType : uint
        {
            WinNullSid = 0,
            WinWorldSid = 1,
            WinLocalSid = 2,
            WinCreatorOwnerSid = 3,
            WinCreatorGroupSid = 4,
            WinCreatorOwnerServerSid = 5,
            WinCreatorGroupServerSid = 6,
            WinNtAuthoritySid = 7,
            WinDialupSid = 8,
            WinNetworkSid = 9,
            WinBatchSid = 10,
            WinInteractiveSid = 11,
            WinServiceSid = 12,
            WinAnonymousSid = 13,
            WinProxySid = 14,
            WinEnterpriseControllersSid = 15,
            WinSelfSid = 16,
            WinAuthenticatedUserSid = 17,
            WinRestrictedCodeSid = 18,
            WinTerminalServerSid = 19,
            WinRemoteLogonIdSid = 20,
            WinLogonIdsSid = 21,
            WinLocalSystemSid = 22,
            WinLocalServiceSid = 23,
            WinNetworkServiceSid = 24,
            WinBuiltinDomainSid = 25,
            WinBuiltinAdministratorsSid = 26,
            WinBuiltinUsersSid = 27,
            WinBuiltinGuestsSid = 28,
            WinBuiltinPowerUsersSid = 29,
            WinBuiltinAccountOperatorsSid = 30,
            WinBuiltinSystemOperatorsSid = 31,
            WinBuiltinPrintOperatorsSid = 32,
            WinBuiltinBackupOperatorsSid = 33,
            WinBuiltinReplicatorSid = 34,
            WinBuiltinPreWindows2000CompatibleAccessSid = 35,
            WinBuiltinRemoteDesktopUsersSid = 36,
            WinBuiltinNetworkConfigurationOperatorsSid = 37,
            WinAccountAdministratorSid = 38,
            WinAccountGuestSid = 39,
            WinAccountKrbtgtSid = 40,
            WinAccountDomainAdminsSid = 41,
            WinAccountDomainUsersSid = 42,
            WinAccountDomainGuestsSid = 43,
            WinAccountComputersSid = 44,
            WinAccountControllersSid = 45,
            WinAccountCertAdminsSid = 46,
            WinAccountSchemaAdminsSid = 47,
            WinAccountEnterpriseAdminsSid = 48,
            WinAccountPolicyAdminsSid = 49,
            WinAccountRasAndIasServersSid = 50,
            WinNTLMAuthenticationSid = 51,
            WinDigestAuthenticationSid = 52,
            WinSChannelAuthenticationSid = 53,
            WinThisOrganizationSid = 54,
            WinOtherOrganizationSid = 55,
            WinBuiltinIncomingForestTrustBuildersSid = 56,
            WinBuiltinPerfMonitoringUsersSid = 57,
            WinBuiltinPerfLoggingUsersSid = 58,
            WinBuiltinAuthorizationAccessSid = 59,
            WinBuiltinTerminalServerLicenseServersSid = 60,
        }
        #endregion
    }

    /// <summary>
    /// Represents an allocated memory.
    /// </summary>
    [SecurityPermission(SecurityAction.InheritanceDemand, UnmanagedCode = true)]
    [SecurityPermission(SecurityAction.Demand, UnmanagedCode = true)]
    internal class LocalAllocSafePtr : SafeHandleZeroOrMinusOneIsInvalid
    {
        /// <summary>
        /// Initializes a new instance of the <see cref="LocalAllocSafePtr"/> class.
        /// Constructor.
        /// </summary>
        internal LocalAllocSafePtr()
            : base(true)
        {
        }

        /// <inheritdoc/>
        protected override bool ReleaseHandle()
        {
            return Native.LocalFree(handle) == IntPtr.Zero;
        }
    }

    /// <summary>
    /// Represents an allocated memory for the security descriptor.
    /// </summary>
    [SecurityPermission(SecurityAction.InheritanceDemand, UnmanagedCode = true)]
    [SecurityPermission(SecurityAction.Demand, UnmanagedCode = true)]
    internal class SecurityDescriptorSafePtr : LocalAllocSafePtr
    {
        internal static SecurityDescriptorSafePtr Invalid = new SecurityDescriptorSafePtr();
    }

    /// <summary>
    /// Represents an allocated memory for the security identifier (sid).
    /// </summary>
    [SecurityPermission(SecurityAction.InheritanceDemand, UnmanagedCode = true)]
    [SecurityPermission(SecurityAction.Demand, UnmanagedCode = true)]
    internal class SecurityIdentifierSafePtr : LocalAllocSafePtr
    {
    }

    /// <summary>
    /// Shared memory handle.
    /// </summary>
    [SecurityPermission(SecurityAction.InheritanceDemand, UnmanagedCode = true)]
    [SecurityPermission(SecurityAction.Demand, UnmanagedCode = true)]
    internal class SharedMemorySafeHandle : SafeHandleZeroOrMinusOneIsInvalid
    {
        /// <summary>
        /// Initializes a new instance of the <see cref="SharedMemorySafeHandle"/> class.
        /// </summary>
        internal SharedMemorySafeHandle()
            : base(true)
        {
        }

        /// <inheritdoc/>
        protected override bool ReleaseHandle()
        {
            return Native.CloseHandle(handle);
        }
    }

    /// <summary>
    /// Memory mapping handle.
    /// </summary>
    [SecurityPermission(SecurityAction.InheritanceDemand, UnmanagedCode = true)]
    [SecurityPermission(SecurityAction.Demand, UnmanagedCode = true)]
    internal class MemoryMappingSafeHandle : SafeHandleZeroOrMinusOneIsInvalid
    {
        /// <summary>
        /// Initializes a new instance of the <see cref="MemoryMappingSafeHandle"/> class.
        /// </summary>
        public MemoryMappingSafeHandle()
            : base(true)
        {
        }

        /// <inheritdoc/>
        protected override bool ReleaseHandle()
        {
            return Native.UnmapViewOfFile(handle);
        }
    }

    /// <summary>
    /// Event handle.
    /// </summary>
    [SecurityPermission(SecurityAction.InheritanceDemand, UnmanagedCode = true)]
    [SecurityPermission(SecurityAction.Demand, UnmanagedCode = true)]
    internal class EventSafeHandle : SafeHandleZeroOrMinusOneIsInvalid
    {
        /// <summary>
        /// Initializes a new instance of the <see cref="EventSafeHandle"/> class.
        /// </summary>
        internal EventSafeHandle()
            : base(true)
        {
        }

        /// <inheritdoc/>
        protected override bool ReleaseHandle()
        {
            return Native.CloseHandle(handle);
        }
    }

    /// <summary>
    /// Access token handle.
    /// </summary>
    [SecurityPermission(SecurityAction.InheritanceDemand, UnmanagedCode = true)]
    [SecurityPermission(SecurityAction.Demand, UnmanagedCode = true)]
    internal class AccessTokenSafeHandle : SafeHandleZeroOrMinusOneIsInvalid
    {
        /// <summary>
        /// Initializes a new instance of the <see cref="AccessTokenSafeHandle"/> class.
        /// </summary>
        internal AccessTokenSafeHandle()
            : base(true)
        {
        }

        /// <inheritdoc/>
        protected override bool ReleaseHandle()
        {
            return Native.CloseHandle(handle);
        }
    }

    /// <summary>
    /// Process token handle.
    /// </summary>
    [SecurityPermission(SecurityAction.InheritanceDemand, UnmanagedCode = true)]
    [SecurityPermission(SecurityAction.Demand, UnmanagedCode = true)]
    internal class ProcessTokenSafeHandle : SafeHandleZeroOrMinusOneIsInvalid
    {
        /// <summary>
        /// Initializes a new instance of the <see cref="ProcessTokenSafeHandle"/> class.
        /// </summary>
        public ProcessTokenSafeHandle()
            : base(true)
        {
        }

        /// <inheritdoc/>
        protected override bool ReleaseHandle()
        {
            return Native.CloseHandle(handle);
        }
    }
}
