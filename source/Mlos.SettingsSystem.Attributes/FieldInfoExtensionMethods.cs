// -----------------------------------------------------------------------
// <copyright file="FieldInfoExtensionMethods.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System.Linq;
using System.Reflection;

namespace Mlos.SettingsSystem.Attributes
{
    /// <summary>
    /// Set of public FieldInfo extension methods.
    /// </summary>
    public static class FieldInfoExtensionMethods
    {
        /// <summary>
        /// Check if the field is a string.
        /// </summary>
        /// <param name="fieldInfo"></param>
        /// <returns></returns>
        public static bool IsString(this FieldInfo fieldInfo)
        {
            return fieldInfo != null
                && fieldInfo.FieldType == typeof(string);
        }

        /// <summary>
        /// Check if the given type is a simple (scalar) Mlos Setting (e.g. in a SettingsRegistry).
        /// </summary>
        /// <param name="fieldInfo"></param>
        /// <returns></returns>
        public static bool IsScalarSetting(this FieldInfo fieldInfo)
        {
            return fieldInfo != null
                && fieldInfo.GetCustomAttributes(typeof(ScalarSettingAttribute), true).Any();
        }

        /// <summary>
        /// Check if given field is a fixed length array.
        /// </summary>
        /// <param name="fieldInfo"></param>
        /// <returns></returns>
        /// <remarks>
        /// We expect an attribute.
        /// </remarks>
        public static bool IsFixedSizedArray(this FieldInfo fieldInfo)
        {
            return fieldInfo != null
                && fieldInfo.FieldType.IsArray
                && fieldInfo.GetCustomAttribute<FixedSizeArrayAttribute>() != null;
        }

        /// <summary>
        /// Check if given field is part of the primary key.
        /// </summary>
        /// <param name="fieldInfo"></param>
        /// <returns></returns>
        public static bool IsPrimaryKey(this FieldInfo fieldInfo)
        {
            return fieldInfo != null
                && fieldInfo.GetCustomAttributes<ScalarSettingAttribute>().Any(r => r.IsPrimaryKey);
        }
    }
}
