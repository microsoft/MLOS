// -----------------------------------------------------------------------
// <copyright file="Utils.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System.Runtime.CompilerServices;

namespace Mlos.Core
{
    /// <summary>
    /// Utility helper class.
    /// </summary>
    public static class Utils
    {
        /// <summary>
        /// Returns aligment value for given input value and alignment.
        /// </summary>
        /// <param name="size"></param>
        /// <param name="aligment"></param>
        /// <returns></returns>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static ulong Align(ulong size, uint aligment) => ((size + aligment - 1) / aligment) * aligment;

        /// <summary>
        /// Returns aligment value for given input value and alignment.
        /// </summary>
        /// <param name="size"></param>
        /// <param name="aligment"></param>
        /// <returns></returns>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static uint Align(uint size, uint aligment) => ((size + aligment - 1) / aligment) * aligment;

        /// <summary>
        /// Returns aligment value for given input value and alignment.
        /// </summary>
        /// <param name="size"></param>
        /// <param name="aligment"></param>
        /// <returns></returns>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static int Align(int size, int aligment) => ((size + aligment - 1) / aligment) * aligment;

        /// <summary>
        /// Converts a unsigned long value into high and low unsigned integers.
        /// </summary>
        /// <param name="number"></param>
        /// <param name="high"></param>
        /// <param name="low"></param>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static void SplitULong(ulong number, out uint high, out uint low)
        {
            high = unchecked((uint)(number >> 32));
            low = unchecked((uint)(number & 0x00000000FFFFFFFFL));
        }
    }
}
