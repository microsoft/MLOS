// -----------------------------------------------------------------------
// <copyright file="CodegenTypeExtensions.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;

namespace Mlos.Core
{
    /// <summary>
    /// Serialization extension methods for ICodegenType.
    /// </summary>
    public static class CodegenTypeExtensions
    {
        public static void Serialize<T>(T instance, IntPtr buffer)
            where T : ICodegenType
        {
            ulong objectOffset = 0;

            // Variable data is located after fixed part of the object.
            //
            ulong dataOffset = instance.CodegenTypeSize();

            // Serialize fixed size part of the object.
            //
            instance.SerializeFixedPart(buffer, objectOffset);

            // Then serialize variable data of the object.
            //
            instance.SerializeVariableData(buffer, objectOffset, dataOffset);
        }

        /// <summary>
        /// Gets serialize instance size, that includes fixed size and the variable data size.
        /// </summary>
        /// <typeparam name="T">Instance type.</typeparam>
        /// <param name="instance"></param>
        /// <returns></returns>
        public static ulong GetSerializedSize<T>(T instance)
            where T : ICodegenType
        {
            ulong size = instance.CodegenTypeSize();
            size += instance.GetVariableDataSize();

            return size;
        }

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static ulong GetVariableDataSize<T>(this T[] collection, uint elementCount)
            where T : ICodegenType
        {
            ulong dataSize = 0;

            for (int i = 0; i < (int)elementCount; i++)
            {
                dataSize += collection[i].GetVariableDataSize();
            }

            return dataSize;
        }

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static ulong SerializeVariableData<T>(this T[] collection, uint elementCount, IntPtr buffer, ulong objectOffset, ulong dataOffset)
            where T : ICodegenType
        {
            ulong dataSize = 0;

            for (int i = 0; i < (int)elementCount; i++)
            {
                ulong elementDataSize = collection[i].GetVariableDataSize();
                collection[i].SerializeVariableData(buffer, objectOffset, dataOffset);

                objectOffset += 16;
                dataOffset += elementDataSize;

                dataSize += elementDataSize;
            }

            return dataSize;
        }

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static void SerializeFixedPart<T>(T value, IntPtr buffer, ulong objectOffset)
            where T : unmanaged
        {
            unsafe
            {
                *(T*)(buffer + (int)objectOffset).ToPointer() = value;
            }
        }

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static void SerializeFixedPartPrimitiveTypeArray<T>(this T[] collection, uint elementCount, IntPtr buffer, ulong objectOffset)
            where T : unmanaged
        {
            if (collection == null)
            {
                return;
            }

            ulong elementSize = (ulong)Marshal.SizeOf<T>();

            for (int i = 0; i < (int)elementCount; i++)
            {
                SerializeFixedPart(collection[i], buffer, objectOffset);

                objectOffset += elementSize;
            }
        }

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static void SerializeFixedPartCodetypeArray<T>(this T[] collection, uint elementCount, IntPtr buffer, ulong objectOffset)
            where T : ICodegenType
        {
            if (collection == null)
            {
                return;
            }

            for (int i = 0; i < (int)elementCount; i++)
            {
                ulong elementSize = collection[i].CodegenTypeSize();
                collection[i].SerializeFixedPart(buffer, objectOffset);

                objectOffset += elementSize;
            }
        }

        /// <summary>
        /// #TODO is update the best name ?.
        /// </summary>
        /// <typeparam name="T">Array element type.</typeparam>
        /// <param name="collection"></param>
        /// <param name="proxyArray"></param>
        /// <param name="elementCount"></param>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static void UpdateProxyArray<T>(this T[] collection, ProxyArray<T> proxyArray, uint elementCount)
            where T : unmanaged
        {
            for (int i = 0; i < (int)elementCount; i++)
            {
                collection[i] = proxyArray[i];
            }
        }

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static void UpdatePropertyProxyArray<T, TProxy>(this T[] collection, PropertyProxyArray<TProxy> proxyArray, uint elementCount)
            where T : ICodegenType
            where TProxy : ICodegenProxy, new()
        {
            for (int i = 0; i < (int)elementCount; i++)
            {
                collection[i].Update(proxyArray[i]);
            }
        }
    }
}
