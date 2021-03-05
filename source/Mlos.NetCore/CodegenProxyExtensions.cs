// -----------------------------------------------------------------------
// <copyright file="CodegenProxyExtensions.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System.Runtime.CompilerServices;

namespace Mlos.Core
{
    /// <summary>
    /// Verification extension methods for ICodegenProxy.
    /// </summary>
    public static class CodegenProxyExtensions
    {
        /// <summary>
        /// Verifies serialized variable data.
        /// </summary>
        /// <typeparam name="TType">Codegen type.</typeparam>
        /// <typeparam name="TProxy">Codegen proxy type.</typeparam>
        /// <param name="array"></param>
        /// <param name="elementCount"></param>
        /// <param name="objectOffset"></param>
        /// <param name="totalDataSize"></param>
        /// <param name="expectedDataOffset"></param>
        /// <returns></returns>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static bool VerifyVariableData<TType, TProxy>(this PropertyProxyArray<TType, TProxy> array, uint elementCount, ulong objectOffset, ulong totalDataSize, ref ulong expectedDataOffset)
            where TType : ICodegenType, new()
            where TProxy : ICodegenProxy<TType, TProxy>, new()
        {
            ulong codegenTypeSize = default(TProxy).CodegenTypeSize();

            for (uint i = 0; i < elementCount; i++)
            {
                if (!((ICodegenProxy)array[(int)i]).VerifyVariableData(objectOffset + (i * codegenTypeSize), totalDataSize, ref expectedDataOffset))
                {
                    return false;
                }
            }

            return true;
        }

        /// <summary>
        /// Verifies serialized variable data.
        /// </summary>
        /// <typeparam name="T">Type of the serialized object.</typeparam>
        /// <param name="proxy"></param>
        /// <param name="frameLength"></param>
        /// <returns></returns>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static bool VerifyVariableData<T>(this T proxy, int frameLength)
            where T : ICodegenProxy, new()
        {
            ulong expectedDataOffset = proxy.CodegenTypeSize();
            ulong totalDataSize = (ulong)frameLength - expectedDataOffset;
            bool isValid = ((ICodegenProxy)proxy).VerifyVariableData(0, totalDataSize, ref expectedDataOffset);

            isValid &= (FrameHeader.TypeSize + (int)expectedDataOffset) <= frameLength;
            return isValid;
        }
    }
}
