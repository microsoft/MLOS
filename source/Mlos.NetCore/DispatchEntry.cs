// -----------------------------------------------------------------------
// <copyright file="DispatchEntry.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;

namespace Mlos.Core
{
    /// <summary>
    /// Dispatch entry.
    /// </summary>
    public struct DispatchEntry : IEquatable<DispatchEntry>
    {
        /// <summary>
        /// Operator ==.
        /// </summary>
        /// <param name="left"></param>
        /// <param name="right"></param>
        /// <returns></returns>
        public static bool operator ==(DispatchEntry left, DispatchEntry right)
        {
            return left.Equals(right);
        }

        /// <summary>
        /// Operator ==.
        /// </summary>
        /// <param name="left"></param>
        /// <param name="right"></param>
        /// <returns></returns>
        public static bool operator !=(DispatchEntry left, DispatchEntry right)
        {
            return !(left == right);
        }

        /// <summary>
        /// CodegenType hash value.
        /// </summary>
        public ulong CodegenTypeHash;

        /// <summary>
        /// Callback.
        /// </summary>
        public Func<IntPtr, int, bool> Callback;

        /// <inheritdoc />
        public override int GetHashCode()
        {
            return CodegenTypeHash.GetHashCode();
        }

        /// <inheritdoc />
        public override bool Equals(object obj)
        {
            if (!(obj is DispatchEntry))
            {
                return false;
            }

            return Equals((DispatchEntry)obj);
        }

        /// <inheritdoc />
        public bool Equals(DispatchEntry other)
        {
            return CodegenTypeHash == other.CodegenTypeHash;
        }
    }
}
