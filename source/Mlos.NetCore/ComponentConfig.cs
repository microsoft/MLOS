// -----------------------------------------------------------------------
// <copyright file="ComponentConfig.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System.Runtime.CompilerServices;

namespace Mlos.Core
{
    public static class ComponentConfig
    {
        /// <summary>
        /// Create component config.
        /// </summary>
        /// <typeparam name="TType">Codegen type.</typeparam>
        /// <typeparam name="TProxy">Proxy type.</typeparam>
        /// <param name="config"></param>
        /// <returns></returns>
        /// <remarks>
        /// Use codegen interface type information to infer required types.
        /// </remarks>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static ComponentConfig<TType, TProxy> Create<TType, TProxy>(ICodegenType<TType, TProxy> config)
            where TType : ICodegenType<TType, TProxy>, new()
            where TProxy : ICodegenProxy<TType, TProxy>, new()
        {
            return new ComponentConfig<TType, TProxy>((TType)config);
        }
    }

    /// <summary>
    /// Component configuration.
    /// </summary>
    /// <typeparam name="TType">Codegen type.</typeparam>
    /// <typeparam name="TProxy">Proxy type of the configuration.</typeparam>
    public class ComponentConfig<TType, TProxy>
        where TType : ICodegenType, new()
        where TProxy : ICodegenProxy<TType, TProxy>, new()
    {
        /// <summary>
        /// Initializes a new instance of the <see cref="ComponentConfig{TType, TProxy}"/> class.
        /// </summary>
        public ComponentConfig()
        {
            sharedConfig = default;
            Config = new TType();
        }

        /// <summary>
        /// Initializes a new instance of the <see cref="ComponentConfig{TType, TProxy}"/> class.
        /// </summary>
        /// <param name="config"></param>
        public ComponentConfig(TType config)
        {
            sharedConfig = default;
            Config = config;
        }

        /// <summary>
        /// Compare local ComponentConfig with the shared memory configuration.
        /// </summary>
        /// <param name="sharedConfig"></param>
        /// <returns></returns>
        public bool Compare(SharedConfig<TProxy> sharedConfig)
        {
            ICodegenType codegenType = Config;

            // First compare the codegen type, only if matches compare the objects.
            //
            return sharedConfig.Header.CodegenTypeIndex == codegenType.CodegenTypeIndex()
                && codegenType.CompareKey(sharedConfig.Config);
        }

        public void Assign(SharedConfig<TProxy> sharedConfig)
        {
            this.sharedConfig = sharedConfig;
        }

        public void Update()
        {
            uint configId = sharedConfig.Header.ConfigId.LoadRelaxed();

            Config.Update(sharedConfig.Config);
        }

        /// <summary>
        /// Component configuration.
        /// </summary>
        public TType Config;

        /// <summary>
        /// Shared configuration.
        /// </summary>
        private SharedConfig<TProxy> sharedConfig;
    }
}
