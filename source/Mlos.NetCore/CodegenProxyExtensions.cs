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
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static bool VerifyVariableData<T>(this PropertyProxyArray<T> array, uint elementCount, ulong objectOffset, ulong totalDataSize, ref ulong expectedDataOffset)
            where T : ICodegenProxy, new()
        {
            ulong codegenTypeSize = default(T).CodegenTypeSize();

            for (uint i = 0; i < elementCount; i++)
            {
                if (!((ICodegenProxy)array[(int)i]).VerifyVariableData(objectOffset + (i * codegenTypeSize), totalDataSize, ref expectedDataOffset))
                {
                    return false;
                }
            }

            return true;
        }

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
