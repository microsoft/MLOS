// -----------------------------------------------------------------------
// <copyright file="TypeExtensionMethods.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Linq;
using System.Reflection;

namespace Mlos.SettingsSystem.Attributes
{
    /// <summary>
    /// Set of public Type extension methods.
    /// </summary>
    public static class TypeExtensionMethods
    {
        /// <summary>
        /// Check if given type should be part of codegen.
        /// </summary>
        /// <param name="type"></param>
        /// <returns></returns>
        public static bool IsCodegenType(this Type type)
        {
            return type.GetCustomAttributes(typeof(CodegenTypeAttribute), true).Any();
        }

        /// <summary>
        /// Check if the given type is a tagged as a codegen configuration type.
        /// </summary>
        /// <param name="type"></param>
        /// <returns></returns>
        public static bool IsCodegenConfigType(this Type type)
        {
            return type.GetCustomAttributes(typeof(CodegenConfigAttribute), true).Any();
        }

        /// <summary>
        /// Get all instance (non static) fields.
        /// </summary>
        /// <param name="type"></param>
        /// <returns>Returns an array of fields.</returns>
        public static FieldInfo[] GetPublicInstanceFields(this Type type)
        {
            BindingFlags fieldBindingFlags = BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance;

            return type.GetFields(fieldBindingFlags);
        }

        /// <summary>
        /// Get all const (static) fields.
        /// </summary>
        /// <param name="type"></param>
        /// <returns>Returns an array of fields.</returns>
        public static FieldInfo[] GetStaticFields(this Type type)
        {
            BindingFlags fieldBindingFlags = BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Static;

            return type.IsStruct() ? type.GetFields(fieldBindingFlags) : Array.Empty<FieldInfo>();
        }

        /// <summary>
        /// Returns true if type has PrimaryKey attribute defined on any of its fields.
        /// </summary>
        /// <param name="type"></param>
        /// <returns>Returns an array of fields.</returns>
        public static bool HasPrimaryKey(this Type type)
        {
            return GetPublicInstanceFields(type).Any(r => r.IsPrimaryKey());
        }

        /// <summary>
        /// Returns true if given type is struct.
        /// </summary>
        /// <param name="type"></param>
        /// <returns></returns>
        public static bool IsStruct(this Type type)
        {
            return type.IsValueType && !type.IsEnum;
        }

        /// <summary>
        /// Returns type full name.
        /// </summary>
        /// <param name="type"></param>
        /// <remarks>Introduced to handle nested types.</remarks>
        /// <returns></returns>
        public static string GetTypeFullName(this Type type)
        {
            if (type.IsNested)
            {
                string fullTypeName = $"{GetTypeFullName(type.DeclaringType)}.{type.Name}";
                return fullTypeName;
            }
            else
            {
                return type.FullName;
            }
        }
    }
}
