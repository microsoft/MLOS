// -----------------------------------------------------------------------
// <copyright file="MurMur2HashFunction.cs" company="Microsoft Corporation">
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
    /// MurMurHash2a function implementation.
    /// </summary>
    /// <typeparam name="THashValue">Type of the hash value.</typeparam>
    /// <typeparam name="THashValueOperators">Interface to the hash value operators.</typeparam>
    internal struct MurMurHash2aFunction<THashValue, THashValueOperators>
        where THashValue : unmanaged
        where THashValueOperators : IHashValueOperators<THashValue>
    {
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static THashValue GetHashValue(ReadOnlySpan<byte> span)
        {
            THashValue hash;
            THashValueOperators conv = default;

            if (typeof(THashValue) == typeof(uint))
            {
                hash = conv.Convert(0x7FBD4396);
            }
            else if (typeof(THashValue) == typeof(ulong))
            {
                hash = conv.Convert(0x1F0D3804);
            }
            else
            {
                throw new InvalidOperationException();
            }

            return CombineHashValue(hash, span);
        }

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static THashValue CombineHashValue(THashValue hashValue, ReadOnlySpan<byte> span)
        {
            unsafe
            {
                THashValueOperators conv = default;

                THashValue length = conv.Convert((uint)span.Length);

                ReadOnlySpan<THashValue> hashValueSpan = MemoryMarshal.Cast<byte, THashValue>(span);

                for (int i = 0; i < hashValueSpan.Length; i++)
                {
                    THashValue k = hashValueSpan[i];

                    MixHash(ref hashValue, ref k);
                }

                THashValue reminder = conv.Convert(0);
                ReadOnlySpan<byte> reminderSpan = span.Slice(span.Length - (span.Length % (sizeof(THashValue) - 1)));

                for (int i = reminderSpan.Length - 1; i >= 0; i--)
                {
                    reminder = conv.ShiftLeft(reminder, 8);
                    reminder = conv.Xor(reminder, conv.Convert(reminderSpan[i]));
                }

                MixHash(ref hashValue, ref reminder);
                MixHash(ref hashValue, ref length);

                THashValue m = MixValue();

                int r1;
                int r2;

                if (typeof(THashValue) == typeof(uint))
                {
                    r1 = 13;
                    r2 = 15;
                }
                else if (typeof(THashValue) == typeof(ulong))
                {
                    r1 = RValue();
                    r2 = r1;
                }
                else
                {
                    throw new NotImplementedException();
                }

                hashValue = conv.Xor(hashValue, conv.ShiftRight(hashValue, r1));
                hashValue = conv.Mul(hashValue, m);
                hashValue = conv.Xor(hashValue, conv.ShiftRight(hashValue, r2));

                return hashValue;
            }
        }

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        private static THashValue MixValue()
        {
            THashValueOperators conv = default;

            if (typeof(THashValue) == typeof(uint))
            {
                return conv.Convert(0x5bd1e995);
            }
            else if (typeof(THashValue) == typeof(ulong))
            {
                return conv.Convert(0xc6a4a7935bd1e995);
            }
            else
            {
                throw new NotImplementedException();
            }
        }

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        private static int RValue()
        {
            if (typeof(THashValue) == typeof(uint))
            {
                return 24;
            }
            else if (typeof(THashValue) == typeof(ulong))
            {
                return 47;
            }
            else
            {
                throw new NotImplementedException();
            }
        }

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        private static THashValue MixHash(ref THashValue h, ref THashValue k)
        {
            THashValueOperators conv = default;

            int r = RValue();

            THashValue m = MixValue();

            k = conv.Mul(k, m);
            k = conv.Xor(k, conv.ShiftRight(k, r));
            k = conv.Mul(k, m);
            h = conv.Mul(h, m);
            h = conv.Xor(h, k);

            return h;
        }
    }
    #endregion

    /*
    public struct
    {
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static uint CombineHashValue(uint hash, ReadOnlySpan<byte> span)
        {
            return hash;
        }

        private static uint rotl32(uint x, byte r)
        {
            return (x << r) | (x >> (32 - r));
        }

    }
    */

    #region Public implementation

    /*public struct MurMur2Hash : IHash<uint, MurMur2HashFunction>
    {
        public uint CombineHashValue(uint hash, string value)
        {
            throw new NotImplementedException();
        }

        public uint CombineHashValue<T>(uint hash, T value)
            where T : unmanaged
        {
            throw new NotImplementedException();
        }

        public uint GetHashValue(string value)
        {
            throw new NotImplementedException();
        }

        public uint GetHashValue<T>(T value)
            where T : unmanaged
        {
            throw new NotImplementedException();
        }
    }
    */

    #endregion

#pragma warning restore CA1000 // Do not declare static members on generic types
#pragma warning restore CA1066 // Type {0} should implement IEquatable<T> because it overrides Equals
#pragma warning restore CA1716 // Identifiers should not match keywords
#pragma warning restore CA1815 // Override equals and operator equals on value types
#pragma warning restore CA2231 // Overload operator equals on overriding value type Equals
#pragma warning restore CS0659 // Type overrides Object.Equals(object o) but does not override Object.GetHashCode()
}
