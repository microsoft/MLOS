// -----------------------------------------------------------------------
// <copyright file="ICodegenType.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;

using Mlos.Core.Collections;

namespace Mlos.Core
{
    /// <summary>
    /// Interface for code generated types.
    /// </summary>
    /// <remarks>
    /// Implementation is required to send the object over the communication channel.
    /// </remarks>
    public interface ICodegenType : ICodegenKey
    {
        /// <summary>
        /// Returns size of the fixed part of the object.
        /// </summary>
        /// <returns></returns>
        ulong CodegenTypeSize();

        /// <summary>
        /// Calculates size required to persist data of fields with variable length.
        /// </summary>
        /// <remarks>
        /// We are calculating just the size of the occupied data. For example for string type, we return the length of string multiplied by the size of char.
        /// </remarks>
        /// <returns></returns>
        ulong GetVariableDataSize();

        /// <summary>
        /// Serialize variable data.
        /// </summary>
        /// <param name="buffer"></param>
        /// <param name="objectOffset"></param>
        /// <param name="dataOffset"></param>
        /// <returns></returns>
        ulong SerializeVariableData(IntPtr buffer, ulong objectOffset, ulong dataOffset);

        /// <summary>
        /// Serialize fixed part.
        /// </summary>
        /// <param name="buffer"></param>
        /// <param name="objectOffset"></param>
        void SerializeFixedPart(IntPtr buffer, ulong objectOffset);

        /// <summary>
        /// Copy values from the proxy to the object.
        /// </summary>
        /// <param name="sourceProxy"></param>
        void Update(ICodegenProxy sourceProxy);
    }

    /// <summary>
    /// Specialization of code type interface with codegen type and proxy information.
    /// </summary>
    /// <typeparam name="TCodegenType">Codegen type.</typeparam>
    /// <typeparam name="TCodegenProxy">Codegen proxy.</typeparam>
    public interface ICodegenType<TCodegenType, TCodegenProxy> : ICodegenType
        where TCodegenType : ICodegenType
        where TCodegenProxy : ICodegenProxy
    {
    }
}
