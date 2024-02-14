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

class State(IntEnum):
    NEW = 0
    CONNECTING = 1
    CONNECTED = 2
    DISCONNECTED = 3
    FAILED = 4
    CLOSED = 5

class IceState(IntEnum):
    ICE_NEW = 0
    ICE_CHECKING = 1
    ICE_CONNECTED = 2
    ICE_COMPLETED = 3
    ICE_FAILED = 4
    ICE_DISCONNECTED = 5
    ICE_CLOSED = 6

class GatheringState(IntEnum):
    GATHERING_NEW = 0
    GATHERING_INPROGRESS = 1
    GATHERING_COMPLETE = 2

class SignalingState(IntEnum):
    SIGNALING_STABLE = 0
    SIGNALING_HAVE_LOCAL_OFFER = 1
    SIGNALING_HAVE_REMOTE_OFFER = 2
    SIGNALING_HAVE_LOCAL_PRANSWER = 3
    SIGNALING_HAVE_REMOTE_PRANSWER = 4

class LogLevel(IntEnum):
    LOG_NONE = 0
    LOG_FATAL = 1
    LOG_ERROR = 2
    LOG_WARNING = 3
    LOG_INFO = 4
    LOG_DEBUG = 5
    LOG_VERBOSE = 6

class CertificateType(IntEnum):
    CERTIFICATE_DEFAULT = 0
    CERTIFICATE_ECDSA = 1
    CERTIFICATE_RSA = 2

class Codec(IntEnum):
    CODEC_H264 = 0
    CODEC_VP8 = 1
    CODEC_VP9 = 2
    CODEC_H265 = 3
    CODEC_AV1 = 4
    CODEC_OPUS = 128
    CODEC_PCMU = 129
    CODEC_PCMA = 130
    CODEC_AAC = 131

class Direction(IntEnum):
    DIRECTION_UNKNOWN = 0
    DIRECTION_SENDONLY = 1
    DIRECTION_RECVONLY = 2
    DIRECTION_SENDRECV = 3
    DIRECTION_INACTIVE = 4

class TransportPolicy(IntEnum):
    TRANSPORT_POLICY_ALL = 0

class ObuPacketization(IntEnum):
    OBU_PACKETIZED_OBU = 0
    OBU_PACKETIZED_TEMPORAL_UNIT = 1

class NalUnitSeparator(IntEnum):
    NAL_SEPARATOR_LENGTH = 0
    NAL_SEPARATOR_LONG_START_SEQUENCE = 1
    NAL_SEPARATOR_SHORT_START_SEQUENCE = 2
    NAL_SEPARATOR_START_SEQUENCE = 3



@ffi.def_extern()
def wrapper_local_description_callback(pc, sdp, type, ptr):
    cb = PeerConnection.get_by_id(pc).local_description_callback
    cb and threadsafe_scheduler(cb, ffi.string(sdp), ffi.string(type), )

@ffi.def_extern()
def wrapper_local_candidate_callback(pc, cand, mid, ptr):
    cb = PeerConnection.get_by_id(pc).local_candidate_callback
    cb and threadsafe_scheduler(cb, ffi.string(cand), ffi.string(mid), )

@ffi.def_extern()
def wrapper_state_change_callback(pc, state, ptr):
    cb = PeerConnection.get_by_id(pc).state_change_callback
    cb and threadsafe_scheduler(cb, State(state), )

@ffi.def_extern()
def wrapper_ice_state_change_callback(pc, state, ptr):
    cb = PeerConnection.get_by_id(pc).ice_state_change_callback
    cb and threadsafe_scheduler(cb, IceState(state), )

@ffi.def_extern()
def wrapper_gathering_state_change_callback(pc, state, ptr):
    cb = PeerConnection.get_by_id(pc).gathering_state_change_callback
    cb and threadsafe_scheduler(cb, GatheringState(state), )

@ffi.def_extern()
def wrapper_signaling_state_change_callback(pc, state, ptr):
    cb = PeerConnection.get_by_id(pc).signaling_state_change_callback
    cb and threadsafe_scheduler(cb, SignalingState(state), )

@ffi.def_extern()
def wrapper_open_callback(id, ptr):
    cb = CommonChannel.get_by_id(id).open_callback
    cb and threadsafe_scheduler(cb, )

@ffi.def_extern()
def wrapper_closed_callback(id, ptr):
    cb = CommonChannel.get_by_id(id).closed_callback
    cb and threadsafe_scheduler(cb, )

@ffi.def_extern()
def wrapper_error_callback(id, error, ptr):
    cb = CommonChannel.get_by_id(id).error_callback
    cb and threadsafe_scheduler(cb, ffi.string(error), )

@ffi.def_extern()
def wrapper_message_callback(id, message, size, ptr):
    cb = CommonChannel.get_by_id(id).message_callback
    cb and threadsafe_scheduler(cb, ffi.string(message), )

@ffi.def_extern()
def wrapper_buffered_amount_low_callback(id, ptr):
    cb = CommonChannel.get_by_id(id).buffered_amount_low_callback
    cb and threadsafe_scheduler(cb, )

@ffi.def_extern()
def wrapper_available_callback(id, ptr):
    cb = CommonChannel.get_by_id(id).available_callback
    cb and threadsafe_scheduler(cb, )

@ffi.def_extern()
def wrapper_data_channel_callback(pc, dc, ptr):
    cb = PeerConnection.get_by_id(pc).data_channel_callback
    cb and threadsafe_scheduler(cb, DataChannel.get_by_id(dc), )

@ffi.def_extern()
def wrapper_track_callback(pc, tr, ptr):
    cb = PeerConnection.get_by_id(pc).track_callback
    cb and threadsafe_scheduler(cb, Track.get_by_id(tr), )



@ffi.def_extern()
def wrapper_message_callback(id, message, size, ptr):
    cb = CommonChannel.assoc[id].message_callback
    cb and threadsafe_scheduler(cb, ffi.buffer(message, size), )

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
        lib.rtcSetOpenCallback(self.id,lib.wrapper_open_callback)
        self.open_callback=None
        lib.rtcSetClosedCallback(self.id,lib.wrapper_closed_callback)
        self.closed_callback=None
        lib.rtcSetErrorCallback(self.id,lib.wrapper_error_callback)
        self.error_callback=None
        lib.rtcSetMessageCallback(self.id,lib.wrapper_message_callback)
        self.message_callback=None
        lib.rtcSetBufferedAmountLowCallback(self.id,lib.wrapper_buffered_amount_low_callback)
        self.buffered_amount_low_callback=None
        lib.rtcSetAvailableCallback(self.id,lib.wrapper_available_callback)
        self.available_callback=None


    def send_message(self, data: bytes):
        return checkErr(lib.rtcSendMessage, self.id, data, len(data))
    

    @classmethod
    def get_by_id(cls, id_):
        return cls.assoc.get(id_) or cls(id_)
    def close(self, ):
        return checkErr(lib.rtcClose, self.id, )
    def delete(self, ):
        return checkErr(lib.rtcDelete, self.id, )
    def max_message_size(self, ):
        return checkErr(lib.rtcMaxMessageSize, self.id, )
    def get_buffered_amount(self, ):
        return checkErr(lib.rtcGetBufferedAmount, self.id, )
    def set_buffered_amount_low_threshold(self, amount: int):
        return checkErr(lib.rtcSetBufferedAmountLowThreshold, self.id, amount)
    def get_available_amount(self, ):
        return checkErr(lib.rtcGetAvailableAmount, self.id, )
    def set_needs_to_send_rtcp_sr(self, ):
        return checkErr(lib.rtcSetNeedsToSendRtcpSr, self.id, )
    buffered_amount = property(get_buffered_amount)
    available_amount = property(get_available_amount)

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
    data_channel_stream = property(get_data_channel_stream)
    data_channel_label = property(get_data_channel_label)
    data_channel_protocol = property(get_data_channel_protocol)

class Track(CommonChannel):
    def delete_track(self, ):
        return checkErr(lib.rtcDeleteTrack, self.id, )
    def get_track_description(self):
        return outString(lib.rtcGetTrackDescription, self.id)
    def get_track_mid(self):
        return outString(lib.rtcGetTrackMid, self.id)
    def request_keyframe(self, ):
        return checkErr(lib.rtcRequestKeyframe, self.id, )
    def request_bitrate(self, bitrate: int):
        return checkErr(lib.rtcRequestBitrate, self.id, bitrate)
    def chain_rtcp_receiving_session(self, ):
        return checkErr(lib.rtcChainRtcpReceivingSession, self.id, )
    def chain_rtcp_sr_reporter(self, ):
        return checkErr(lib.rtcChainRtcpSrReporter, self.id, )
    def chain_rtcp_nack_responder(self, maxStoredPacketsCount: int):
        return checkErr(lib.rtcChainRtcpNackResponder, self.id, maxStoredPacketsCount)
    track_description = property(get_track_description)
    track_mid = property(get_track_mid)
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
        lib.rtcSetLocalDescriptionCallback(self.id,lib.wrapper_local_description_callback)
        self.local_description_callback=None
        lib.rtcSetLocalCandidateCallback(self.id,lib.wrapper_local_candidate_callback)
        self.local_candidate_callback=None
        lib.rtcSetStateChangeCallback(self.id,lib.wrapper_state_change_callback)
        self.state_change_callback=None
        lib.rtcSetIceStateChangeCallback(self.id,lib.wrapper_ice_state_change_callback)
        self.ice_state_change_callback=None
        lib.rtcSetGatheringStateChangeCallback(self.id,lib.wrapper_gathering_state_change_callback)
        self.gathering_state_change_callback=None
        lib.rtcSetSignalingStateChangeCallback(self.id,lib.wrapper_signaling_state_change_callback)
        self.signaling_state_change_callback=None
        lib.rtcSetDataChannelCallback(self.id,lib.wrapper_data_channel_callback)
        self.data_channel_callback=None
        lib.rtcSetTrackCallback(self.id,lib.wrapper_track_callback)
        self.track_callback=None


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

    def close_peer_connection(self, ):
        return checkErr(lib.rtcClosePeerConnection, self.id, )
    def delete_peer_connection(self, ):
        return checkErr(lib.rtcDeletePeerConnection, self.id, )
    def set_local_description(self, type: str):
        return checkErr(lib.rtcSetLocalDescription, self.id, type.encode())
    def set_remote_description(self, sdp: str, type: str):
        return checkErr(lib.rtcSetRemoteDescription, self.id, sdp.encode(), type.encode())
    def add_remote_candidate(self, cand: str, mid: str):
        return checkErr(lib.rtcAddRemoteCandidate, self.id, cand.encode(), mid.encode())
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
    def get_max_data_channel_stream(self, ):
        return checkErr(lib.rtcGetMaxDataChannelStream, self.id, )
    def get_remote_max_message_size(self, ):
        return checkErr(lib.rtcGetRemoteMaxMessageSize, self.id, )
    def create_data_channel(self, label: str):
        return checkErr(lib.rtcCreateDataChannel, self.id, label.encode())
    def add_track(self, mediaDescriptionSdp: str):
        return checkErr(lib.rtcAddTrack, self.id, mediaDescriptionSdp.encode())
    local_description = property(get_local_description)
    remote_description = property(get_remote_description)
    local_description_type = property(get_local_description_type)
    remote_description_type = property(get_remote_description_type)
    local_address = property(get_local_address)
    remote_address = property(get_remote_address)
    max_data_channel_stream = property(get_max_data_channel_stream)
    remote_max_message_size = property(get_remote_max_message_size)
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

