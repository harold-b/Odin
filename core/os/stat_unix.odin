#+build linux, darwin, freebsd, openbsd, netbsd, haiku
package os

import "core:time"

/*
For reference
-------------

Unix_File_Time :: struct {
	seconds:     i64,
	nanoseconds: i64,
}

Stat :: struct {
	device_id:     u64, // ID of device containing file
	serial:        u64, // File serial number
	nlink:         u64, // Number of hard links
	mode:          u32, // Mode of the file
	uid:           u32, // User ID of the file's owner
	gid:           u32, // Group ID of the file's group
	_padding:      i32, // 32 bits of padding
	rdev:          u64, // Device ID, if device
	size:          i64, // Size of the file, in bytes
	block_size:    i64, // Optimal bllocksize for I/O
	blocks:        i64, // Number of 512-byte blocks allocated

	last_access:   Unix_File_Time, // Time of last access
	modified:      Unix_File_Time, // Time of last modification
	status_change: Unix_File_Time, // Time of last status change

	_reserve1,
	_reserve2,
	_reserve3:     i64,
};

Time :: struct {
	_nsec: i64, // zero is 1970-01-01 00:00:00
}

File_Info :: struct {
	fullpath: string,
	name:     string,
	size:     i64,
	mode:     File_Mode,
	is_dir:   bool,
	creation_time:     time.Time,
	modification_time: time.Time,
	access_time:       time.Time,
}
*/

@(private, require_results)
_make_time_from_unix_file_time :: proc(uft: Unix_File_Time) -> time.Time {
	return time.Time{
		_nsec = i64(uft.nanoseconds) + i64(uft.seconds) * 1_000_000_000,
	}
}

@(private)
_fill_file_info_from_stat :: proc(fi: ^File_Info, s: OS_Stat) {
	fi.size = s.size
	fi.mode = cast(File_Mode)s.mode
	fi.is_dir = S_ISDIR(s.mode)

	// NOTE(laleksic, 2021-01-21): Not really creation time, but closest we can get (maybe better to leave it 0?)
	fi.creation_time = _make_time_from_unix_file_time(s.status_change)

	fi.modification_time = _make_time_from_unix_file_time(s.modified)
	fi.access_time = _make_time_from_unix_file_time(s.last_access)
}


@(private, require_results)
path_base :: proc(path: string) -> string {
	is_separator :: proc(c: byte) -> bool {
		return c == '/'
	}

	if path == "" {
		return "."
	}

	path := path
	for len(path) > 0 && is_separator(path[len(path)-1]) {
		path = path[:len(path)-1]
	}

	i := len(path)-1
	for i >= 0 && !is_separator(path[i]) {
		i -= 1
	}
	if i >= 0 {
		path = path[i+1:]
	}
	if path == "" {
		return "/"
	}
	return path
}


@(require_results)
lstat :: proc(name: string, allocator := context.allocator) -> (fi: File_Info, err: Error) {
	context.allocator = allocator

	s := _lstat(name) or_return
	_fill_file_info_from_stat(&fi, s)
	fi.fullpath = absolute_path_from_relative(name) or_return
	fi.name = path_base(fi.fullpath)
	return
}

@(require_results)
stat :: proc(name: string, allocator := context.allocator) -> (fi: File_Info, err: Error) {
	context.allocator = allocator

	s := _stat(name) or_return
	_fill_file_info_from_stat(&fi, s)
	fi.fullpath = absolute_path_from_relative(name) or_return
	fi.name = path_base(fi.fullpath)
	return
}

@(require_results)
fstat :: proc(fd: Handle, allocator := context.allocator) -> (fi: File_Info, err: Error) {
	context.allocator = allocator

	s := _fstat(fd) or_return
	_fill_file_info_from_stat(&fi, s)
	fi.fullpath = absolute_path_from_handle(fd) or_return
	fi.name = path_base(fi.fullpath)
	return
}
