// -----------------------------------------------------------------------
// <copyright file="SharedConfig.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using Mlos.Core.Collections;

using MlosProxy = Proxy.Mlos.Core;

namespace Mlos.Core
{
    /// <summary>
    /// Shared config. Proxy to configuration stored in the shared memory.
    /// </summary>
    /// <typeparam name="TProxy">Proxy type of the configuration.</typeparam>
    public struct SharedConfig<TProxy> : IEquatable<SharedConfig<TProxy>>, ICodegenProxy
        where TProxy : ICodegenProxy, new()
    {
        /// <summary>
        /// Operator ==.
        /// </summary>
        /// <param name="left"></param>
        /// <param name="right"></param>
        /// <returns></returns>
        public static bool operator ==(SharedConfig<TProxy> left, SharedConfig<TProxy> right) => left.Equals(right);

        /// <summary>
        /// Operator !=.
        /// </summary>
        /// <param name="left"></param>
        /// <param name="right"></param>
        /// <returns></returns>
        public static bool operator !=(SharedConfig<TProxy> left, SharedConfig<TProxy> right) => !(left == right);

        /// <inheritdoc />
        public override bool Equals(object obj)
        {
            if (!(obj is SharedConfig<TProxy>))
            {
                return false;
            }

            return Equals((SharedConfig<TProxy>)obj);
        }

        /// <inheritdoc />
        public bool Equals(SharedConfig<TProxy> other) => Buffer == other.Buffer;

        /// <inheritdoc />
        public override int GetHashCode() => Buffer.GetHashCode();

        /// <inheritdoc/>
        public ulong CodegenTypeSize() => SharedConfigHeader.TypeSize + default(TProxy).CodegenTypeSize();

        /// <inheritdoc/>
        public uint CodegenTypeIndex() => throw new NotImplementedException();

        /// <inheritdoc/>
        public ulong CodegenTypeHash() => throw new NotImplementedException();

        /// <inheritdoc/>
        public uint GetKeyHashValue<THash>()
            where THash : IHash<uint> => throw new NotImplementedException();

        /// <inheritdoc/>
        public bool CompareKey(ICodegenProxy proxy) => throw new NotImplementedException();

        /// <summary>
        /// Gets shared config header.
        /// </summary>
        public MlosProxy.SharedConfigHeader Header => new MlosProxy.SharedConfigHeader { Buffer = this.Buffer };

        /// <summary>
        /// Gets a value indicating whether the instance points to a valid config in the shared memory.
        /// </summary>
        /// <returns></returns>
        public bool HasSharedConfig => Buffer != IntPtr.Zero;

        /// <summary>
        /// Gets the proxy object to the configuration stored in the shared memory.
        /// </summary>
        public TProxy Config => new TProxy { Buffer = this.Buffer + SharedConfigHeader.TypeSize };

        /// <inheritdoc/>
        bool ICodegenProxy.VerifyVariableData(ulong objectOffset, ulong totalDataSize, ref ulong expectedDataOffset) => true;

        /// <inheritdoc/>
        public IntPtr Buffer { get; set; }
    }
}
