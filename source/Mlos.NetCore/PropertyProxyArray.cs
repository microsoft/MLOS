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
    /// <typeparam name="TType">Codegen type.</typeparam>
    /// <typeparam name="TProxy">Proxy type.</typeparam>
    public readonly struct PropertyProxyArray<TType, TProxy> : IEquatable<PropertyProxyArray<TType, TProxy>>, IEquatable<TType[]>
        where TType : ICodegenType, new()
        where TProxy : ICodegenProxy<TType, TProxy>, new()
    {
        /// <summary>
        /// Operator ==.
        /// </summary>
        /// <param name="left"></param>
        /// <param name="right"></param>
        /// <returns></returns>
        public static bool operator ==(PropertyProxyArray<TType, TProxy> left, PropertyProxyArray<TType, TProxy> right) => left.Equals(right);

        /// <summary>
        /// Operator !=.
        /// </summary>
        /// <param name="left"></param>
        /// <param name="right"></param>
        /// <returns></returns>
        public static bool operator !=(PropertyProxyArray<TType, TProxy> left, PropertyProxyArray<TType, TProxy> right) => !(left == right);

        /// <summary>
        /// Initializes a new instance of the <see cref="PropertyProxyArray{TType, TProxy}"/> struct.
        /// </summary>
        /// <param name="buffer"></param>
        /// <param name="typeSize">Size of the underlying proxy type.</param>
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
        public TProxy this[int i]
        {
            get
            {
                unsafe
                {
                    return new TProxy() { Buffer = buffer + (i * typeSize) };
                }
            }
        }

        /// <inheritdoc />
        public override bool Equals(object obj)
        {
            if (obj is PropertyProxyArray<TType, TProxy> proxyArray)
            {
                return Equals(proxyArray);
            }
            else if (obj is TType[] array)
            {
                return Equals(array);
            }

            return false;
        }

        /// <inheritdoc />
        public bool Equals(PropertyProxyArray<TType, TProxy> other) =>
            buffer == other.buffer &&
            typeSize == other.typeSize;

        /// <inheritdoc />
        public bool Equals(TType[] other)
        {
            for (int i = 0; i < other.Length; i++)
            {
                if (!this[i].Equals(other[i]))
                {
                    return false;
                }
            }

            return true;
        }

        /// <inheritdoc />
        public override int GetHashCode() => buffer.GetHashCode();

        private readonly IntPtr buffer;

        private readonly int typeSize;
    }
}
