// -----------------------------------------------------------------------
// <copyright file="StringTypes.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;

using Mlos.Core;

namespace Mlos.SettingsSystem.StdTypes
{
    /// <summary>
    /// Maps to char pointer.
    /// </summary>
    public struct StringPtr : ICodegenType, IEquatable<StringPtr>
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
        public bool Equals(StringPtr other) => Value == other.Value;

        /// <inheritdoc />
        public override int GetHashCode() => Value.GetHashCode();

        /// <summary>
        /// Gets or sets string value.
        /// </summary>
        public string Value { get; set; }

        /// <inheritdoc />
        ulong ICodegenKey.CodegenTypeHash() => throw new System.NotImplementedException();

        /// <inheritdoc />
        uint ICodegenKey.CodegenTypeIndex() => throw new System.NotImplementedException();

        /// <inheritdoc />
        ulong ICodegenType.CodegenTypeSize() => 16;

        /// <inheritdoc />
        uint ICodegenKey.GetKeyHashValue<THash>() => throw new NotImplementedException();

        /// <inheritdoc />
        bool ICodegenKey.CompareKey(ICodegenProxy proxy) => throw new NotImplementedException();

        /// <inheritdoc />
        ulong ICodegenType.GetVariableDataSize() => Value != null ? (ulong)Value.Length : 0;

        /// <inheritdoc />
        ulong ICodegenType.SerializeVariableData(IntPtr buffer, ulong objectOffset, ulong dataOffset)
        {
            unsafe
            {
                ReadOnlySpan<char> valueSpan = Value.AsSpan();
                int length = valueSpan.Length;

                Span<byte> messageSpan = new Span<byte>((buffer + (int)dataOffset).ToPointer(), length);

                // Copy the string data.
                //
                for (int i = 0; i < length; i++)
                {
                    messageSpan[i] = (byte)valueSpan[i];
                }

                // Update links.
                //
                *(ulong*)(buffer + (int)objectOffset) = dataOffset - objectOffset;
                *(ulong*)(buffer + (int)objectOffset + sizeof(ulong)) = (ulong)length;

                return (ulong)length;
            }
        }

        /// <inheritdoc />
        public void SerializeFixedPart(IntPtr buffer, ulong objectOffset)
        {
            // Nothing.
            //
        }

        /// <inheritdoc />
        public void Update(ICodegenProxy proxy) => throw new NotImplementedException();
    }

    /// <summary>
    /// Maps to wchar pointer.
    /// </summary>
    public struct WideStringPtr : ICodegenType, IEquatable<WideStringPtr>
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
        public bool Equals(WideStringPtr other) => Value == other.Value;

        /// <inheritdoc />
        public override int GetHashCode() => Value.GetHashCode(StringComparison.InvariantCulture);

        /// <summary>
        /// Gets or sets string value.
        /// </summary>
        public string Value { get; set; }

        /// <inheritdoc />
        ulong ICodegenKey.CodegenTypeHash() => throw new System.NotImplementedException();

        /// <inheritdoc />
        uint ICodegenKey.CodegenTypeIndex() => throw new System.NotImplementedException();

        /// <inheritdoc />
        ulong ICodegenType.CodegenTypeSize() => 16;

        /// <inheritdoc />
        uint ICodegenKey.GetKeyHashValue<THash>() => throw new NotImplementedException();

        /// <inheritdoc />
        bool ICodegenKey.CompareKey(ICodegenProxy proxy) => throw new NotImplementedException();

        /// <inheritdoc />
        ulong ICodegenType.GetVariableDataSize() => Value != null ? (ulong)(Value.Length * 2) : 0;

        /// <inheritdoc />
        ulong ICodegenType.SerializeVariableData(IntPtr buffer, ulong objectOffset, ulong dataOffset)
        {
            unsafe
            {
                ReadOnlySpan<char> valueSpan = Value.AsSpan();
                Span<char> messageSpan = new Span<char>((buffer + (int)dataOffset).ToPointer(), valueSpan.Length);

                // Copy the string data.
                //
                valueSpan.CopyTo(messageSpan);

                // Update links.
                //
                ulong length = (ulong)valueSpan.Length * 2;
                *(ulong*)(buffer + (int)objectOffset) = dataOffset - objectOffset;
                *(ulong*)(buffer + (int)objectOffset + sizeof(ulong)) = length;

                return length;
            }
        }

        /// <inheritdoc />
        public void SerializeFixedPart(IntPtr buffer, ulong objectOffset)
        {
            // Nothing.
            //
        }

        /// <inheritdoc />
        public void Update(ICodegenProxy proxy) => throw new NotImplementedException();
    }

    /// <summary>
    /// Maps to std::string_view.
    /// </summary>
    public struct StringView : ICodegenType, IEquatable<StringView>
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
        public bool Equals(StringView other) => Value == other.Value;

        /// <inheritdoc />
        public override int GetHashCode() => Value.GetHashCode(StringComparison.InvariantCulture);

        /// <summary>
        /// Gets or sets string value.
        /// </summary>
        public string Value { get; set; }

        /// <inheritdoc />
        ulong ICodegenKey.CodegenTypeHash() => throw new NotImplementedException();

        /// <inheritdoc />
        uint ICodegenKey.CodegenTypeIndex() => throw new NotImplementedException();

        /// <inheritdoc />
        ulong ICodegenType.CodegenTypeSize() => 16;

        /// <inheritdoc />
        uint ICodegenKey.GetKeyHashValue<THash>() => throw new NotImplementedException();

        /// <inheritdoc />
        bool ICodegenKey.CompareKey(ICodegenProxy proxy) => throw new NotImplementedException();

        /// <inheritdoc />
        ulong ICodegenType.GetVariableDataSize() => Value != null ? (ulong)Value.Length : 0;

        /// <inheritdoc />
        ulong ICodegenType.SerializeVariableData(IntPtr buffer, ulong objectOffset, ulong dataOffset)
        {
            unsafe
            {
                ReadOnlySpan<char> valueSpan = Value.AsSpan();
                int length = valueSpan.Length;

                Span<byte> messageSpan = new Span<byte>((buffer + (int)dataOffset).ToPointer(), length);

                // Copy the string data.
                //
                for (int i = 0; i < length; i++)
                {
                    messageSpan[i] = (byte)valueSpan[i];
                }

                // Update links.
                //
                *(ulong*)(buffer + (int)objectOffset) = dataOffset - objectOffset;
                *(ulong*)(buffer + (int)objectOffset + sizeof(ulong)) = (ulong)length;

                return (ulong)length;
            }
        }

        /// <inheritdoc />
        public void SerializeFixedPart(IntPtr buffer, ulong objectOffset)
        {
            // Nothing.
            //
        }

        /// <inheritdoc />
        public void Update(ICodegenProxy proxy) => throw new NotImplementedException();
    }

    /// <summary>
    /// Maps to std::wstring_view.
    /// </summary>
    public struct WideStringView : ICodegenType, IEquatable<WideStringView>
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
        public bool Equals(WideStringView other) => Value == other.Value;

        /// <inheritdoc />
        public override int GetHashCode() => Value.GetHashCode(StringComparison.InvariantCulture);

        /// <summary>
        /// Gets or sets string value.
        /// </summary>
        public string Value { get; set; }

        /// <inheritdoc/>
        ulong ICodegenKey.CodegenTypeHash() => throw new NotImplementedException();

        /// <inheritdoc/>
        uint ICodegenKey.CodegenTypeIndex() => throw new NotImplementedException();

        /// <inheritdoc/>
        ulong ICodegenType.CodegenTypeSize() => 16;

        /// <inheritdoc />
        uint ICodegenKey.GetKeyHashValue<THash>() => throw new NotImplementedException();

        /// <inheritdoc />
        bool ICodegenKey.CompareKey(ICodegenProxy proxy) => throw new NotImplementedException();

        /// <inheritdoc/>
        ulong ICodegenType.GetVariableDataSize() => Value != null ? (ulong)(Value.Length * 2) : 0;

        /// <inheritdoc/>
        ulong ICodegenType.SerializeVariableData(IntPtr buffer, ulong objectOffset, ulong dataOffset)
        {
            unsafe
            {
                ReadOnlySpan<char> valueSpan = Value.AsSpan();
                Span<char> messageSpan = new Span<char>((buffer + (int)dataOffset).ToPointer(), valueSpan.Length);

                // Copy the string data.
                //
                valueSpan.CopyTo(messageSpan);

                // Update links.
                //
                ulong length = (ulong)valueSpan.Length * 2;
                *(ulong*)(buffer + (int)objectOffset) = dataOffset - objectOffset;
                *(ulong*)(buffer + (int)objectOffset + sizeof(ulong)) = length;

                return length;
            }
        }

        /// <inheritdoc/>
        public void SerializeFixedPart(IntPtr buffer, ulong objectOffset)
        {
            // Nothing.
            //
        }

        /// <inheritdoc/>
        public void Update(ICodegenProxy proxy) => throw new NotImplementedException();
    }
}
