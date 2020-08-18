// Exchange protocol based on circular buffer
//  More details in: Doc\CircularBuffer.md
//
#include "Mlos.Core.h"

namespace Mlos
{
namespace Core
{
//----------------------------------------------------------------------------
// NAME: SignalFrameIsReady
//
// PURPOSE:
//  Signals readers that the frame is available to process.
//
// RETURNS:
//
// NOTES:
//
void SignalFrameIsReady(FrameHeader& frame, int32_t frameLength)
{
    frame.Length.store(frameLength, std::memory_order_release);
}

//----------------------------------------------------------------------------
// NAME: SignalFrameForCleanup
//
// PURPOSE:
//  Notify the cleanup thread, that the frame has been processed.
//
// RETURNS:
//  Nothing.
//
// NOTES:
//  Reader function.
//
void SignalFrameForCleanup(FrameHeader& frame, int32_t frameLength)
{
    frame.Length.store(-frameLength, std::memory_order_release);
}
}
}