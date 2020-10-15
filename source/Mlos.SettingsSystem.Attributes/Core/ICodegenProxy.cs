// -----------------------------------------------------------------------
// <copyright file="ICodegenProxy.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;

namespace Mlos.Core
{
    /// <summary>
    /// Proxy interface to code generated types.
    /// </summary>
    public interface ICodegenProxy : ICodegenKey
    {
        /// <summary>
        /// Returns size of the fixed part of the object.
        /// </summary>
        /// <returns></returns>
        ulong CodegenTypeSize();

        /// <summary>
        /// Verifies the variable data.
        /// </summary>
        /// <param name="objectOffset"></param>
        /// <param name="totalDataSize"></param>
        /// <param name="expectedDataOffset"></param>
        /// <returns></returns>
        /// <remarks>
        /// Method verifies if the variable data of the proxy has correct size and it is within limit of the message.
        /// </remarks>
        bool VerifyVariableData(ulong objectOffset, ulong totalDataSize, ref ulong expectedDataOffset);

        /// <summary>
        /// Gets or sets pointer to the shared memory where we store the instance of code gen type.
        /// </summary>
        IntPtr Buffer { get; set; }
    }

    /// <summary>
    /// Proxy specialization interface with codegen type and proxy information.
    /// </summary>
    /// <typeparam name="TCodegenType">Codegen type.</typeparam>
    /// <typeparam name="TCodegenProxy">Codegen proxy.</typeparam>
    public interface ICodegenProxy<TCodegenType, TCodegenProxy> : ICodegenProxy
        where TCodegenType : ICodegenType
        where TCodegenProxy : ICodegenProxy
    {
    }
}
