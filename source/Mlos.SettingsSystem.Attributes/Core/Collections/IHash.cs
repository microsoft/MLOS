// -----------------------------------------------------------------------
// <copyright file="IHash.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

namespace Mlos.Core.Collections
{
    /// <summary>
    /// Hash implementation interface.
    /// </summary>
    /// <typeparam name="THashValue">Type of the hash value (uint32_t or uint64_t).</typeparam>
    public interface IHash<THashValue>
        where THashValue : unmanaged
    {
        THashValue CombineHashValue(THashValue hashValue, string value);

        THashValue CombineHashValue<T>(THashValue hashValue, T value)
            where T : unmanaged;

        THashValue GetHashValue(string value);

        THashValue GetHashValue<T>(T value)
            where T : unmanaged;
    }
}