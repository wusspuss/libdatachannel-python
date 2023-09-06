import json
import time
from cffi import FFI
from codegen import *
from enum import IntEnum

# {{FFI_BOILERPLATE}}

def checkErr(func, *args, **kwargs):
    i=func(*args, **kwargs)
    if i<0:
        raise RtcError.from_code(i)
    return i

def outString(func, id_):
    size = checkErr(func,id_, ffi.NULL, 0)

    # if size < 0:
    #     raise ValueError(RtcReturn(size))
    buf=ffi.new(f"char[{size}]")
    func(id_, buf, size)
    return ffi.string(buf).decode()
    
class CommonChannel:
    assoc = {}
    
    # DataChannel, Track, and WebSocket common API
    def __init__(self, id_):
        self.id=id_
        pass
        # {{ NONE_INITIALIZE_CALLBACKS_COMMON_CHANNEL }}

    # {{METHODS_COMMON_CHANNEL}}

class DataChannel(CommonChannel):
    assoc = {}
    def __init__(self, pc, name):
        super().__init__(lib.rtcCreateDataChannel(pc.id, name.encode()))
        self.assoc[self.id]=self
        
    # {{METHODS_DATA_CHANNEL}}
    
class PeerConnection:
    # C bindings PeerConnection ids to objects of this class
    assoc = {}
    
    def __init__(self):
        self.conf=ffi.new("rtcConfiguration *")
        self.id=lib.rtcCreatePeerConnection(self.conf)
        print("Created peerconn:", self.id)
        self.conf=ffi.gc(self.conf, lambda: print(123) and lib.rtcDeletePeerConnection(self.id))
        self.assoc[self.id]=self
        # {{ NONE_INITIALIZE_CALLBACKS_PEER_CONNECTION }}

    def __enter__(self):
        return self

    def __exit__(self,type, value, traceback):
        self.delete()
        
    def delete(self):
        lib.rtcDeletePeerConnection(self.id)
        del self.assoc[self.id]

    # {{METHODS_PEER_CONNECTION}}
    def set_local_description(self, type=ffi.NULL):
        return checkErr(lib.rtcSetLocalDescription, self.id, type, )
    
    # optional arg
    def override_set_remote_description(self, desc):
        self.set_remote_description(desc, ffi.NULL)
    remote_description=property(get_remote_description, override_set_remote_description)
    
def init_logger(level):
    lib.rtcInitLogger(level.value, ffi.NULL)

