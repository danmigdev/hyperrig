"""Host-file publication and monitoring; never issues a device command.

Readers share READ/WRITE/DELETE and close promptly. Legacy Windows rename
can still wait for an existing read handle; a bounded retry covers only the
local rename, never a hardware
operation that preceded/follows the journal update.
"""
from __future__ import annotations

import argparse
import ctypes as c
import json
import os
from pathlib import Path
import time


def atomic_write_json(path, value, *, attempts=20, delay=.025):
    if type(attempts) is not int or not 1 <= attempts <= 40 or not 0 <= delay <= .1:
        raise ValueError('bounded local publication retry required')
    path=Path(path)
    temporary=path.with_suffix(path.suffix+'.tmp')
    encoded=json.dumps(value,indent=2)+'\n'
    with temporary.open('w',encoding='utf-8',newline='\n') as stream:
        stream.write(encoded);stream.flush();os.fsync(stream.fileno())
    for attempt in range(1,attempts+1):
        try:
            os.replace(temporary,path)
            return {'replace_attempts':attempt,'device_commands_retried':False}
        except PermissionError as error:
            if getattr(error,'winerror',None) not in (None,5,32,33) or attempt==attempts:
                raise
            time.sleep(delay)


def read_shared_bytes(path, *, maximum=8*1024*1024):
    path=Path(path).resolve()
    if os.name!='nt':
        data=path.read_bytes()
        if len(data)>maximum:raise ValueError('snapshot exceeds read bound')
        return data
    from ctypes import wintypes as w
    kernel=c.WinDLL('kernel32',use_last_error=True)
    kernel.CreateFileW.argtypes=[w.LPCWSTR,w.DWORD,w.DWORD,c.c_void_p,w.DWORD,w.DWORD,w.HANDLE]
    kernel.CreateFileW.restype=w.HANDLE
    kernel.ReadFile.argtypes=[w.HANDLE,c.c_void_p,w.DWORD,c.POINTER(w.DWORD),c.c_void_p]
    kernel.ReadFile.restype=w.BOOL
    kernel.GetFileSizeEx.argtypes=[w.HANDLE,c.POINTER(c.c_int64)]
    kernel.GetFileSizeEx.restype=w.BOOL
    kernel.CloseHandle.argtypes=[w.HANDLE];kernel.CloseHandle.restype=w.BOOL
    # GENERIC_READ; FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE.
    handle=kernel.CreateFileW(str(path),0x80000000,7,None,3,0,None)
    if handle==c.c_void_p(-1).value:raise OSError(c.get_last_error(),'cannot open shared snapshot')
    try:
        length=c.c_int64()
        if not kernel.GetFileSizeEx(handle,c.byref(length)):raise OSError(c.get_last_error(),'cannot size snapshot')
        if not 0<=length.value<=maximum:raise ValueError('snapshot exceeds read bound')
        chunks=[];remaining=length.value
        while remaining:
            size=min(65536,remaining);data=(c.c_ubyte*size)();read=w.DWORD()
            if not kernel.ReadFile(handle,c.byref(data),size,c.byref(read),None):
                raise OSError(c.get_last_error(),'cannot read snapshot')
            if not read.value or read.value>size:raise OSError('snapshot read extent changed')
            chunks.append(bytes(data[:read.value]));remaining-=read.value
        return b''.join(chunks)
    finally:kernel.CloseHandle(handle)


def read_shared_json(path):return json.loads(read_shared_bytes(path).decode('utf-8-sig'))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path',type=Path)
    parser.add_argument('--fields',nargs='+')
    args=parser.parse_args();value=read_shared_json(args.path)
    if args.fields:value={key:value.get(key) for key in args.fields}
    print(json.dumps(value,indent=2))

if __name__=='__main__':main()
