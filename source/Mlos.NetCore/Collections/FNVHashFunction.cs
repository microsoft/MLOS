// -----------------------------------------------------------------------
// <copyright file="FNVHashFunction.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;

namespace Mlos.Core.Collections
{
#pragma warning disable CA1000 // Do not declare static members on generic types
#pragma warning disable CA1066 // Type {0} should implement IEquatable<T> because it overrides Equals
#pragma warning disable CA1716 // Identifiers should not match keywords
#pragma warning disable CA1815 // Override equals and operator equals on value types
#pragma warning disable CA2231 // Overload operator equals on overriding value type Equals
#pragma warning disable CS0659 // Type overrides Object.Equals(object o) but does not override Object.GetHashCode()

    #region FNV hash implementation

    /// <summary>
    /// Fowler-Noll-Vo hash function implementation.
    /// </summary>
    /// <typeparam name="THashValue">Type of the hash value.</typeparam>
    /// <typeparam name="THashValueOperators">Interface to the hash value operators.</typeparam>
    internal struct FNVHashFunction<THashValue, THashValueOperators>
        where THashValue : unmanaged
        where THashValueOperators : IHashValueOperators<THashValue>
    {
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static THashValue GetHashValue(ReadOnlySpan<byte> span)
        {
            THashValueOperators conv = default;

            THashValue fnvOffsetBasis;

            if (typeof(THashValue) == typeof(uint))
            {
                fnvOffsetBasis = conv.Convert(0x811c9dc5);
                return CombineHashValue(fnvOffsetBasis, span);
            }
            else if (typeof(THashValue) == typeof(ulong))
            {
                fnvOffsetBasis = conv.Convert(0xcbf29ce484222325);
                return CombineHashValue(fnvOffsetBasis, span);
            }
            else
            {
                throw new NotImplementedException();
            }
        }

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static THashValue CombineHashValue(THashValue hashValue, ReadOnlySpan<byte> span)
        {
            THashValueOperators conv = default;

            THashValue fnvPrime;

            if (typeof(THashValueOperators) == typeof(UIntHashValueOperators))
            {
                fnvPrime = conv.Convert(0x01000193);
            }
            else if (typeof(THashValueOperators) == typeof(ULongHashValueOperators))
            {
                fnvPrime = conv.Convert(0x00000100000001B3ul);
            }
            else
            {
                throw new NotImplementedException();
            }

            for (int i = 0; i < span.Length; i++)
            {
                hashValue = conv.Xor(conv.Convert(span[i]), hashValue);
                hashValue = conv.Mul(hashValue, fnvPrime);
            }

            return hashValue;
        }
    }
    #endregion

    #region Public implementation

    public struct FNVHash<THashValue> : IHash<THashValue>
        where THashValue : unmanaged
    {
        /// <summary>
        /// Explicit implementation for comparision.
        /// </summary>
        /// <param name="hashValue"></param>
        /// <returns></returns>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static ulong GetHashValueULong(int hashValue)
        {
            unsafe
            {
                var span = new ReadOnlySpan<byte>(&hashValue, sizeof(int));

                ulong fnvPrime = 0x00000100000001B3ul;
                ulong fnvOffsetBasis = 0xcbf29ce484222325;

                ulong hash = fnvOffsetBasis;

                for (int i = 0; i < span.Length; i++)
                {
                    hash = span[i] ^ hash;
                    hash *= fnvPrime;
                }

                return hash;
            }
        }

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        private static THashValue CombineHashValue(THashValue hashValue, ReadOnlySpan<byte> span)
        {
            if (typeof(THashValue) == typeof(uint))
            {
                return (THashValue)(object)FNVHashFunction<uint, UIntHashValueOperators>.CombineHashValue((uint)(object)hashValue, span);
            }
            else if (typeof(THashValue) == typeof(ulong))
            {
                return (THashValue)(object)FNVHashFunction<ulong, ULongHashValueOperators>.CombineHashValue((ulong)(object)hashValue, span);
            }
            else
            {
                throw new NotImplementedException();
            }
        }

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        private static THashValue GetHashValue(ReadOnlySpan<byte> span)
        {
            if (typeof(THashValue) == typeof(uint))
            {
                return (THashValue)(object)FNVHashFunction<uint, UIntHashValueOperators>.GetHashValue(span);
            }
            else if (typeof(THashValue) == typeof(ulong))
            {
                return (THashValue)(object)FNVHashFunction<ulong, ULongHashValueOperators>.GetHashValue(span);
            }
            else
            {
                throw new NotImplementedException();
            }
        }

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public THashValue CombineHashValue(THashValue hash, string value)
        {
            ReadOnlySpan<byte> span = MemoryMarshal.Cast<char, byte>(value.AsSpan());

            return CombineHashValue(hash, span);
        }

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public THashValue CombineHashValue<T>(THashValue hash, T value)
            where T : unmanaged
        {
            unsafe
            {
                var span = new ReadOnlySpan<byte>(&value, sizeof(T));

                return CombineHashValue(hash, span);
            }
        }

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public THashValue GetHashValue(string value)
        {
            ReadOnlySpan<byte> span = MemoryMarshal.Cast<char, byte>(value.AsSpan());

            return GetHashValue(span);
        }

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public THashValue GetHashValue<T>(T value)
            where T : unmanaged
        {
            unsafe
            {
                var span = new ReadOnlySpan<byte>(&value, sizeof(T));

                return GetHashValue(span);
            }
        }
    }
    #endregion

#pragma warning restore CA1000 // Do not declare static members on generic types
#pragma warning restore CA1066 // Type {0} should implement IEquatable<T> because it overrides Equals
#pragma warning restore CA1716 // Identifiers should not match keywords
#pragma warning restore CA1815 // Override equals and operator equals on value types
#pragma warning restore CA2231 // Overload operator equals on overriding value type Equals
#pragma warning restore CS0659 // Type overrides Object.Equals(object o) but does not override Object.GetHashCode()
}
