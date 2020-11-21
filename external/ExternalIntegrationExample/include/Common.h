//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: Common.h
//
// Purpose:
//  This is supposed to represent a typical header file for an external project.
//
// Notes:
//      <special-instructions>
//
//*********************************************************************

#pragma once

// Existing project includes:
#include <iostream>
#include <string>
#include <future>

// Now we start adding Mlos items:

// Include Mlos.Core shared memory channel APIs.
//
// This also includes the the core message headers code generated from the
// Mlos.NetCore project for registering new assemblies for application specific
// smart components.
//
#include "Mlos.Core.h"

// Include application specific codegen files and sets up the global dispatch table.
//
#include "GlobalDispatchTable.h"

// Include Mlos.Core inline implementations.
//
// Note: This should be included after the application specific code gen
// included in GlobalDispatchTable.h
//
#include "Mlos.Core.inl"
