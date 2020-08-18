// -----------------------------------------------------------------------
// <copyright file="IHashValueOperators.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Runtime.CompilerServices;

namespace Mlos.Core.Collections
{
#pragma warning disable CA1000 // Do not declare static members on generic types
#pragma warning disable CA1066 // Type {0} should implement IEquatable<T> because it overrides Equals
#pragma warning disable CA1716 // Identifiers should not match keywords
#pragma warning disable CA1815 // Override equals and operator equals on value types
#pragma warning disable CA2231 // Overload operator equals on overriding value type Equals
#pragma warning disable CS0659 // Type overrides Object.Equals(object o) but does not override Object.GetHashCode()

    public interface IHashValueOperators<THash>
         where THash : struct
    {
        /// <summary>
        /// Convert functions.
        /// </summary>
        /// <param name="a"></param>
        /// <returns></returns>
        THash Convert(byte a);
        THash Convert(char a);
        THash Convert(uint a);
        THash Convert(ulong a);

        /// <summary>
        /// Calcuate xor value.
        /// </summary>
        /// <param name="a"></param>
        /// <param name="b"></param>
        /// <returns></returns>
        THash Xor(THash a, THash b);

        /// <summary>
        /// Multiply value.
        /// </summary>
        /// <param name="a"></param>
        /// <param name="b"></param>
        /// <returns></returns>
        THash Mul(THash a, THash b);

        /// <summary>
        /// Shift left a &lt;&lt; b.
        /// </summary>
        /// <param name="a"></param>
        /// <param name="b"></param>
        /// <returns></returns>
        THash ShiftLeft(THash a, int b);

        /// <summary>
        /// Shift right a>>b.
        /// </summary>
        /// <param name="a"></param>
        /// <param name="b"></param>
        /// <returns></returns>
        THash ShiftRight(THash a, int b);
    }

    public struct UIntHashValueOperators : IHashValueOperators<uint>
    {
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public uint Convert(byte a) => a;

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public uint Convert(char a) => a;

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public uint Convert(uint a) => a;

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public uint Convert(ulong a) => throw new NotImplementedException();

        /// <inheritdoc/>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public uint Xor(uint a, uint b) => a ^ b;

        /// <inheritdoc/>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public uint Mul(uint a, uint b) => a * b;

        /// <inheritdoc/>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public uint ShiftLeft(uint a, int b) => a << b;

        /// <inheritdoc/>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public uint ShiftRight(uint a, int b) => a >> b;
    }

    public struct ULongHashValueOperators : IHashValueOperators<ulong>
    {
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public ulong Convert(byte a) => a;

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public ulong Convert(char a) => a;

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public ulong Convert(uint a) => a;

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public ulong Convert(ulong a) => a;

        /// <inheritdoc/>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public ulong Xor(ulong a, ulong b) => a ^ b;

        /// <inheritdoc/>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public ulong Mul(ulong a, ulong b) => a * b;

        /// <inheritdoc/>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public ulong ShiftLeft(ulong a, int b) => a << b;

        /// <inheritdoc/>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public ulong ShiftRight(ulong a, int b) => a >> b;
    }

#pragma warning restore CA1000 // Do not declare static members on generic types
#pragma warning restore CA1066 // Type {0} should implement IEquatable<T> because it overrides Equals
#pragma warning restore CA1716 // Identifiers should not match keywords
#pragma warning restore CA1815 // Override equals and operator equals on value types
#pragma warning restore CA2231 // Overload operator equals on overriding value type Equals
#pragma warning restore CS0659 // Type overrides Object.Equals(object o) but does not override Object.GetHashCode()
}
