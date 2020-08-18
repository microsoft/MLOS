// -----------------------------------------------------------------------
// <copyright file="DeserializeEntry.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;

namespace Mlos.Core
{
    /// <summary>
    /// Deserialize entry.
    /// </summary>
    public struct DeserializeEntry : IEquatable<DeserializeEntry>
    {
        /// <summary>
        /// Operator ==.
        /// </summary>
        /// <param name="left"></param>
        /// <param name="right"></param>
        /// <returns></returns>
        public static bool operator ==(DeserializeEntry left, DeserializeEntry right)
        {
            return left.Equals(right);
        }

        /// <summary>
        /// Operator ==.
        /// </summary>
        /// <param name="left"></param>
        /// <param name="right"></param>
        /// <returns></returns>
        public static bool operator !=(DeserializeEntry left, DeserializeEntry right)
        {
            return !(left == right);
        }

        /// <summary>
        /// Type hash.
        /// </summary>
        public ulong TypeHash;

        /// <summary>
        /// Deserialize function.
        /// </summary>
        public Func<IntPtr, ICodegenProxy> Deserialize;

        /// <inheritdoc />
        public override int GetHashCode()
        {
            return TypeHash.GetHashCode();
        }

        /// <inheritdoc />
        public override bool Equals(object obj)
        {
            if (!(obj is DeserializeEntry))
            {
                return false;
            }

            return Equals((DeserializeEntry)obj);
        }

        /// <inheritdoc/>
        public bool Equals(DeserializeEntry other)
        {
            return TypeHash == other.TypeHash;
        }
    }
}
