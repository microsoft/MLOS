// -----------------------------------------------------------------------
// <copyright file="ArrayExtensions.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

namespace Mlos.Core
{
    /// <summary>
    /// Array extension methods.
    /// </summary>
    public static class ArrayExtensions
    {
        /// <summary>
        /// Creates an array of objects.
        /// </summary>
        /// <param name="array"></param>
        /// <typeparam name="T">The type of the elements in the array.</typeparam>
        public static void Create<T>(this T[] array)
            where T : new()
        {
            for (int i = 0; i < array.Length; i++)
            {
                array[i] = new T();
            }
        }
    }
}
