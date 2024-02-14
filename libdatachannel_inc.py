import json
import time
from cffi import FFI
from enum import IntEnum
from _libdatachannel_cffi import ffi, lib

threadsafe_scheduler=lambda f, *args: f(*args)

class RtcError(Exception):
    @staticmethod
    def from_code(i):
        return {-1: Invalid, -2: Failure, -3: NotAvail, -4: TooSmall}[i]

class Invalid(RtcError):
    pass

class Failure(RtcError):
    pass

class NotAvail(RtcError):
    pass

class TooSmall(RtcError):
    pass


# {{FFI_BOILERPLATE}}

# {{ENUMS}}

# {{PYTHON_CALLBACK_WRAPPERS}}

@ffi.def_extern()
def wrapper_message_callback(id, message, size, ptr):
    cb = CommonChannel.assoc[id].message_callback
    cb and threadsafe_scheduler(cb, ffi.buffer(message, size), size, )

def checkErr(func, *args, **kwargs):
    i=func(*args, **kwargs)
    if i<0:
        raise RtcError.from_code(i)
    return i

def outString(func, id_):
    """
    for functions like
    int rtcGetLocalDescription(int pc, char *buffer, int size)
    1. call with buffer=NULL to get size
    2. allocate a buffer of that size
    3. call again with that buffer
    4. convert result to Python string
    """
    size = checkErr(func,id_, ffi.NULL, 0)
    buf=ffi.new(f"char[{size}]")
    func(id_, buf, size)
    return ffi.string(buf).decode()


class CommonChannel:
    assoc = {}
    # DataChannel, Track, and WebSocket common API
    def __init__(self, id_):
        self.id=id_
        self.assoc[self.id]=self
# {{ NONE_INITIALIZE_CALLBACKS_COMMON_CHANNEL }}

    def send_message(self, data: bytes):
        return checkErr(lib.rtcSendMessage, self.id, data, len(data))
    

    @classmethod
    def get_by_id(cls, id_):
        return cls.assoc.get(id_) or cls(id_)
# {{METHODS_COMMON_CHANNEL}}

class DataChannel(CommonChannel):
    def __init__(self, pc, name):
        super().__init__(lib.rtcCreateDataChannel(pc.id, name.encode()))
# {{METHODS_DATA_CHANNEL}}

class Track(CommonChannel):
# {{METHODS_TRACK}}
    pass

class PeerConnection:
    # C bindings PeerConnection ids to objects of this class
    assoc = {}
    
    def __init__(self, ice_servers=[]):
        self.conf=ffi.new("rtcConfiguration *")
        self.conf.iceServers = ffi.new("char*[]", [ffi.new("char[]", s.encode("latin1")) for s in ice_servers])
        self.conf.iceServersCount = len(ice_servers)
        self.id=lib.rtcCreatePeerConnection(self.conf)
        self.conf=ffi.gc(self.conf, lambda *args: lib.rtcDeletePeerConnection(self.id))
        self.assoc[self.id]=self
# {{ NONE_INITIALIZE_CALLBACKS_PEER_CONNECTION }}

    @classmethod
    def get_by_id(cls, id_):
        return cls.assoc.get(id_) or cls(id_)
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
        return checkErr(lib.rtcSetRemoteDescription, self.id, desc.encode(), ffi.NULL)
    remote_description=property(get_remote_description, override_set_remote_description)

    _generated_add_track=add_track
    def add_track(self, mediaDescriptionSdp, ):
        return Track(self._generated_add_track(mediaDescriptionSdp))

    def get_selected_candidate_pair(self):
        max_size=checkErr(lib.rtcGetSelectedCandidatePair, self.id, ffi.NULL, 0, ffi.NULL, 0, )
        remote_buf=ffi.new(f"char[{max_size}]")
        local_buf=ffi.new(f"char[{max_size}]")
        checkErr(lib.rtcGetSelectedCandidatePair, self.id, local_buf, max_size, remote_buf, max_size, )
        return ffi.string(local_buf).decode(), ffi.string(remote_buf).decode()
    
def init_logger(level):
    lib.rtcInitLogger(level.value, ffi.NULL)

