// -----------------------------------------------------------------------
// <copyright file="ProxyArray.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;

namespace Mlos.Core
{
    /// <summary>
    /// Property array accessor class.
    /// </summary>
    /// <typeparam name="T">Proxy type.</typeparam>
    public struct ProxyArray<T> : IEquatable<ProxyArray<T>>
        where T : unmanaged
    {
        /// <summary>
        /// Operator ==.
        /// </summary>
        /// <param name="left"></param>
        /// <param name="right"></param>
        /// <returns></returns>
        public static bool operator ==(ProxyArray<T> left, ProxyArray<T> right) => left.Equals(right);

        /// <summary>
        /// Operator !=.
        /// </summary>
        /// <param name="left"></param>
        /// <param name="right"></param>
        /// <returns></returns>
        public static bool operator !=(ProxyArray<T> left, ProxyArray<T> right) => !(left == right);

        /// <summary>
        /// Initializes a new instance of the <see cref="ProxyArray{T}"/> struct.
        /// </summary>
        /// <param name="buffer"></param>
        /// <param name="typeSize">Size of the underlying proxy type.</param>
        public ProxyArray(IntPtr buffer, int typeSize)
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
                    return *(T*)(buffer + (i * typeSize)).ToPointer();
                }
            }

            set
            {
                unsafe
                {
                    *(T*)(buffer + (i * typeSize)).ToPointer() = value;
                }
            }
        }

        /// <inheritdoc />
        public override bool Equals(object obj)
        {
            if (!(obj is ProxyArray<T>))
            {
                return false;
            }

            return Equals((ProxyArray<T>)obj);
        }

        /// <inheritdoc />
        public bool Equals(ProxyArray<T> other) =>
            buffer == other.buffer &&
            typeSize == other.typeSize;

        /// <inheritdoc />
        public override int GetHashCode() => buffer.GetHashCode();

        private readonly IntPtr buffer;

        private readonly int typeSize;
    }
}
