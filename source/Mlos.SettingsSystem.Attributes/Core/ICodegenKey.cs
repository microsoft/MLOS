// -----------------------------------------------------------------------
// <copyright file="ICodegenKey.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using Mlos.Core.Collections;

namespace Mlos.Core
{
    /// <summary>
    /// Codegen key interface to code generated key types.
    /// </summary>
    public interface ICodegenKey
    {
        /// <summary>
        /// Returns unique, global identifier of the type.
        /// </summary>
        /// <returns></returns>
        uint CodegenTypeIndex();

        /// <summary>
        /// Returns a hash value generated from the type definition.
        /// </summary>
        /// <returns></returns>
        ulong CodegenTypeHash();

        /// <summary>
        /// Get primary key hash value.
        /// </summary>
        /// <typeparam name="THash">Hash implementation.</typeparam>
        /// <returns></returns>
        uint GetKeyHashValue<THash>()
            where THash : IHash<uint>;

        /// <summary>
        /// Compare primary key with another instance.
        /// </summary>
        /// <param name="proxy"></param>
        /// <returns></returns>
        bool CompareKey(ICodegenProxy proxy);
    }

    /// <summary>
    /// Specialization of key interface with codegen type and proxy information.
    /// </summary>
    /// <typeparam name="TCodegenType">Codegen type.</typeparam>
    /// <typeparam name="TCodegenKey">Codegen key.</typeparam>
    /// <typeparam name="TCodegenProxy">Codegen proxy.</typeparam>
    public interface ICodegenKey<TCodegenType, TCodegenKey, TCodegenProxy> : ICodegenKey
        where TCodegenType : ICodegenType
        where TCodegenKey : ICodegenKey
        where TCodegenProxy : ICodegenProxy
    {
    }
}
