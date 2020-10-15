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

    /// <summary>
    /// Interface defines operations used to calculate the hash value.
    /// </summary>
    /// <typeparam name="THashValue">Type used to store hash value (uint or ulong).</typeparam>
    public interface IHashValueOperators<THashValue>
         where THashValue : struct
    {
        /// <summary>
        /// Convert functions.
        /// </summary>
        /// <param name="a"></param>
        /// <returns></returns>
        THashValue Convert(byte a);

        /// <summary>
        /// Convert functions.
        /// </summary>
        /// <param name="a"></param>
        /// <returns></returns>
        THashValue Convert(char a);

        /// <summary>
        /// Convert functions.
        /// </summary>
        /// <param name="a"></param>
        /// <returns></returns>
        THashValue Convert(uint a);

        /// <summary>
        /// Convert functions.
        /// </summary>
        /// <param name="a"></param>
        /// <returns></returns>
        THashValue Convert(ulong a);

        /// <summary>
        /// Calcuate xor value.
        /// </summary>
        /// <param name="a"></param>
        /// <param name="b"></param>
        /// <returns></returns>
        THashValue Xor(THashValue a, THashValue b);

        /// <summary>
        /// Multiply value.
        /// </summary>
        /// <param name="a"></param>
        /// <param name="b"></param>
        /// <returns></returns>
        THashValue Mul(THashValue a, THashValue b);

        /// <summary>
        /// Shift left a &lt;&lt; b.
        /// </summary>
        /// <param name="a"></param>
        /// <param name="b"></param>
        /// <returns></returns>
        THashValue ShiftLeft(THashValue a, int b);

        /// <summary>
        /// Shift right a>>b.
        /// </summary>
        /// <param name="a"></param>
        /// <param name="b"></param>
        /// <returns></returns>
        THashValue ShiftRight(THashValue a, int b);
    }

    /// <summary>
    /// Implementation of IHashValueOperators that supports uint values.
    /// </summary>
    public struct UIntHashValueOperators : IHashValueOperators<uint>
    {
        /// <inheritdoc/>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public uint Convert(byte a) => a;

        /// <inheritdoc/>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public uint Convert(char a) => a;

        /// <inheritdoc/>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public uint Convert(uint a) => a;

        /// <inheritdoc/>
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

    /// <summary>
    /// Implementation of IHashValueOperators that supports ulong values.
    /// </summary>
    public struct ULongHashValueOperators : IHashValueOperators<ulong>
    {
        /// <inheritdoc/>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public ulong Convert(byte a) => a;

        /// <inheritdoc/>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public ulong Convert(char a) => a;

        /// <inheritdoc/>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public ulong Convert(uint a) => a;

        /// <inheritdoc/>
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
