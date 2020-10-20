// -----------------------------------------------------------------------
// <copyright file="PropertyProxyArray.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;

namespace Mlos.Core
{
    /// <summary>
    /// Property proxy array accessor class.
    /// </summary>
    /// <typeparam name="T">Proxy type.</typeparam>
    public struct PropertyProxyArray<T> : IEquatable<PropertyProxyArray<T>>
        where T : ICodegenProxy, new()
    {
        /// <summary>
        /// Operator ==.
        /// </summary>
        /// <param name="left"></param>
        /// <param name="right"></param>
        /// <returns></returns>
        public static bool operator ==(PropertyProxyArray<T> left, PropertyProxyArray<T> right) => left.Equals(right);

        /// <summary>
        /// Operator !=.
        /// </summary>
        /// <param name="left"></param>
        /// <param name="right"></param>
        /// <returns></returns>
        public static bool operator !=(PropertyProxyArray<T> left, PropertyProxyArray<T> right) => !(left == right);

        /// <summary>
        /// Initializes a new instance of the <see cref="PropertyProxyArray{T}"/> struct.
        /// </summary>
        /// <param name="buffer"></param>
        /// <param name="typeSize">Size of the underlaying proxy type.</param>
        public PropertyProxyArray(IntPtr buffer, int typeSize)
        {
            this.buffer = buffer;
            this.typeSize = typeSize;
        }

        /// <summary>
        /// Define the indexer to allow client code to use [] notation.
        /// </summary>
        /// <param name="i"></param>
        /// <returns></returns>
        public T this[int i]
        {
            get
            {
                unsafe
                {
                    return new T() { Buffer = buffer + (i * typeSize) };
                }
            }
        }

        /// <inheritdoc />
        public override bool Equals(object obj)
        {
            if (!(obj is PropertyProxyArray<T>))
            {
                return false;
            }

            return Equals((PropertyProxyArray<T>)obj);
        }

        /// <inheritdoc />
        public bool Equals(PropertyProxyArray<T> other) =>
            buffer == other.buffer &&
            typeSize == other.typeSize;

        /// <inheritdoc />
        public override int GetHashCode() => buffer.GetHashCode();

        private readonly IntPtr buffer;

        private readonly int typeSize;
    }
}
