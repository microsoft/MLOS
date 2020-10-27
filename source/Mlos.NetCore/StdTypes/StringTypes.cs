// -----------------------------------------------------------------------
// <copyright file="StringTypes.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Runtime.CompilerServices;

using Mlos.Core;
using Mlos.Core.Collections;

namespace Proxy.Mlos.SettingsSystem.StdTypes
{
    /// <summary>
    /// Maps to StringPtr.
    /// </summary>
    public struct StringPtr : IEquatable<StringPtr>, ICodegenProxy
    {
        /// <summary>
        /// Operator ==.
        /// </summary>
        /// <param name="left"></param>
        /// <param name="right"></param>
        /// <returns></returns>
        public static bool operator ==(StringPtr left, StringPtr right) => left.Equals(right);

        /// <summary>
        /// Operator !=.
        /// </summary>
        /// <param name="left"></param>
        /// <param name="right"></param>
        /// <returns></returns>
        public static bool operator !=(StringPtr left, StringPtr right) => !(left == right);

        public string Value
        {
            get
            {
                unsafe
                {
                    ulong offset = *(ulong*)Buffer;
                    ulong dataSize = *(ulong*)(Buffer + sizeof(ulong));

                    if (dataSize == 0)
                    {
                        return null;
                    }

                    sbyte* dataPtr = (sbyte*)(Buffer + (int)offset);

                    return new string(dataPtr, startIndex: 0, length: (int)dataSize / sizeof(sbyte));
                }
            }
        }

        /// <inheritdoc />
        public override bool Equals(object obj)
        {
            if (!(obj is StringPtr))
            {
                return false;
            }

            return Equals((StringPtr)obj);
        }

        /// <inheritdoc />
        public bool Equals(StringPtr other) => Buffer == other.Buffer;

        /// <inheritdoc />
        public override int GetHashCode() => Buffer.GetHashCode();

        /// <inheritdoc />
        uint ICodegenKey.CodegenTypeIndex() => throw new NotImplementedException();

        /// <inheritdoc />
        ulong ICodegenKey.CodegenTypeHash() => throw new NotImplementedException();

        /// <inheritdoc />
        public ulong CodegenTypeSize() => 16;

        /// <inheritdoc />
        public uint GetKeyHashValue<THash>()
            where THash : IHash<uint> => default(THash).GetHashValue(Buffer);

        /// <inheritdoc />
        public bool CompareKey(ICodegenProxy proxy) => this == (StringPtr)proxy;

        /// <inheritdoc/>
        bool ICodegenProxy.VerifyVariableData(ulong objectOffset, ulong totalDataSize, ref ulong expectedDataOffset)
        {
            unsafe
            {
                ulong dataSize = *(ulong*)(Buffer + sizeof(ulong));

                if (dataSize > totalDataSize)
                {
                    return false;
                }

                ulong offset = *(ulong*)Buffer;
                offset += objectOffset;

                if (expectedDataOffset != offset)
                {
                    return false;
                }

                expectedDataOffset += dataSize;
                return true;
            }
        }

        /// <inheritdoc />
        public IntPtr Buffer { get; set; }
    }

    /// <summary>
    /// Maps to WideStringPtr.
    /// </summary>
    public struct WideStringPtr : IEquatable<WideStringPtr>, ICodegenProxy
    {
        /// <summary>
        /// Operator ==.
        /// </summary>
        /// <param name="left"></param>
        /// <param name="right"></param>
        /// <returns></returns>
        public static bool operator ==(WideStringPtr left, WideStringPtr right) => left.Equals(right);

        /// <summary>
        /// Operator !=.
        /// </summary>
        /// <param name="left"></param>
        /// <param name="right"></param>
        /// <returns></returns>
        public static bool operator !=(WideStringPtr left, WideStringPtr right) => !(left == right);

        public string Value
        {
            get
            {
                unsafe
                {
                    ulong offset = *(ulong*)Buffer;
                    ulong dataSize = *(ulong*)(Buffer + sizeof(ulong));

                    if (dataSize == 0)
                    {
                        return null;
                    }

                    char* dataPtr = (char*)(Buffer + (int)offset);

                    return new string(dataPtr, startIndex: 0, length: (int)dataSize / sizeof(char));
                }
            }
        }

        /// <inheritdoc />
        public override bool Equals(object obj)
        {
            if (!(obj is WideStringPtr))
            {
                return false;
            }

            return Equals((WideStringPtr)obj);
        }

        /// <inheritdoc />
        public bool Equals(WideStringPtr other) => Buffer == other.Buffer;

        /// <inheritdoc />
        public override int GetHashCode() => Buffer.GetHashCode();

        /// <inheritdoc />
        uint ICodegenKey.CodegenTypeIndex() => throw new NotImplementedException();

        /// <inheritdoc />
        ulong ICodegenKey.CodegenTypeHash() => throw new NotImplementedException();

        /// <inheritdoc />
        public ulong CodegenTypeSize() => 16;

        /// <inheritdoc />
        public uint GetKeyHashValue<THash>()
            where THash : IHash<uint> => default(THash).GetHashValue(Buffer);

        /// <inheritdoc />
        public bool CompareKey(ICodegenProxy proxy) => this == (WideStringPtr)proxy;

        /// <inheritdoc/>
        bool ICodegenProxy.VerifyVariableData(ulong objectOffset, ulong totalDataSize, ref ulong expectedDataOffset)
        {
            unsafe
            {
                ulong dataSize = *(ulong*)(Buffer + sizeof(ulong));

                if (dataSize > totalDataSize)
                {
                    return false;
                }

                ulong offset = *(ulong*)Buffer;
                offset += objectOffset;

                if (expectedDataOffset != offset)
                {
                    return false;
                }

                expectedDataOffset += dataSize;
                return true;
            }
        }

        /// <inheritdoc />
        public IntPtr Buffer { get; set; }
    }

    /// <summary>
    /// Maps to std::string_view.
    /// </summary>
    public struct StringView : IEquatable<StringView>, ICodegenProxy
    {
        /// <summary>
        /// Operator ==.
        /// </summary>
        /// <param name="left"></param>
        /// <param name="right"></param>
        /// <returns></returns>
        public static bool operator ==(StringView left, StringView right) => left.Equals(right);

        /// <summary>
        /// Operator !=.
        /// </summary>
        /// <param name="left"></param>
        /// <param name="right"></param>
        /// <returns></returns>
        public static bool operator !=(StringView left, StringView right) => !(left == right);

        public string Value
        {
            get
            {
                unsafe
                {
                    ulong offset = *(ulong*)Buffer;
                    ulong dataSize = *(ulong*)(Buffer + sizeof(ulong));

                    if (dataSize == 0)
                    {
                        return null;
                    }

                    sbyte* dataPtr = (sbyte*)(Buffer + (int)offset);

                    return new string(dataPtr, startIndex: 0, length: (int)dataSize / sizeof(sbyte));
                }
            }
        }

        /// <inheritdoc />
        public override bool Equals(object obj)
        {
            if (!(obj is StringView))
            {
                return false;
            }

            return Equals((StringView)obj);
        }

        /// <inheritdoc />
        public bool Equals(StringView other) => Buffer == other.Buffer;

        /// <inheritdoc />
        public override int GetHashCode() => Buffer.GetHashCode();

        /// <inheritdoc />
        uint ICodegenKey.CodegenTypeIndex() => throw new NotImplementedException();

        /// <inheritdoc />
        ulong ICodegenKey.CodegenTypeHash() => throw new NotImplementedException();

        /// <inheritdoc />
        public ulong CodegenTypeSize() => 16;

        /// <inheritdoc />
        public uint GetKeyHashValue<THash>()
            where THash : IHash<uint> => default(THash).GetHashValue(Buffer);

        /// <inheritdoc />
        public bool CompareKey(ICodegenProxy proxy) => this == (StringView)proxy;

        /// <inheritdoc/>
        bool ICodegenProxy.VerifyVariableData(ulong objectOffset, ulong totalDataSize, ref ulong expectedDataOffset)
        {
            unsafe
            {
                ulong dataSize = *(ulong*)(Buffer + sizeof(ulong));

                if (dataSize > totalDataSize)
                {
                    return false;
                }

                ulong offset = *(ulong*)Buffer;
                offset += objectOffset;

                if (expectedDataOffset != offset)
                {
                    return false;
                }

                expectedDataOffset += dataSize;
                return true;
            }
        }

        /// <inheritdoc />
        public IntPtr Buffer { get; set; }
    }

    /// <summary>
    /// Maps to std::wstring_view.
    /// </summary>
    public struct WideStringView : IEquatable<WideStringView>, ICodegenProxy
    {
        /// <summary>
        /// Operator ==.
        /// </summary>
        /// <param name="left"></param>
        /// <param name="right"></param>
        /// <returns></returns>
        public static bool operator ==(WideStringView left, WideStringView right) => left.Equals(right);

        /// <summary>
        /// Operator !=.
        /// </summary>
        /// <param name="left"></param>
        /// <param name="right"></param>
        /// <returns></returns>
        public static bool operator !=(WideStringView left, WideStringView right) => !(left == right);

        public string Value
        {
            get
            {
                unsafe
                {
                    ulong offset = *(ulong*)Buffer;
                    ulong dataSize = *(ulong*)(Buffer + sizeof(ulong));

                    if (dataSize == 0)
                    {
                        return null;
                    }

                    char* dataPtr = (char*)(Buffer + (int)offset);

                    return new string(dataPtr, startIndex: 0, length: (int)dataSize / sizeof(char));
                }
            }
        }

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public ReadOnlySpan<char> ValueAsSpan()
        {
            unsafe
            {
                ulong offset = *(ulong*)Buffer;
                ulong size = *(ulong*)(Buffer + sizeof(ulong));

                char* dataPtr = (char*)(Buffer + (int)offset);

                ReadOnlySpan<char> valueSpan = new ReadOnlySpan<char>(dataPtr, length: (int)size / sizeof(char));
                return valueSpan;
            }
        }

        /// <inheritdoc />
        public override bool Equals(object obj)
        {
            if (!(obj is WideStringView))
            {
                return false;
            }

            return Equals((WideStringView)obj);
        }

        /// <inheritdoc />
        public bool Equals(WideStringView other) => Buffer == other.Buffer;

        /// <inheritdoc />
        public override int GetHashCode() => Buffer.GetHashCode();

        /// <inheritdoc />
        uint ICodegenKey.CodegenTypeIndex() => throw new NotImplementedException();

        /// <inheritdoc />
        ulong ICodegenKey.CodegenTypeHash() => throw new NotImplementedException();

        /// <inheritdoc />
        public ulong CodegenTypeSize() => 16;

        /// <inheritdoc />
        public uint GetKeyHashValue<THash>()
            where THash : IHash<uint> => default(THash).GetHashValue(Buffer);

        /// <inheritdoc />
        public bool CompareKey(ICodegenProxy proxy) => this == (WideStringView)proxy;

        /// <inheritdoc/>
        bool ICodegenProxy.VerifyVariableData(ulong objectOffset, ulong totalDataSize, ref ulong expectedDataOffset)
        {
            unsafe
            {
                ulong dataSize = *(ulong*)(Buffer + sizeof(ulong));

                if (dataSize > totalDataSize)
                {
                    return false;
                }

                ulong offset = *(ulong*)Buffer;
                offset += objectOffset;

                if (expectedDataOffset != offset)
                {
                    return false;
                }

                expectedDataOffset += dataSize;
                return true;
            }
        }

        /// <inheritdoc />
        public IntPtr Buffer { get; set; }
    }
}
