#include "Mlos.Core.h"

using namespace Mlos::Core;

namespace Mlos
{
namespace Core
{

//----------------------------------------------------------------------------
// NAME: NamedEvent::Constructor.
//
NamedEvent::NamedEvent() noexcept
{
}

//----------------------------------------------------------------------------
// NAME: NamedEvent::Constructor.
//
// PURPOSE:
//  Move constructor.
//
NamedEvent::NamedEvent(NamedEvent&& namedEvent) noexcept
{
}

_Check_return_
HRESULT NamedEvent::CreateOrOpen(const char* const namedEventName) noexcept
{
    return S_OK;
}

_Check_return_
HRESULT NamedEvent::Open(const char* const namedEventName) noexcept
{
    return S_OK;
}

//----------------------------------------------------------------------------
// NAME: NamedEvent::Destructor.
//
NamedEvent::~NamedEvent()
{
}

void NamedEvent::Signal()
{
}

void NamedEvent::Wait()
{
}

}
}