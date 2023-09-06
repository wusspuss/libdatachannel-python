import json
import time
from cffi import FFI
from codegen import *
from enum import IntEnum

from enum import IntEnum
from cffi import FFI
ffibuilder = FFI()
ffibuilder.cdef('''
typedef enum {
	RTC_NEW = 0,
	RTC_CONNECTING = 1,
	RTC_CONNECTED = 2,
	RTC_DISCONNECTED = 3,
	RTC_FAILED = 4,
	RTC_CLOSED = 5
} rtcState;

typedef enum {
	RTC_GATHERING_NEW = 0,
	RTC_GATHERING_INPROGRESS = 1,
	RTC_GATHERING_COMPLETE = 2
} rtcGatheringState;

typedef enum {
	RTC_SIGNALING_STABLE = 0,
	RTC_SIGNALING_HAVE_LOCAL_OFFER = 1,
	RTC_SIGNALING_HAVE_REMOTE_OFFER = 2,
	RTC_SIGNALING_HAVE_LOCAL_PRANSWER = 3,
	RTC_SIGNALING_HAVE_REMOTE_PRANSWER = 4,
} rtcSignalingState;

typedef enum { // Don't change, it must match plog severity
	RTC_LOG_NONE = 0,
	RTC_LOG_FATAL = 1,
	RTC_LOG_ERROR = 2,
	RTC_LOG_WARNING = 3,
	RTC_LOG_INFO = 4,
	RTC_LOG_DEBUG = 5,
	RTC_LOG_VERBOSE = 6
} rtcLogLevel;

typedef enum {
	RTC_CERTIFICATE_DEFAULT = 0, // ECDSA
	RTC_CERTIFICATE_ECDSA = 1,
	RTC_CERTIFICATE_RSA = 2,
} rtcCertificateType;

typedef enum {
	// video
	RTC_CODEC_H264 = 0,
	RTC_CODEC_VP8 = 1,
	RTC_CODEC_VP9 = 2,

	// audio
	RTC_CODEC_OPUS = 128,
    RTC_CODEC_PCMU = 129,
    RTC_CODEC_PCMA = 130
} rtcCodec;

typedef enum {
	RTC_DIRECTION_UNKNOWN = 0,
	RTC_DIRECTION_SENDONLY = 1,
	RTC_DIRECTION_RECVONLY = 2,
	RTC_DIRECTION_SENDRECV = 3,
	RTC_DIRECTION_INACTIVE = 4
} rtcDirection;

typedef enum { RTC_TRANSPORT_POLICY_ALL = 0, RTC_TRANSPORT_POLICY_RELAY = 1 } rtcTransportPolicy;

#define RTC_ERR_SUCCESS 0
#define RTC_ERR_INVALID -1   // invalid argument
#define RTC_ERR_FAILURE -2   // runtime error
#define RTC_ERR_NOT_AVAIL -3 // element not available
#define RTC_ERR_TOO_SMALL -4 // buffer too small

typedef void(*rtcLogCallbackFunc)(rtcLogLevel level, const char *message);
typedef void(*rtcDescriptionCallbackFunc)(int pc, const char *sdp, const char *type,
                                                  void *ptr);
typedef void(*rtcCandidateCallbackFunc)(int pc, const char *cand, const char *mid,
                                                void *ptr);
typedef void(*rtcStateChangeCallbackFunc)(int pc, rtcState state, void *ptr);
typedef void(*rtcGatheringStateCallbackFunc)(int pc, rtcGatheringState state, void *ptr);
typedef void(*rtcSignalingStateCallbackFunc)(int pc, rtcSignalingState state, void *ptr);
typedef void(*rtcDataChannelCallbackFunc)(int pc, int dc, void *ptr);
typedef void(*rtcTrackCallbackFunc)(int pc, int tr, void *ptr);
typedef void(*rtcOpenCallbackFunc)(int id, void *ptr);
typedef void(*rtcClosedCallbackFunc)(int id, void *ptr);
typedef void(*rtcErrorCallbackFunc)(int id, const char *error, void *ptr);
typedef void(*rtcMessageCallbackFunc)(int id, const char *message, int size, void *ptr);
typedef void(*rtcBufferedAmountLowCallbackFunc)(int id, void *ptr);
typedef void(*rtcAvailableCallbackFunc)(int id, void *ptr);

// Log

// NULL cb on the first call will log to stdout
void rtcInitLogger(rtcLogLevel level, rtcLogCallbackFunc cb);

// User pointer
void rtcSetUserPointer(int id, void *ptr);
void *rtcGetUserPointer(int i);

// PeerConnection

typedef struct {
	const char **iceServers;
	int iceServersCount;
	const char *proxyServer; // libnice only
	const char *bindAddress; // libjuice only, NULL means any
	rtcCertificateType certificateType;
	rtcTransportPolicy iceTransportPolicy;
	bool enableIceTcp;    // libnice only
	bool enableIceUdpMux; // libjuice only
	bool disableAutoNegotiation;
	bool forceMediaTransport;
	uint16_t portRangeBegin; // 0 means automatic
	uint16_t portRangeEnd;   // 0 means automatic
	int mtu;                 // <= 0 means automatic
	int maxMessageSize;      // <= 0 means default
} rtcConfiguration;

int rtcCreatePeerConnection(const rtcConfiguration *config); // returns pc id
int rtcClosePeerConnection(int pc);
int rtcDeletePeerConnection(int pc);

int rtcSetLocalDescriptionCallback(int pc, rtcDescriptionCallbackFunc cb);
int rtcSetLocalCandidateCallback(int pc, rtcCandidateCallbackFunc cb);
int rtcSetStateChangeCallback(int pc, rtcStateChangeCallbackFunc cb);
int rtcSetGatheringStateChangeCallback(int pc, rtcGatheringStateCallbackFunc cb);
int rtcSetSignalingStateChangeCallback(int pc, rtcSignalingStateCallbackFunc cb);

int rtcSetLocalDescription(int pc, const char *type);
int rtcSetRemoteDescription(int pc, const char *sdp, const char *type);
int rtcAddRemoteCandidate(int pc, const char *cand, const char *mid);

int rtcGetLocalDescription(int pc, char *buffer, int size);
int rtcGetRemoteDescription(int pc, char *buffer, int size);

int rtcGetLocalDescriptionType(int pc, char *buffer, int size);
int rtcGetRemoteDescriptionType(int pc, char *buffer, int size);

int rtcGetLocalAddress(int pc, char *buffer, int size);
int rtcGetRemoteAddress(int pc, char *buffer, int size);

int rtcGetSelectedCandidatePair(int pc, char *local, int localSize, char *remote,
                                           int remoteSize);

int rtcGetMaxDataChannelStream(int pc);

// DataChannel, Track, and WebSocket common API

int rtcSetOpenCallback(int id, rtcOpenCallbackFunc cb);
int rtcSetClosedCallback(int id, rtcClosedCallbackFunc cb);
int rtcSetErrorCallback(int id, rtcErrorCallbackFunc cb);
int rtcSetMessageCallback(int id, rtcMessageCallbackFunc cb);
int rtcSendMessage(int id, const char *data, int size);
int rtcClose(int id);
int rtcDelete(int id);
bool rtcIsOpen(int id);
bool rtcIsClosed(int id);

int rtcGetBufferedAmount(int id); // total size buffered to send
int rtcSetBufferedAmountLowThreshold(int id, int amount);
int rtcSetBufferedAmountLowCallback(int id, rtcBufferedAmountLowCallbackFunc cb);

// DataChannel, Track, and WebSocket common extended API

int rtcGetAvailableAmount(int id); // total size available to receive
int rtcSetAvailableCallback(int id, rtcAvailableCallbackFunc cb);
int rtcReceiveMessage(int id, char *buffer, int *size);

// DataChannel

typedef struct {
	bool unordered;
	bool unreliable;
	int maxPacketLifeTime; // ignored if reliable
	int maxRetransmits;    // ignored if reliable
} rtcReliability;

typedef struct {
	rtcReliability reliability;
	const char *protocol; // empty string if NULL
	bool negotiated;
	bool manualStream;
	uint16_t stream; // numeric ID 0-65534, ignored if manualStream is false
} rtcDataChannelInit;

int rtcSetDataChannelCallback(int pc, rtcDataChannelCallbackFunc cb);
int rtcCreateDataChannel(int pc, const char *label); // returns dc id
int rtcCreateDataChannelEx(int pc, const char *label,
                                      const rtcDataChannelInit *init); // returns dc id
int rtcDeleteDataChannel(int dc);

int rtcGetDataChannelStream(int dc);
int rtcGetDataChannelLabel(int dc, char *buffer, int size);
int rtcGetDataChannelProtocol(int dc, char *buffer, int size);
int rtcGetDataChannelReliability(int dc, rtcReliability *reliability);

// Track

typedef struct {
	rtcDirection direction;
	rtcCodec codec;
	int payloadType;
	uint32_t ssrc;
	const char *mid;
	const char *name;    // optional
	const char *msid;    // optional
	const char *trackId; // optional, track ID used in MSID
} rtcTrackInit;

int rtcSetTrackCallback(int pc, rtcTrackCallbackFunc cb);
int rtcAddTrack(int pc, const char *mediaDescriptionSdp); // returns tr id
int rtcAddTrackEx(int pc, const rtcTrackInit *init);      // returns tr id
int rtcDeleteTrack(int tr);

int rtcGetTrackDescription(int tr, char *buffer, int size);
int rtcGetTrackMid(int tr, char *buffer, int size);
int rtcGetTrackDirection(int tr, rtcDirection *direction);


// Media

// Define how NAL units are separated in a H264 sample
typedef enum {
	RTC_NAL_SEPARATOR_LENGTH = 0,               // first 4 bytes are NAL unit length
	RTC_NAL_SEPARATOR_LONG_START_SEQUENCE = 1,  // 0x00, 0x00, 0x00, 0x01
	RTC_NAL_SEPARATOR_SHORT_START_SEQUENCE = 2, // 0x00, 0x00, 0x01
	RTC_NAL_SEPARATOR_START_SEQUENCE = 3,       // long or short start sequence
} rtcNalUnitSeparator;

typedef struct {
	uint32_t ssrc;
	const char *cname;
	uint8_t payloadType;
	uint32_t clockRate;
	uint16_t sequenceNumber;
	uint32_t timestamp;

	// H264
	rtcNalUnitSeparator nalSeparator; // NAL unit separator
	uint16_t maxFragmentSize;         // Maximum NAL unit fragment size

} rtcPacketizationHandlerInit;

typedef struct {
	uint32_t ssrc;
	const char *name;    // optional
	const char *msid;    // optional
	const char *trackId; // optional, track ID used in MSID
} rtcSsrcForTypeInit;

// Set H264PacketizationHandler for track
int rtcSetH264PacketizationHandler(int tr, const rtcPacketizationHandlerInit *init);

// Set OpusPacketizationHandler for track
int rtcSetOpusPacketizationHandler(int tr, const rtcPacketizationHandlerInit *init);

// Chain RtcpSrReporter to handler chain for given track
int rtcChainRtcpSrReporter(int tr);

// Chain RtcpNackResponder to handler chain for given track
int rtcChainRtcpNackResponder(int tr, unsigned int maxStoredPacketsCount);

// Transform seconds to timestamp using track's clock rate, result is written to timestamp
int rtcTransformSecondsToTimestamp(int id, double seconds, uint32_t *timestamp);

// Transform timestamp to seconds using track's clock rate, result is written to seconds
int rtcTransformTimestampToSeconds(int id, uint32_t timestamp, double *seconds);

// Get current timestamp, result is written to timestamp
int rtcGetCurrentTrackTimestamp(int id, uint32_t *timestamp);

// Set RTP timestamp for track identified by given id
int rtcSetTrackRtpTimestamp(int id, uint32_t timestamp);

// Get timestamp of last RTCP SR, result is written to timestamp
int rtcGetLastTrackSenderReportTimestamp(int id, uint32_t *timestamp);

// Set NeedsToReport flag in RtcpSrReporter handler identified by given track id
int rtcSetNeedsToSendRtcpSr(int id);

// Get all available payload types for given codec and stores them in buffer, does nothing if
// buffer is NULL
int rtcGetTrackPayloadTypesForCodec(int tr, const char *ccodec, int *buffer, int size);

// Get all SSRCs for given track
int rtcGetSsrcsForTrack(int tr, uint32_t *buffer, int count);

// Get CName for SSRC
int rtcGetCNameForSsrc(int tr, uint32_t ssrc, char *cname, int cnameSize);

// Get all SSRCs for given media type in given SDP
int rtcGetSsrcsForType(const char *mediaType, const char *sdp, uint32_t *buffer, int bufferSize);

// Set SSRC for given media type in given SDP
int rtcSetSsrcForType(const char *mediaType, const char *sdp, char *buffer, const int bufferSize,
                      rtcSsrcForTypeInit *init);



// WebSocket

typedef struct {
	bool disableTlsVerification; // if true, don't verify the TLS certificate
	const char *proxyServer;     // unsupported for now
	const char **protocols;
	int protocolsCount;
	int pingInterval;        // in milliseconds, 0 means default, < 0 means disabled
	int maxOutstandingPings; // 0 means default, < 0 means disabled
} rtcWsConfiguration;

int rtcCreateWebSocket(const char *url); // returns ws id
int rtcCreateWebSocketEx(const char *url, const rtcWsConfiguration *config);
int rtcDeleteWebSocket(int ws);

int rtcGetWebSocketRemoteAddress(int ws, char *buffer, int size);
int rtcGetWebSocketPath(int ws, char *buffer, int size);

// WebSocketServer

typedef void(*rtcWebSocketClientCallbackFunc)(int wsserver, int ws, void *ptr);

typedef struct {
	uint16_t port;                  // 0 means automatic selection
	bool enableTls;                 // if true, enable TLS (WSS)
	const char *certificatePemFile; // NULL for autogenerated certificate
	const char *keyPemFile;         // NULL for autogenerated certificate
	const char *keyPemPass;         // NULL if no pass
} rtcWsServerConfiguration;

int rtcCreateWebSocketServer(const rtcWsServerConfiguration *config,
                                        rtcWebSocketClientCallbackFunc cb); // returns wsserver id
int rtcDeleteWebSocketServer(int wsserver);

int rtcGetWebSocketServerPort(int wsserver);


// Optional global preload and cleanup

void rtcPreload(void);
void rtcCleanup(void);

// SCTP global settings

typedef struct {
	int recvBufferSize;             // in bytes, <= 0 means optimized default
	int sendBufferSize;             // in bytes, <= 0 means optimized default
	int maxChunksOnQueue;           // in chunks, <= 0 means optimized default
	int initialCongestionWindow;    // in MTUs, <= 0 means optimized default
	int maxBurst;                   // in MTUs, 0 means optimized default, < 0 means disabled
	int congestionControlModule;    // 0: RFC2581 (default), 1: HSTCP, 2: H-TCP, 3: RTCC
	int delayedSackTimeMs;          // in msecs, 0 means optimized default, < 0 means disabled
	int minRetransmitTimeoutMs;     // in msecs, <= 0 means optimized default
	int maxRetransmitTimeoutMs;     // in msecs, <= 0 means optimized default
	int initialRetransmitTimeoutMs; // in msecs, <= 0 means optimized default
	int maxRetransmitAttempts;      // number of retransmissions, <= 0 means optimized default
	int heartbeatIntervalMs;        // in msecs, <= 0 means optimized default
} rtcSctpSettings;

// Note: SCTP settings apply to newly-created PeerConnections only
int rtcSetSctpSettings(const rtcSctpSettings *settings);
''')
ffibuilder.cdef('''
extern "Python" void wrapper_local_description_callback(int pc, const char *sdp, const char *type, void *ptr);
extern "Python" void wrapper_local_candidate_callback(int pc, const char *cand, const char *mid, void *ptr);
extern "Python" void wrapper_state_change_callback(int pc, rtcState state, void *ptr);
extern "Python" void wrapper_gathering_state_change_callback(int pc, rtcGatheringState state, void *ptr);
extern "Python" void wrapper_signaling_state_change_callback(int pc, rtcSignalingState state, void *ptr);
extern "Python" void wrapper_open_callback(int id, void *ptr);
extern "Python" void wrapper_closed_callback(int id, void *ptr);
extern "Python" void wrapper_error_callback(int id, const char *error, void *ptr);
extern "Python" void wrapper_message_callback(int id, const char *message, int size, void *ptr);
extern "Python" void wrapper_buffered_amount_low_callback(int id, void *ptr);
extern "Python" void wrapper_available_callback(int id, void *ptr);
extern "Python" void wrapper_data_channel_callback(int pc, int dc, void *ptr);
extern "Python" void wrapper_track_callback(int pc, int tr, void *ptr);


''')
ffibuilder.set_source("_libdatachannel_cffi",
"""
     #include "rtc/rtc.h"   // the C header of the library
""",
		      libraries=['datachannel'])   # library name, for the linker
ffibuilder.compile(verbose=True)
from _libdatachannel_cffi import ffi, lib

class State(Enum):
    NEW=0
    CONNECTING=1
    CONNECTED=2
    DISCONNECTED=3
    FAILED=4
    CLOSED=5

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
    CODEC_OPUS=128
    CODEC_PCMU=129
    CODEC_PCMA=130

class Direction(Enum):
    DIRECTION_UNKNOWN=0
    DIRECTION_SENDONLY=1
    DIRECTION_RECVONLY=2
    DIRECTION_SENDRECV=3
    DIRECTION_INACTIVE=4

class TransportPolicy(Enum):
    TRANSPORT_POLICY_ALL=0
    TRANSPORT_POLICY_RELAY=1

class NalUnitSeparator(Enum):
    NAL_SEPARATOR_LENGTH=0
    NAL_SEPARATOR_LONG_START_SEQUENCE=1
    NAL_SEPARATOR_SHORT_START_SEQUENCE=2
    NAL_SEPARATOR_START_SEQUENCE=3

@ffi.def_extern()
def wrapper_local_description_callback(pc, sdp, type, ptr):
    cb = PeerConnection.assoc[pc].local_description_callback
    cb and cb(ffi.string(sdp).decode(), ffi.string(type).decode(), )

@ffi.def_extern()
def wrapper_local_candidate_callback(pc, cand, mid, ptr):
    cb = PeerConnection.assoc[pc].local_candidate_callback
    cb and cb(ffi.string(cand).decode(), ffi.string(mid).decode(), )

@ffi.def_extern()
def wrapper_state_change_callback(pc, state, ptr):
    cb = PeerConnection.assoc[pc].state_change_callback
    cb and cb(State(state), )

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
    cb = CommonChannel.assoc[pc].open_callback
    cb and cb()

@ffi.def_extern()
def wrapper_closed_callback(id, ptr):
    cb = CommonChannel.assoc[pc].closed_callback
    cb and cb()

@ffi.def_extern()
def wrapper_error_callback(id, error, ptr):
    cb = CommonChannel.assoc[pc].error_callback
    cb and cb(ffi.string(error).decode(), )

@ffi.def_extern()
def wrapper_message_callback(id, message, size, ptr):
    cb = CommonChannel.assoc[pc].message_callback
    cb and cb(ffi.string(message).decode(), size, )

@ffi.def_extern()
def wrapper_buffered_amount_low_callback(id, ptr):
    cb = CommonChannel.assoc[pc].buffered_amount_low_callback
    cb and cb()

@ffi.def_extern()
def wrapper_available_callback(id, ptr):
    cb = CommonChannel.assoc[pc].available_callback
    cb and cb()

@ffi.def_extern()
def wrapper_data_channel_callback(pc, dc, ptr):
    cb = PeerConnection.assoc[pc].data_channel_callback
    cb and cb(dc, )

@ffi.def_extern()
def wrapper_track_callback(pc, tr, ptr):
    cb = PeerConnection.assoc[pc].track_callback
    cb and cb(tr, )


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

    def send_message(self, data, size, ):
        checkErr(lib.rtcSendMessage, self.id, data, size, )
    def close(self, ):
        checkErr(lib.rtcClose, self.id, )
    def delete(self, ):
        checkErr(lib.rtcDelete, self.id, )
    def get_buffered_amount(self, ):
        checkErr(lib.rtcGetBufferedAmount, self.id, )
    def set_buffered_amount_low_threshold(self, amount, ):
        checkErr(lib.rtcSetBufferedAmountLowThreshold, self.id, amount, )
    def get_available_amount(self, ):
        checkErr(lib.rtcGetAvailableAmount, self.id, )
    def set_needs_to_send_rtcp_sr(self, ):
        checkErr(lib.rtcSetNeedsToSendRtcpSr, self.id, )
    buffered_amount = property(get_buffered_amount, )
    available_amount = property(get_available_amount, )
    

class DataChannel(CommonChannel):
    assoc = {}
    def __init__(self, pc, name):
        super().__init__(lib.rtcCreateDataChannel(pc.id, name.encode()))
        self.assoc[self.id]=self
        
    def delete_data_channel(self, ):
        checkErr(lib.rtcDeleteDataChannel, self.id, )
    def get_data_channel_stream(self, ):
        checkErr(lib.rtcGetDataChannelStream, self.id, )
    def get_data_channel_label(self):
        return outString(lib.rtcGetDataChannelLabel, self.id)
    def get_data_channel_protocol(self):
        return outString(lib.rtcGetDataChannelProtocol, self.id)
    data_channel_stream = property(get_data_channel_stream, )
    data_channel_label = property(get_data_channel_label, )
    data_channel_protocol = property(get_data_channel_protocol, )
    
    
class PeerConnection:
    # C bindings PeerConnection ids to objects of this class
    assoc = {}
    
    def __init__(self):
        self.conf=ffi.new("rtcConfiguration *")
        self.id=lib.rtcCreatePeerConnection(self.conf)
        print("Created peerconn:", self.id)
        self.conf=ffi.gc(self.conf, lambda: print(123) and lib.rtcDeletePeerConnection(self.id))
        self.assoc[self.id]=self
        lib.rtcSetDataChannelCallback(self.id, lib.wrapper_data_channel_callback)
        lib.rtcSetGatheringStateChangeCallback(self.id, lib.wrapper_gathering_state_change_callback)
        lib.rtcSetLocalCandidateCallback(self.id, lib.wrapper_local_candidate_callback)
        lib.rtcSetLocalDescriptionCallback(self.id, lib.wrapper_local_description_callback)
        lib.rtcSetSignalingStateChangeCallback(self.id, lib.wrapper_signaling_state_change_callback)
        lib.rtcSetStateChangeCallback(self.id, lib.wrapper_state_change_callback)
        lib.rtcSetTrackCallback(self.id, lib.wrapper_track_callback)
        self.data_channel_callback = None
        self.gathering_state_change_callback = None
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
        checkErr(lib.rtcClosePeerConnection, self.id, )
    def delete_peer_connection(self, ):
        checkErr(lib.rtcDeletePeerConnection, self.id, )
    def set_local_description(self, type, ):
        checkErr(lib.rtcSetLocalDescription, self.id, type, )
    def set_remote_description(self, sdp, type, ):
        checkErr(lib.rtcSetRemoteDescription, self.id, sdp, type, )
    def add_remote_candidate(self, cand, mid, ):
        checkErr(lib.rtcAddRemoteCandidate, self.id, cand, mid, )
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
        checkErr(lib.rtcGetSelectedCandidatePair, self.id, local, localSize, remote, remoteSize, )
    def get_max_data_channel_stream(self, ):
        checkErr(lib.rtcGetMaxDataChannelStream, self.id, )
    def create_data_channel(self, label, ):
        checkErr(lib.rtcCreateDataChannel, self.id, label, )
    def add_track(self, mediaDescriptionSdp, ):
        checkErr(lib.rtcAddTrack, self.id, mediaDescriptionSdp, )
    local_description = property(get_local_description, set_local_description)
    remote_description = property(get_remote_description, set_remote_description)
    local_description_type = property(get_local_description_type, )
    remote_description_type = property(get_remote_description_type, )
    local_address = property(get_local_address, )
    remote_address = property(get_remote_address, )
    selected_candidate_pair = property(get_selected_candidate_pair, )
    max_data_channel_stream = property(get_max_data_channel_stream, )
    
    def set_local_description(self, type=ffi.NULL):
        return checkErr(lib.rtcSetLocalDescription, self.id, type, )
    
    # optional arg
    def override_set_remote_description(self, desc):
        self.set_remote_description(desc, ffi.NULL)
    remote_description=property(get_remote_description, override_set_remote_description)
    
def init_logger(level):
    lib.rtcInitLogger(level.value, ffi.NULL)

