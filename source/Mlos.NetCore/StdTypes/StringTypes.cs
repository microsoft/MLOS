// -----------------------------------------------------------------------
// <copyright file="StringTypes.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Globalization;
using System.Runtime.CompilerServices;

using Mlos.Core;
using Mlos.Core.Collections;

using MlosStdTypes = global::Mlos.SettingsSystem.StdTypes;

namespace Proxy.Mlos.SettingsSystem.StdTypes
{
    /// <summary>
    /// Codegen proxy for StringPtr.
    /// </summary>
    public struct StringPtr : ICodegenProxy<MlosStdTypes.StringPtr, StringPtr>, IEquatable<StringPtr>, IEquatable<MlosStdTypes.StringPtr>
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

        /// <summary>
        /// Operator ==.
        /// </summary>
        /// <param name="left"></param>
        /// <param name="right"></param>
        /// <returns></returns>
        public static bool operator ==(StringPtr left, MlosStdTypes.StringPtr right) => left.Equals(right);

        /// <summary>
        /// Operator !=.
        /// </summary>
        /// <param name="left"></param>
        /// <param name="right"></param>
        /// <returns></returns>
        public static bool operator !=(StringPtr left, MlosStdTypes.StringPtr right) => !(left == right);

        /// <summary>
        /// Gets value stored in the buffer as a string.
        /// </summary>
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

                    return new string(dataPtr, startIndex: 0, length: ((int)dataSize / sizeof(sbyte)) - 1);
                }
            }
        }

        /// <inheritdoc />
        public override bool Equals(object obj)
        {
            if (obj is StringPtr stringPtr)
            {
                return Equals(stringPtr);
            }
            else if (obj is MlosStdTypes.StringPtr stdStringPtr)
            {
                return Equals(stdStringPtr);
            }

            return false;
        }

        /// <inheritdoc />
        public bool Equals(StringPtr other) => Buffer == other.Buffer;

        /// <inheritdoc />
        public bool Equals(MlosStdTypes.StringPtr other) => string.Compare(Value, other.Value, ignoreCase: false, culture: CultureInfo.InvariantCulture) == 0;

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
    /// Codegen proxy for WideStringPtr.
    /// </summary>
    public struct WideStringPtr : ICodegenProxy<MlosStdTypes.WideStringPtr, WideStringPtr>, IEquatable<WideStringPtr>, IEquatable<MlosStdTypes.WideStringPtr>
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

        /// <summary>
        /// Operator ==.
        /// </summary>
        /// <param name="left"></param>
        /// <param name="right"></param>
        /// <returns></returns>
        public static bool operator ==(WideStringPtr left, MlosStdTypes.WideStringPtr right) => left.Equals(right);

        /// <summary>
        /// Operator !=.
        /// </summary>
        /// <param name="left"></param>
        /// <param name="right"></param>
        /// <returns></returns>
        public static bool operator !=(WideStringPtr left, MlosStdTypes.WideStringPtr right) => !(left == right);

        /// <summary>
        /// Gets a string stored in the buffer.
        /// </summary>
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

                    return new string(dataPtr, startIndex: 0, length: ((int)dataSize / sizeof(char)) - 1);
                }
            }
        }

        /// <inheritdoc />
        public override bool Equals(object obj)
        {
            if (obj is WideStringPtr wideStringPtr)
            {
                return Equals(wideStringPtr);
            }
            else if (obj is MlosStdTypes.WideStringPtr stdWideStringPtr)
            {
                return Equals(stdWideStringPtr);
            }

            return false;
        }

        /// <inheritdoc />
        public bool Equals(WideStringPtr other) => Buffer == other.Buffer;

        /// <inheritdoc />
        public bool Equals(MlosStdTypes.WideStringPtr other) => string.Compare(Value, other.Value, ignoreCase: false, culture: CultureInfo.InvariantCulture) == 0;

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
    /// Codegen proxy for std::string_view.
    /// </summary>
    public struct StringView : ICodegenProxy<MlosStdTypes.StringView, StringView>, IEquatable<StringView>, IEquatable<MlosStdTypes.StringView>
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

        /// <summary>
        /// Operator ==.
        /// </summary>
        /// <param name="left"></param>
        /// <param name="right"></param>
        /// <returns></returns>
        public static bool operator ==(StringView left, MlosStdTypes.StringView right) => left.Equals(right);

        /// <summary>
        /// Operator !=.
        /// </summary>
        /// <param name="left"></param>
        /// <param name="right"></param>
        /// <returns></returns>
        public static bool operator !=(StringView left, MlosStdTypes.StringView right) => !(left == right);

        /// <summary>
        /// Gets a string stored in the buffer.
        /// </summary>
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
            if (obj is StringView stringView)
            {
                return Equals(stringView);
            }
            else if (obj is MlosStdTypes.StringView stdStringView)
            {
                return Equals(stdStringView);
            }

            return false;
        }

        /// <inheritdoc />
        public bool Equals(StringView other) => Buffer == other.Buffer;

        /// <inheritdoc />
        public bool Equals(MlosStdTypes.StringView other) => string.Compare(Value, other.Value, ignoreCase: false, culture: CultureInfo.InvariantCulture) == 0;

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
    /// Codegen proxy for std::wstring_view.
    /// </summary>
    public struct WideStringView : ICodegenProxy<MlosStdTypes.WideStringView, WideStringView>, IEquatable<WideStringView>, IEquatable<MlosStdTypes.WideStringView>
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

        /// <summary>
        /// Operator ==.
        /// </summary>
        /// <param name="left"></param>
        /// <param name="right"></param>
        /// <returns></returns>
        public static bool operator ==(WideStringView left, MlosStdTypes.WideStringView right) => left.Equals(right);

        /// <summary>
        /// Operator !=.
        /// </summary>
        /// <param name="left"></param>
        /// <param name="right"></param>
        /// <returns></returns>
        public static bool operator !=(WideStringView left, MlosStdTypes.WideStringView right) => !(left == right);

        /// <summary>
        /// Gets a string stored in the buffer.
        /// </summary>
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

        /// <summary>
        /// Gets a string stored in the buffer as read only span.
        /// </summary>
        /// <returns></returns>
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
            if (obj is WideStringView wideStringView)
            {
                return Equals(wideStringView);
            }
            else if (obj is MlosStdTypes.WideStringView stdWideStringView)
            {
                return Equals(stdWideStringView);
            }

            return false;
        }

        /// <inheritdoc />
        public bool Equals(WideStringView other) => Buffer == other.Buffer;

        /// <inheritdoc />
        public bool Equals(MlosStdTypes.WideStringView other) => string.Compare(Value, other.Value, ignoreCase: false, culture: CultureInfo.InvariantCulture) == 0;

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
