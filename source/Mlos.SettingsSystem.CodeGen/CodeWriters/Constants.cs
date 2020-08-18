// -----------------------------------------------------------------------
// <copyright file="Constants.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

namespace Mlos.SettingsSystem.CodeGen.CodeWriters
{
    /// <summary>
    /// A class to stash various constants.
    /// </summary>
    internal static class Constants
    {
        /// <summary>
        /// The namespace ObjectDeserializationCallback code is generated to.
        /// </summary>
        public const string ObjectDeserializationCallbackNamespace = "ObjectDeserializationCallback";

        /// <summary>
        /// The namespace ObjectSerilization code is generated to.
        /// </summary>
        public const string ObjectSerializationNamespace = "ObjectSerialization";

        /// <summary>
        /// The namespace Proxy code is generated into.
        /// </summary>
        public const string ProxyNamespace = "Proxy";

        /// <summary>
        /// The namespace TypeMetadataInfo code is generated to.
        /// </summary>
        public const string TypeMetadataInfoNamespace = "TypeMetadataInfo";

        /// <summary>
        /// ObjectDeserializationHandler namespace (Cpp) or static class (CSharp).
        /// </summary>
        public const string ObjectDeserializationHandler = "ObjectDeserializationHandler";
    }
}
