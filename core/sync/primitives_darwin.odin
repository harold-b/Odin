//+build darwin
//+private
package sync

import "core:c"
import "base:intrinsics"

when ODIN_OS == .Darwin && ODIN_PLATFORM_SUBTARGET == .Default {
	foreign import pthread "system:System.framework"
} else {
	foreign import pthread "system:c"
}

_current_thread_id :: proc "contextless" () -> int {
	tid: u64
	// NOTE(Oskar): available from OSX 10.6 and iOS 3.2.
	// For older versions there is `syscall(SYS_thread_selfid)`, but not really
	// the same thing apparently.
	foreign pthread { pthread_threadid_np :: proc "c" (rawptr, ^u64) -> c.int --- }
	pthread_threadid_np(nil, &tid)
	return int(tid)
}
