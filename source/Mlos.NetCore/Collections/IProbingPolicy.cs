// -----------------------------------------------------------------------
// <copyright file="IProbingPolicy.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Collections.Generic;
using System.Text;

namespace Mlos.Core.Collections
{
    /// <summary>
    /// Hash table probing policy interface.
    /// </summary>
    public interface IProbingPolicy
    {
        /// <summary>
        /// Calculates the hash table index of for the given key.
        /// </summary>
        /// <param name="codegenKey"></param>
        /// <param name="probingCount"></param>
        /// <param name="elementCount"></param>
        /// <returns></returns>
        uint CalculateIndex(ICodegenKey codegenKey, ref uint probingCount, uint elementCount);
    }

    public struct TLinearProbing<THash> : IProbingPolicy
        where THash : IHash<uint>
    {
        /// <inheritdoc/>
        public uint CalculateIndex(ICodegenKey codegenKey, ref uint probingCount, uint elementCount)
        {
            uint hashValue = codegenKey.GetKeyHashValue<THash>();
            return (hashValue + probingCount++) % elementCount;
        }
    }
}
