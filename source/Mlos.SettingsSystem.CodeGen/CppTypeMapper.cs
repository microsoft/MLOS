// -----------------------------------------------------------------------
// <copyright file="CppTypeMapper.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Collections.Generic;
using System.Reflection;

using Mlos.SettingsSystem.Attributes;
using Mlos.SettingsSystem.StdTypes;

namespace Mlos.SettingsSystem.CodeGen
{
    /// <summary>
    /// Maintains mapping of CSharp types encountered to C++ types generated.
    /// </summary>
    internal static class CppTypeMapper
    {
        /// <summary>
        /// Mapping of CSharp types to Cpp types.
        /// </summary>
        private static readonly Dictionary<Type, CppType?> CppTypeMapping = new Dictionary<Type, CppType?>
        {
            { typeof(bool), new CppType { Name = "bool", TypeSize = 1, ProxyTypeName = "::Mlos::Core::PropertyProxy<volatile bool>" } },
            { typeof(char), new CppType { Name = "char", TypeSize = 1, ProxyTypeName = "::Mlos::Core::PropertyProxy<volatile char>" } },
            { typeof(short), new CppType { Name = "int16_t", TypeSize = 2, Alignment = 2, ProxyTypeName = "::Mlos::Core::PropertyProxy<volatile int16_t>" } },
            { typeof(ushort), new CppType { Name = "uint16_t", TypeSize = 2, Alignment = 2, ProxyTypeName = "::Mlos::Core::PropertyProxy<volatile uint16_t>" } },
            { typeof(int), new CppType { Name = "int32_t", TypeSize = 4, Alignment = 4, ProxyTypeName = "::Mlos::Core::PropertyProxy<volatile int32_t>" } },
            { typeof(uint), new CppType { Name = "uint32_t", TypeSize = 4, Alignment = 4, ProxyTypeName = "::Mlos::Core::PropertyProxy<volatile uint32_t>" } },
            { typeof(long), new CppType { Name = "int64_t", TypeSize = 8, Alignment = 8, ProxyTypeName = "::Mlos::Core::PropertyProxy<volatile int64_t>" } },
            { typeof(ulong), new CppType { Name = "uint64_t", TypeSize = 8, Alignment = 8, ProxyTypeName = "::Mlos::Core::PropertyProxy<volatile uint64_t>" } },
            { typeof(float), new CppType { Name = "float", TypeSize = 4, Alignment = 4 } },
            { typeof(double), new CppType { Name = "double", TypeSize = 8, Alignment = 8 } },
            { typeof(string), new CppType { Name = "std::wstring_view", TypeSize = 16, Alignment = 8, ProxyTypeName = "::Mlos::Core::PropertyProxy<std::wstring_view>", HasVariableData = true } },
            { typeof(StringPtr), new CppType { Name = "::Mlos::Core::StringPtr", TypeSize = 16, Alignment = 8, ProxyTypeName = "::Mlos::Core::PropertyProxy<::Mlos::Core::StringPtr>", IsCodegenType = true, HasVariableData = true } },
            { typeof(WideStringPtr), new CppType { Name = "::Mlos::Core::WideStringPtr", TypeSize = 16, Alignment = 8, ProxyTypeName = "::Mlos::Core::PropertyProxy<::Mlos::Core::WideStringPtr>", IsCodegenType = true, HasVariableData = true } },
            { typeof(StringView), new CppType { Name = "std::string_view", TypeSize = 16, Alignment = 8, ProxyTypeName = "::Mlos::Core::PropertyProxy<std::string_view>", IsCodegenType = true, HasVariableData = true } },
            { typeof(WideStringView), new CppType { Name = "std::wstring_view", TypeSize = 16, Alignment = 8, ProxyTypeName = "::Mlos::Core::PropertyProxy<std::wstring_view>", IsCodegenType = true, HasVariableData = true } },
            { typeof(AtomicBool), new CppType { Name = "std::atomic<bool>", TypeSize = 1, ProxyTypeName = "::Mlos::Core::PropertyProxy<std::atomic_bool>", IsCodegenType = true } },
            { typeof(AtomicInt32), new CppType { Name = "std::atomic<int32_t>", TypeSize = 4, Alignment = 4, ProxyTypeName = "::Mlos::Core::PropertyProxy<std::atomic<int32_t>>", IsCodegenType = true } },
            { typeof(AtomicUInt32), new CppType { Name = "std::atomic<uint32_t>", TypeSize = 4, Alignment = 4, ProxyTypeName = "::Mlos::Core::PropertyProxy<std::atomic<uint32_t>>", IsCodegenType = true } },
            { typeof(AtomicInt64), new CppType { Name = "std::atomic<int64_t>", TypeSize = 8, Alignment = 8, ProxyTypeName = "::Mlos::Core::PropertyProxy<std::atomic<int64_t>>", IsCodegenType = true } },
            { typeof(AtomicUInt64), new CppType { Name = "std::atomic<uint64_t>", TypeSize = 8, Alignment = 8, ProxyTypeName = "::Mlos::Core::PropertyProxy<std::atomic<uint64_t>>", IsCodegenType = true } },
        };

        /// <summary>
        /// Try get a Cpp type for given CSharp type.
        /// </summary>
        /// <param name="type"></param>
        /// <param name="cppType"></param>
        /// <returns></returns>
        public static bool TryGetCppType(Type type, out CppType cppType)
        {
            CppTypeMapping.TryGetValue(type, out CppType? nullableCppType);
            if (nullableCppType.HasValue)
            {
                cppType = nullableCppType.Value;
                return true;
            }

            cppType = default;
            return false;
        }

        /// <summary>
        /// Declare the type. From now on, CodeGen is aware that the type has been declared, but has not yet been defined.
        /// </summary>
        /// <param name="sourceType"></param>
        internal static void DeclareType(Type sourceType) => CppTypeMapping[sourceType] = null;

        /// <summary>
        /// Try get a Cpp type for given CSharp type.
        /// </summary>
        /// <param name="sourceType"></param>
        /// <returns></returns>
        public static CppType GetCppType(Type sourceType)
        {
            if (!CppTypeMapping.TryGetValue(sourceType, out CppType? cppType))
            {
                // There is no Cpp type, we run into code gen issue.
                //
                throw new InvalidOperationException($"Unable to locate cpp type for '{sourceType}' type.");
            }

            return cppType.Value;
        }

        /// <summary>
        /// Do we have corresponding Cpp type.
        /// </summary>
        /// <param name="type"></param>
        /// <returns></returns>
        public static bool HasCppType(Type type) => CppTypeMapping.ContainsKey(type);

        /// <summary>
        /// Gets fully qualified cpp type name.
        /// </summary>
        /// <param name="sourceType"></param>
        /// <returns></returns>
        internal static string GetCppFullTypeName(Type sourceType) => GetCppType(sourceType).Name;

        /// <summary>
        /// Get a fully qualified proxy type name to a cpp type.
        /// </summary>
        /// <param name="sourceType"></param>
        /// <returns></returns>
        public static string GetCppProxyFullTypeName(Type sourceType)
        {
            CppType cppType = GetCppType(sourceType);

            // Proxy always exposes internal fields as proxy types.
            //
            if (cppType.HasDefinedProxy)
            {
                // Type has explicitly defined a proxy type.
                //
                return cppType.ProxyTypeName;
            }
            else if (!IsShareable(sourceType))
            {
                // Primitive types need to be wrapped using ProperyProxy.
                //
                string cppTypeFullName = cppType.Name;

                return $"::Mlos::Core::PropertyProxy<{cppTypeFullName}>";
            }
            else
            {
                // For non-primitive types, use the generated proxy type.
                //
                return $"::Proxy{cppType.Name}";
            }
        }

        /// <summary>
        /// Define a new type.
        /// </summary>
        /// <param name="sourceType">CSharp type.</param>
        /// <param name="cppTypeSize">Size of the generated structure.</param>
        /// <param name="aligment">Type aligment.</param>
        /// <param name="paddingSize">Padding size required to match declared size.</param>
        /// <param name="hasVariableSerializableLength">True is serialized type has variable length, type contains dynamic types.</param>
        public static void DefineType(Type sourceType, uint cppTypeSize, uint aligment, uint paddingSize, bool hasVariableSerializableLength)
        {
            if (!CppTypeMapping.ContainsKey(sourceType))
            {
                throw new InvalidOperationException("Type {type} should be declared.");
            }

            // Calculate codegen type hash value, so it can be used by the codegen writes.
            //
            TypeMetadataMapper.ComputeAndStoreHash(sourceType);

            CppTypeMapping[sourceType] = new CppType
            {
                Name = GenerateCppFullTypeName(sourceType),
                TypeSize = cppTypeSize,
                Alignment = aligment,
                PaddingSize = paddingSize,
                HasVariableData = hasVariableSerializableLength,
                IsCodegenType = sourceType.IsCodegenType(),
            };
        }

        /// <summary>
        /// Construct a fully qualified cpp type name.
        /// </summary>
        /// <param name="type"></param>
        /// <returns></returns>
        public static string GenerateCppFullTypeName(Type type)
        {
            string cppNamespace = string.Join("::", type.Namespace.Split('.'));

            return $"::{cppNamespace}::{type.Name}";
        }

        /// <summary>
        /// Create a field name from fullly qualified cpp type name.
        /// </summary>
        /// <param name="type"></param>
        /// <returns></returns>
        public static string GenerateFieldNameFromCppFullTypeName(Type type)
        {
            string cppNamespace = string.Join("_", type.Namespace.Split('.'));

            return $"{cppNamespace}_{type.Name}";
        }

        /// <summary>
        /// Checks if type has generated a proxy class.
        /// </summary>
        /// <param name="sourceType"></param>
        /// <returns>True for all non primitive types.</returns>
        public static bool IsShareable(Type sourceType) => GetCppType(sourceType).IsCodegenType;

        /// <summary>
        /// Align provided size.
        /// </summary>
        /// <param name="size"></param>
        /// <param name="alignment"></param>
        /// <returns></returns>
        public static uint AlignSize(uint size, uint alignment) => ((size + alignment - 1) / alignment) * alignment;
    }

    /// <summary>
    /// Describes the Cpp structure.
    /// </summary>
    internal struct CppType
    {
        /// <summary>
        /// The name of the Cpp type.
        /// </summary>
        internal string Name;

        /// <summary>
        /// The size in bytes of the Cpp type.
        /// </summary>
        /// <remarks>
        /// The size does not include length of the variable fields data (strings).
        /// For variable field TypeSize will include size of the data holder (uint64_t for data offset and uint64_t for the data length).
        /// </remarks>
        internal uint TypeSize;

        /// <summary>
        /// Aligment.
        /// </summary>
        internal uint Alignment;

        /// <summary>
        /// The size of padding required if codegen type has declared size.
        /// </summary>
        internal uint PaddingSize;

        /// <summary>
        /// Optional name of the proxy type.
        /// </summary>
        internal string ProxyTypeName;

        /// <summary>
        /// If true type contains variable size data (strings).
        /// </summary>
        internal bool HasVariableData;

        /// <summary>
        /// True if a type has a CodegenType attribute.
        /// </summary>
        internal bool IsCodegenType;

        /// <summary>
        /// Gets a value indicating whether if a type has defined a proxy class.
        /// </summary>
        internal bool HasDefinedProxy => !string.IsNullOrEmpty(ProxyTypeName);
    }

    /// <summary>
    /// Structure describing a field of Cpp structure.
    /// </summary>
    internal struct CppField
    {
        /// <summary>
        /// Offset in flatten Cpp structure.
        /// </summary>
        internal uint CppStructOffset;

        /// <summary>
        /// CSharp field info.
        /// </summary>
        internal FieldInfo FieldInfo;

        /// <summary>
        /// The Cpp type info for the field.
        /// </summary>
        internal CppType CppType;
    }
}
