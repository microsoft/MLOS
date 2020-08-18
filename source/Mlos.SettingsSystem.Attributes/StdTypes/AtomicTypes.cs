// -----------------------------------------------------------------------
// <copyright file="AtomicTypes.cs" company="Microsoft Corporation">
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
    /// Maps to std::atomic_bool.
    /// </summary>
    public struct AtomicBool : ICodegenType, IEquatable<AtomicBool>
    {
        /// <summary>
        /// Operator ==.
        /// </summary>
        /// <param name="left"></param>
        /// <param name="right"></param>
        /// <returns></returns>
        public static bool operator ==(AtomicBool left, AtomicBool right) => left.Equals(right);

        /// <summary>
        /// Operator !=.
        /// </summary>
        /// <param name="left"></param>
        /// <param name="right"></param>
        /// <returns></returns>
        public static bool operator !=(AtomicBool left, AtomicBool right) => !(left == right);

        /// <inheritdoc />
        public override bool Equals(object obj)
        {
            if (!(obj is AtomicBool))
            {
                return false;
            }

            return Equals((AtomicBool)obj);
        }

        /// <inheritdoc />
        public bool Equals(AtomicBool other) => Value == other.Value;

        /// <inheritdoc />
        public override int GetHashCode() => Value.GetHashCode();

        /// <inheritdoc />
        uint ICodegenKey.CodegenTypeIndex() => throw new NotImplementedException();

        /// <inheritdoc />
        ulong ICodegenKey.CodegenTypeHash() => throw new NotImplementedException();

        /// <inheritdoc />
        ulong ICodegenType.CodegenTypeSize() => sizeof(bool);

        /// <inheritdoc />
        uint ICodegenKey.GetKeyHashValue<THash>() => throw new NotImplementedException();

        /// <inheritdoc />
        bool ICodegenKey.CompareKey(ICodegenProxy proxy) => throw new NotImplementedException();

        /// <inheritdoc />
        ulong ICodegenType.GetVariableDataSize() => 0;

        /// <inheritdoc />
        ulong ICodegenType.SerializeVariableData(IntPtr buffer, ulong objectOffset, ulong dataOffset) => 0;

        /// <inheritdoc />
        void ICodegenType.SerializeFixedPart(IntPtr buffer, ulong objectOffset)
        {
            unsafe
            {
                *(bool*)(buffer + (int)objectOffset) = Value;
            }
        }

        /// <inheritdoc />
        public void Update(ICodegenProxy sourceProxy)
        {
            unsafe
            {
                Value = *(bool*)sourceProxy.Buffer;
            }
        }

        /// <summary>
        /// Value.
        /// </summary>
        public bool Value;
    }

    /// <summary>
    /// Maps to std::atomic_int32_t.
    /// </summary>
    public struct AtomicInt32 : ICodegenType, IEquatable<AtomicInt32>
    {
        /// <summary>
        /// Operator ==.
        /// </summary>
        /// <param name="left"></param>
        /// <param name="right"></param>
        /// <returns></returns>
        public static bool operator ==(AtomicInt32 left, AtomicInt32 right) => left.Equals(right);

        /// <summary>
        /// Operator !=.
        /// </summary>
        /// <param name="left"></param>
        /// <param name="right"></param>
        /// <returns></returns>
        public static bool operator !=(AtomicInt32 left, AtomicInt32 right) => !(left == right);

        /// <inheritdoc />
        public override bool Equals(object obj)
        {
            if (!(obj is AtomicInt32))
            {
                return false;
            }

            return Equals((AtomicInt32)obj);
        }

        /// <inheritdoc />
        public bool Equals(AtomicInt32 other) => Value == other.Value;

        /// <inheritdoc />
        public override int GetHashCode() => Value.GetHashCode();

        /// <inheritdoc />
        uint ICodegenKey.CodegenTypeIndex() => throw new NotImplementedException();

        /// <inheritdoc />
        ulong ICodegenKey.CodegenTypeHash() => throw new NotImplementedException();

        /// <inheritdoc />
        ulong ICodegenType.CodegenTypeSize() => sizeof(int);

        /// <inheritdoc />
        uint ICodegenKey.GetKeyHashValue<THash>() => throw new NotImplementedException();

        /// <inheritdoc />
        bool ICodegenKey.CompareKey(ICodegenProxy proxy) => throw new NotImplementedException();

        /// <inheritdoc />
        ulong ICodegenType.GetVariableDataSize() => 0;

        /// <inheritdoc />
        ulong ICodegenType.SerializeVariableData(IntPtr buffer, ulong objectOffset, ulong dataOffset) => 0;

        /// <inheritdoc />
        void ICodegenType.SerializeFixedPart(IntPtr buffer, ulong objectOffset)
        {
            unsafe
            {
                *(int*)(buffer + (int)objectOffset) = Value;
            }
        }

        /// <inheritdoc />
        public void Update(ICodegenProxy sourceProxy)
        {
            unsafe
            {
                Value = *(int*)sourceProxy.Buffer;
            }
        }

        /// <summary>
        /// Value.
        /// </summary>
        public int Value;
    }

    /// <summary>
    /// Maps to std::atomic_uint32_t.
    /// </summary>
    public struct AtomicUInt32 : ICodegenType, IEquatable<AtomicUInt32>
    {
        /// <summary>
        /// Operator ==.
        /// </summary>
        /// <param name="left"></param>
        /// <param name="right"></param>
        /// <returns></returns>
        public static bool operator ==(AtomicUInt32 left, AtomicUInt32 right) => left.Equals(right);

        /// <summary>
        /// Operator !=.
        /// </summary>
        /// <param name="left"></param>
        /// <param name="right"></param>
        /// <returns></returns>
        public static bool operator !=(AtomicUInt32 left, AtomicUInt32 right) => !(left == right);

        /// <inheritdoc />
        public override bool Equals(object obj)
        {
            if (!(obj is AtomicUInt32))
            {
                return false;
            }

            return Equals((AtomicUInt32)obj);
        }

        /// <inheritdoc />
        public bool Equals(AtomicUInt32 other) => Value == other.Value;

        /// <inheritdoc />
        public override int GetHashCode() => Value.GetHashCode();

        /// <inheritdoc />
        uint ICodegenKey.CodegenTypeIndex() => throw new NotImplementedException();

        /// <inheritdoc />
        ulong ICodegenKey.CodegenTypeHash() => throw new NotImplementedException();

        /// <inheritdoc />
        ulong ICodegenType.CodegenTypeSize() => sizeof(uint);

        /// <inheritdoc />
        uint ICodegenKey.GetKeyHashValue<THash>() => throw new NotImplementedException();

        /// <inheritdoc />
        bool ICodegenKey.CompareKey(ICodegenProxy proxy) => throw new NotImplementedException();

        /// <inheritdoc />
        ulong ICodegenType.GetVariableDataSize() => 0;

        /// <inheritdoc />
        ulong ICodegenType.SerializeVariableData(IntPtr buffer, ulong objectOffset, ulong dataOffset) => 0;

        /// <inheritdoc />
        void ICodegenType.SerializeFixedPart(IntPtr buffer, ulong objectOffset)
        {
            unsafe
            {
                *(uint*)(buffer + (int)objectOffset) = Value;
            }
        }

        /// <inheritdoc />
        public void Update(ICodegenProxy sourceProxy)
        {
            unsafe
            {
                Value = *(uint*)sourceProxy.Buffer;
            }
        }

        /// <summary>
        /// Value.
        /// </summary>
        public uint Value;
    }

    /// <summary>
    /// Maps to std::atomic_int64_t.
    /// </summary>
    public struct AtomicInt64 : ICodegenType, IEquatable<AtomicInt64>
    {
        /// <summary>
        /// Operator ==.
        /// </summary>
        /// <param name="left"></param>
        /// <param name="right"></param>
        /// <returns></returns>
        public static bool operator ==(AtomicInt64 left, AtomicInt64 right) => left.Equals(right);

        /// <summary>
        /// Operator !=.
        /// </summary>
        /// <param name="left"></param>
        /// <param name="right"></param>
        /// <returns></returns>
        public static bool operator !=(AtomicInt64 left, AtomicInt64 right) => !(left == right);

        /// <inheritdoc />
        public override bool Equals(object obj)
        {
            if (!(obj is AtomicInt64))
            {
                return false;
            }

            return Equals((AtomicInt64)obj);
        }

        /// <inheritdoc />
        public bool Equals(AtomicInt64 other) => Value == other.Value;

        /// <inheritdoc />
        public override int GetHashCode() => Value.GetHashCode();

        /// <inheritdoc />
        uint ICodegenKey.CodegenTypeIndex() => throw new NotImplementedException();

        /// <inheritdoc />
        ulong ICodegenKey.CodegenTypeHash() => throw new NotImplementedException();

        /// <inheritdoc />
        ulong ICodegenType.CodegenTypeSize() => sizeof(ulong);

        /// <inheritdoc />
        uint ICodegenKey.GetKeyHashValue<THash>() => throw new NotImplementedException();

        /// <inheritdoc />
        bool ICodegenKey.CompareKey(ICodegenProxy proxy) => throw new NotImplementedException();

        /// <inheritdoc />
        ulong ICodegenType.GetVariableDataSize() => 0;

        /// <inheritdoc />
        ulong ICodegenType.SerializeVariableData(IntPtr buffer, ulong objectOffset, ulong dataOffset) => 0;

        /// <inheritdoc />
        void ICodegenType.SerializeFixedPart(IntPtr buffer, ulong objectOffset)
        {
            unsafe
            {
                *(long*)(buffer + (int)objectOffset) = Value;
            }
        }

        /// <inheritdoc />
        public void Update(ICodegenProxy sourceProxy)
        {
            unsafe
            {
                Value = *(long*)sourceProxy.Buffer;
            }
        }

        /// <summary>
        /// Value.
        /// </summary>
        public long Value;
    }

    /// <summary>
    /// Maps to std::atomic_uint64_t.
    /// </summary>
    public struct AtomicUInt64 : ICodegenType, IEquatable<AtomicUInt64>
    {
        /// <summary>
        /// Operator ==.
        /// </summary>
        /// <param name="left"></param>
        /// <param name="right"></param>
        /// <returns></returns>
        public static bool operator ==(AtomicUInt64 left, AtomicUInt64 right) => left.Equals(right);

        /// <summary>
        /// Operator !=.
        /// </summary>
        /// <param name="left"></param>
        /// <param name="right"></param>
        /// <returns></returns>
        public static bool operator !=(AtomicUInt64 left, AtomicUInt64 right) => !(left == right);

        /// <inheritdoc />
        public override bool Equals(object obj)
        {
            if (!(obj is AtomicUInt64))
            {
                return false;
            }

            return Equals((AtomicUInt64)obj);
        }

        /// <inheritdoc />
        public bool Equals(AtomicUInt64 other) => Value == other.Value;

        /// <inheritdoc />
        public override int GetHashCode() => Value.GetHashCode();

        /// <inheritdoc />
        uint ICodegenKey.CodegenTypeIndex() => throw new NotImplementedException();

        /// <inheritdoc />
        ulong ICodegenKey.CodegenTypeHash() => throw new NotImplementedException();

        /// <inheritdoc />
        ulong ICodegenType.CodegenTypeSize() => sizeof(ulong);

        /// <inheritdoc />
        uint ICodegenKey.GetKeyHashValue<THash>() => throw new NotImplementedException();

        /// <inheritdoc />
        bool ICodegenKey.CompareKey(ICodegenProxy proxy) => throw new NotImplementedException();

        /// <inheritdoc />
        ulong ICodegenType.GetVariableDataSize() => 0;

        /// <inheritdoc />
        ulong ICodegenType.SerializeVariableData(IntPtr buffer, ulong objectOffset, ulong dataOffset) => 0;

        /// <inheritdoc />
        void ICodegenType.SerializeFixedPart(IntPtr buffer, ulong objectOffset)
        {
            unsafe
            {
                *(ulong*)(buffer + (int)objectOffset) = Value;
            }
        }

        /// <inheritdoc />
        public void Update(ICodegenProxy sourceProxy)
        {
            unsafe
            {
                Value = *(ulong*)sourceProxy.Buffer;
            }
        }

        /// <summary>
        /// Value.
        /// </summary>
        public ulong Value;
    }
}
