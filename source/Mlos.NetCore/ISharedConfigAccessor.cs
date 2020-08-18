// -----------------------------------------------------------------------
// <copyright file="ISharedConfigAccessor.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

namespace Mlos.Core
{
    public interface ISharedConfigAccessor
    {
        /// <summary>
        /// Lookup shared config by codegen key.
        /// </summary>
        /// <typeparam name="TType">Codegen type.</typeparam>
        /// <typeparam name="TKey">Codegen key type.</typeparam>
        /// <typeparam name="TProxy">Codegen proxy.</typeparam>
        /// <param name="codegenKey"></param>
        /// <returns></returns>
        SharedConfig<TProxy> Lookup<TType, TKey, TProxy>(ICodegenKey<TType, TKey, TProxy> codegenKey)
            where TType : ICodegenType, new()
            where TKey : ICodegenKey, new()
            where TProxy : ICodegenProxy<TType, TProxy>, new();

        /// <summary>
        /// Lookup by codegen type.
        /// </summary>
        /// <typeparam name="TType">Codegen type.</typeparam>
        /// <typeparam name="TProxy">Codegen proxy.</typeparam>
        /// <param name="codegenType"></param>
        /// <returns></returns>
        SharedConfig<TProxy> Lookup<TType, TProxy>(ICodegenType<TType, TProxy> codegenType)
            where TType : ICodegenType, new()
            where TProxy : ICodegenProxy<TType, TProxy>, new();

        /// <summary>
        /// Lookup by codegen proxy.
        /// </summary>
        /// <typeparam name="TProxy">Codegen proxy.</typeparam>
        /// <returns></returns>
        public SharedConfig<TProxy> Lookup<TProxy>()
            where TProxy : ICodegenProxy, new();
    }
}
