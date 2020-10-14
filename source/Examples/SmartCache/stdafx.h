//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: stdafx.h
//
// Purpose:
//  This is the standard include header, expected to be in every compilation unit
//  in this project.
//
// Notes:
//  It is generally not expected to change much, so precompiled headers can be
//  made use of to help optimize builds if desired.
//
//*********************************************************************

#pragma once

// Include standard libraries necessary for all compilation units.
//
#include <array>
#include <condition_variable>
#include <iostream>
#include <functional>
#include <future>
#include <memory>
#include <mutex>
#include <list>
#include <unordered_map>

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

// Macros.
//
#define UNUSED(x) (void)x

using namespace Mlos::Core;
