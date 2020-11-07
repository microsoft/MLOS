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
        /// <summary>
        /// Calculates hash value for given string and combines it with the hash value.
        /// </summary>
        /// <param name="hashValue"></param>
        /// <param name="value"></param>
        /// <returns></returns>
        THashValue CombineHashValue(THashValue hashValue, string value);

        /// <summary>
        /// Calculates hash value for given parameter and combines it with the hash value.
        /// </summary>
        /// <param name="hashValue"></param>
        /// <param name="value"></param>
        /// <typeparam name="T">Type the given parameter.</typeparam>
        /// <returns></returns>
        THashValue CombineHashValue<T>(THashValue hashValue, T value)
            where T : unmanaged;

        /// <summary>
        /// Gets the hash value for the given string.
        /// </summary>
        /// <param name="value"></param>
        /// <returns></returns>
        THashValue GetHashValue(string value);

        /// <summary>
        /// Gets the hash value for the given parameter.
        /// </summary>
        /// <param name="value"></param>
        /// <typeparam name="T">Type the given parameter.</typeparam>
        /// <returns></returns>
        THashValue GetHashValue<T>(T value)
            where T : unmanaged;
    }
}
