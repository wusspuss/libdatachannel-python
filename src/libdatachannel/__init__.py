import json
import time
from cffi import FFI
from enum import IntEnum

from enum import Enum
from _libdatachannel_cffi import ffi, lib

class State(Enum):
    NEW=0
    CONNECTING=1
    CONNECTED=2
    DISCONNECTED=3
    FAILED=4
    CLOSED=5

class IceState(Enum):
    ICE_NEW=0
    ICE_CHECKING=1
    ICE_CONNECTED=2
    ICE_COMPLETED=3
    ICE_FAILED=4
    ICE_DISCONNECTED=5
    ICE_CLOSED=6

class GatheringState(Enum):
    GATHERING_NEW=0
    GATHERING_INPROGRESS=1
    GATHERING_COMPLETE=2

class SignalingState(Enum):
    SIGNALING_STABLE=0
    SIGNALING_HAVE_LOCAL_OFFER=1
    SIGNALING_HAVE_REMOTE_OFFER=2
    SIGNALING_HAVE_LOCAL_PRANSWER=3
    SIGNALING_HAVE_REMOTE_PRANSWER=4

class LogLevel(Enum):
    LOG_NONE=0
    LOG_FATAL=1
    LOG_ERROR=2
    LOG_WARNING=3
    LOG_INFO=4
    LOG_DEBUG=5
    LOG_VERBOSE=6

class CertificateType(Enum):
    CERTIFICATE_DEFAULT=0
    CERTIFICATE_ECDSA=1
    CERTIFICATE_RSA=2

class Codec(Enum):
    CODEC_H264=0
    CODEC_VP8=1
    CODEC_VP9=2
    CODEC_H265=3
    CODEC_OPUS=128
    CODEC_PCMU=129
    CODEC_PCMA=130
    CODEC_AAC=131

class Direction(Enum):
    DIRECTION_UNKNOWN=0
    DIRECTION_SENDONLY=1
    DIRECTION_RECVONLY=2
    DIRECTION_SENDRECV=3
    DIRECTION_INACTIVE=4

class TransportPolicy(Enum):
    TRANSPORT_POLICY_ALL=0
    TRANSPORT_POLICY_RELAY=1

class ObuPacketization(Enum):
    OBU_PACKETIZED_OBU=0
    OBU_PACKETIZED_TEMPORAL_UNIT=1

class NalUnitSeparator(Enum):
    NAL_SEPARATOR_LENGTH=0
    NAL_SEPARATOR_LONG_START_SEQUENCE=1
    NAL_SEPARATOR_SHORT_START_SEQUENCE=2
    NAL_SEPARATOR_START_SEQUENCE=3

@ffi.def_extern()
def wrapper_local_description_callback(pc, sdp, type, ptr):
    cb = PeerConnection.assoc[pc].local_description_callback
    cb and cb(ffi.string(sdp), ffi.string(type), )

@ffi.def_extern()
def wrapper_local_candidate_callback(pc, cand, mid, ptr):
    cb = PeerConnection.assoc[pc].local_candidate_callback
    cb and cb(ffi.string(cand), ffi.string(mid), )

@ffi.def_extern()
def wrapper_state_change_callback(pc, state, ptr):
    cb = PeerConnection.assoc[pc].state_change_callback
    cb and cb(State(state), )

@ffi.def_extern()
def wrapper_ice_state_change_callback(pc, state, ptr):
    cb = PeerConnection.assoc[pc].ice_state_change_callback
    cb and cb(IceState(state), )

@ffi.def_extern()
def wrapper_gathering_state_change_callback(pc, state, ptr):
    cb = PeerConnection.assoc[pc].gathering_state_change_callback
    cb and cb(GatheringState(state), )

@ffi.def_extern()
def wrapper_signaling_state_change_callback(pc, state, ptr):
    cb = PeerConnection.assoc[pc].signaling_state_change_callback
    cb and cb(SignalingState(state), )

@ffi.def_extern()
def wrapper_open_callback(id, ptr):
    cb = CommonChannel.assoc[id].open_callback
    cb and cb()

@ffi.def_extern()
def wrapper_closed_callback(id, ptr):
    cb = CommonChannel.assoc[id].closed_callback
    cb and cb()

@ffi.def_extern()
def wrapper_error_callback(id, error, ptr):
    cb = CommonChannel.assoc[id].error_callback
    cb and cb(ffi.string(error), )

@ffi.def_extern()
def wrapper_message_callback(id, message, size, ptr):
    cb = CommonChannel.assoc[id].message_callback
    cb and cb(ffi.string(message), size, )

@ffi.def_extern()
def wrapper_buffered_amount_low_callback(id, ptr):
    cb = CommonChannel.assoc[id].buffered_amount_low_callback
    cb and cb()

@ffi.def_extern()
def wrapper_available_callback(id, ptr):
    cb = CommonChannel.assoc[id].available_callback
    cb and cb()

@ffi.def_extern()
def wrapper_data_channel_callback(pc, dc, ptr):
    cb = PeerConnection.assoc[pc].data_channel_callback
    cb and cb(DataChannel.get_by_id(dc), )

@ffi.def_extern()
def wrapper_track_callback(pc, tr, ptr):
    cb = PeerConnection.assoc[pc].track_callback
    cb and cb(Track.get_by_id(tr), )


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




@ffi.def_extern()
def wrapper_message_callback(id, message, size, ptr):
    cb = CommonChannel.assoc[id].message_callback
    cb and cb(ffi.buffer(message, size), size, )

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
        pass
        lib.rtcSetAvailableCallback(self.id, lib.wrapper_available_callback)
        lib.rtcSetBufferedAmountLowCallback(self.id, lib.wrapper_buffered_amount_low_callback)
        lib.rtcSetClosedCallback(self.id, lib.wrapper_closed_callback)
        lib.rtcSetErrorCallback(self.id, lib.wrapper_error_callback)
        lib.rtcSetMessageCallback(self.id, lib.wrapper_message_callback)
        lib.rtcSetOpenCallback(self.id, lib.wrapper_open_callback)
        self.available_callback = None
        self.buffered_amount_low_callback = None
        self.closed_callback = None
        self.error_callback = None
        self.message_callback = None
        self.open_callback = None
    @classmethod
    def get_by_id(cls, id_):
        return cls.assoc.get(id_) or cls(id_)
    def send_message(self, data, size, ):
        return checkErr(lib.rtcSendMessage, self.id, data, size, )
    def close(self, ):
        return checkErr(lib.rtcClose, self.id, )
    def delete(self, ):
        return checkErr(lib.rtcDelete, self.id, )
    def get_buffered_amount(self, ):
        return checkErr(lib.rtcGetBufferedAmount, self.id, )
    def set_buffered_amount_low_threshold(self, amount, ):
        return checkErr(lib.rtcSetBufferedAmountLowThreshold, self.id, amount, )
    def get_available_amount(self, ):
        return checkErr(lib.rtcGetAvailableAmount, self.id, )
    def set_needs_to_send_rtcp_sr(self, ):
        return checkErr(lib.rtcSetNeedsToSendRtcpSr, self.id, )
    buffered_amount = property(get_buffered_amount, )
    available_amount = property(get_available_amount, )
    

class DataChannel(CommonChannel):
    def __init__(self, pc, name):
        super().__init__(lib.rtcCreateDataChannel(pc.id, name.encode()))
    def delete_data_channel(self, ):
        return checkErr(lib.rtcDeleteDataChannel, self.id, )
    def get_data_channel_stream(self, ):
        return checkErr(lib.rtcGetDataChannelStream, self.id, )
    def get_data_channel_label(self):
        return outString(lib.rtcGetDataChannelLabel, self.id)
    def get_data_channel_protocol(self):
        return outString(lib.rtcGetDataChannelProtocol, self.id)
    data_channel_stream = property(get_data_channel_stream, )
    data_channel_label = property(get_data_channel_label, )
    data_channel_protocol = property(get_data_channel_protocol, )
    

class Track(CommonChannel):
    pass
    def delete_track(self, ):
        return checkErr(lib.rtcDeleteTrack, self.id, )
    def get_track_description(self):
        return outString(lib.rtcGetTrackDescription, self.id)
    def get_track_mid(self):
        return outString(lib.rtcGetTrackMid, self.id)
    def chain_rtcp_sr_reporter(self, ):
        return checkErr(lib.rtcChainRtcpSrReporter, self.id, )
    track_description = property(get_track_description, )
    track_mid = property(get_track_mid, )
    

class PeerConnection:
    # C bindings PeerConnection ids to objects of this class
    assoc = {}
    
    def __init__(self, ice_servers=[]):
        self.conf=ffi.new("rtcConfiguration *")
        # ice_servers
        # ice_servers_bytes_list = [ffi.new("char[]", s.encode("latin1")) for s in ice_servers]
        # ice_servers_pointer = ffi.new("char*[]", ice_servers_bytes_list)
        self.conf.iceServers = ffi.new("char*[]", [ffi.new("char[]", s.encode("latin1")) for s in ice_servers])
        self.conf.iceServersCount = len(ice_servers)
        self.id=lib.rtcCreatePeerConnection(self.conf)
        self.conf=ffi.gc(self.conf, lambda *args: lib.rtcDeletePeerConnection(self.id))
        self.assoc[self.id]=self
        lib.rtcSetDataChannelCallback(self.id, lib.wrapper_data_channel_callback)
        lib.rtcSetGatheringStateChangeCallback(self.id, lib.wrapper_gathering_state_change_callback)
        lib.rtcSetIceStateChangeCallback(self.id, lib.wrapper_ice_state_change_callback)
        lib.rtcSetLocalCandidateCallback(self.id, lib.wrapper_local_candidate_callback)
        lib.rtcSetLocalDescriptionCallback(self.id, lib.wrapper_local_description_callback)
        lib.rtcSetSignalingStateChangeCallback(self.id, lib.wrapper_signaling_state_change_callback)
        lib.rtcSetStateChangeCallback(self.id, lib.wrapper_state_change_callback)
        lib.rtcSetTrackCallback(self.id, lib.wrapper_track_callback)
        self.data_channel_callback = None
        self.gathering_state_change_callback = None
        self.ice_state_change_callback = None
        self.local_candidate_callback = None
        self.local_description_callback = None
        self.signaling_state_change_callback = None
        self.state_change_callback = None
        self.track_callback = None

    def __enter__(self):
        return self

    def __exit__(self,type, value, traceback):
        self.delete()
        
    def delete(self):
        lib.rtcDeletePeerConnection(self.id)
        del self.assoc[self.id]

    def close_peer_connection(self, ):
        return checkErr(lib.rtcClosePeerConnection, self.id, )
    def delete_peer_connection(self, ):
        return checkErr(lib.rtcDeletePeerConnection, self.id, )
    def set_local_description(self, type, ):
        return checkErr(lib.rtcSetLocalDescription, self.id, type, )
    def set_remote_description(self, sdp, type, ):
        return checkErr(lib.rtcSetRemoteDescription, self.id, sdp, type, )
    def add_remote_candidate(self, cand, mid, ):
        return checkErr(lib.rtcAddRemoteCandidate, self.id, cand, mid, )
    def get_local_description(self):
        return outString(lib.rtcGetLocalDescription, self.id)
    def get_remote_description(self):
        return outString(lib.rtcGetRemoteDescription, self.id)
    def get_local_description_type(self):
        return outString(lib.rtcGetLocalDescriptionType, self.id)
    def get_remote_description_type(self):
        return outString(lib.rtcGetRemoteDescriptionType, self.id)
    def get_local_address(self):
        return outString(lib.rtcGetLocalAddress, self.id)
    def get_remote_address(self):
        return outString(lib.rtcGetRemoteAddress, self.id)
    def get_selected_candidate_pair(self, local, localSize, remote, remoteSize, ):
        return checkErr(lib.rtcGetSelectedCandidatePair, self.id, local, localSize, remote, remoteSize, )
    def get_max_data_channel_stream(self, ):
        return checkErr(lib.rtcGetMaxDataChannelStream, self.id, )
    def get_remote_max_message_size(self, ):
        return checkErr(lib.rtcGetRemoteMaxMessageSize, self.id, )
    def create_data_channel(self, label, ):
        return checkErr(lib.rtcCreateDataChannel, self.id, label, )
    def add_track(self, mediaDescriptionSdp, ):
        return checkErr(lib.rtcAddTrack, self.id, mediaDescriptionSdp, )
    local_description = property(get_local_description, set_local_description)
    remote_description = property(get_remote_description, set_remote_description)
    local_description_type = property(get_local_description_type, )
    remote_description_type = property(get_remote_description_type, )
    local_address = property(get_local_address, )
    remote_address = property(get_remote_address, )
    selected_candidate_pair = property(get_selected_candidate_pair, )
    max_data_channel_stream = property(get_max_data_channel_stream, )
    remote_max_message_size = property(get_remote_max_message_size, )
    
    def set_local_description(self, type=ffi.NULL):
        return checkErr(lib.rtcSetLocalDescription, self.id, type, )
    
    # optional arg
    def override_set_remote_description(self, desc):
        self.set_remote_description(desc, ffi.NULL)
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

