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
	RTC_ICE_NEW = 0,
	RTC_ICE_CHECKING = 1,
	RTC_ICE_CONNECTED = 2,
	RTC_ICE_COMPLETED = 3,
	RTC_ICE_FAILED = 4,
	RTC_ICE_DISCONNECTED = 5,
	RTC_ICE_CLOSED = 6
} rtcIceState;

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
	RTC_CODEC_H265 = 3,

	// audio
	RTC_CODEC_OPUS = 128,
	RTC_CODEC_PCMU = 129,
	RTC_CODEC_PCMA = 130,
	RTC_CODEC_AAC = 131,
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
typedef void(*rtcIceStateChangeCallbackFunc)(int pc, rtcIceState state, void *ptr);
typedef void(*rtcGatheringStateCallbackFunc)(int pc, rtcGatheringState state, void *ptr);
typedef void(*rtcSignalingStateCallbackFunc)(int pc, rtcSignalingState state, void *ptr);
typedef void(*rtcDataChannelCallbackFunc)(int pc, int dc, void *ptr);
typedef void(*rtcTrackCallbackFunc)(int pc, int tr, void *ptr);
typedef void(*rtcOpenCallbackFunc)(int id, void *ptr);
typedef void(*rtcClosedCallbackFunc)(int id, void *ptr);
typedef void(*rtcErrorCallbackFunc)(int id, const char *error, void *ptr);
typedef void(*rtcMessageCallbackFunc)(int id, const char *message, int size, void *ptr);
typedef void *(*rtcInterceptorCallbackFunc)(int pc, const char *message, int size,
                                                    void *ptr);
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
int rtcSetIceStateChangeCallback(int pc, rtcIceStateChangeCallbackFunc cb);
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
	const char *profile; // optional, codec profile
} rtcTrackInit;

int rtcSetTrackCallback(int pc, rtcTrackCallbackFunc cb);
int rtcAddTrack(int pc, const char *mediaDescriptionSdp); // returns tr id
int rtcAddTrackEx(int pc, const rtcTrackInit *init);      // returns tr id
int rtcDeleteTrack(int tr);

int rtcGetTrackDescription(int tr, char *buffer, int size);
int rtcGetTrackMid(int tr, char *buffer, int size);
int rtcGetTrackDirection(int tr, rtcDirection *direction);


// Media

// Define how OBUs are packetizied in a AV1 Sample
typedef enum {
	RTC_OBU_PACKETIZED_OBU = 0,
	RTC_OBU_PACKETIZED_TEMPORAL_UNIT = 1,
} rtcObuPacketization;

// Define how NAL units are separated in a H264/H265 sample
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

	// H264/H265
	rtcNalUnitSeparator nalSeparator; // NAL unit separator
	uint16_t maxFragmentSize;         // Maximum NAL unit fragment size

} rtcPacketizationHandlerInit;

typedef struct {
	uint32_t ssrc;
	const char *name;    // optional
	const char *msid;    // optional
	const char *trackId; // optional, track ID used in MSID
} rtcSsrcForTypeInit;

// Opaque message

// Opaque type used (via rtcMessage*) to reference an rtc::Message
typedef void *rtcMessage;

// Allocate a new opaque message.
// Must be explicitly freed by rtcDeleteOpaqueMessage() unless
// explicitly returned by a media interceptor callback;
rtcMessage *rtcCreateOpaqueMessage(void *data, int size);
void rtcDeleteOpaqueMessage(rtcMessage *msg);

// Set MediaInterceptor for peer connection
int rtcSetMediaInterceptorCallback(int id, rtcInterceptorCallbackFunc cb);

// Set H264PacketizationHandler for track
int rtcSetH264PacketizationHandler(int tr, const rtcPacketizationHandlerInit *init);

// Set H265PacketizationHandler for track
int rtcSetH265PacketizationHandler(int tr, const rtcPacketizationHandlerInit *init);

// Set OpusPacketizationHandler for track
int rtcSetOpusPacketizationHandler(int tr, const rtcPacketizationHandlerInit *init);

// Set AACPacketizationHandler for track
int rtcSetAACPacketizationHandler(int tr, const rtcPacketizationHandlerInit *init);

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
	const char *proxyServer;     // only non-authenticated http supported for now
	const char **protocols;
	int protocolsCount;
	int connectionTimeoutMs; // in milliseconds, 0 means default, < 0 means disabled
	int pingIntervalMs;      // in milliseconds, 0 means default, < 0 means disabled
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
	const char *bindAddress;        // NULL for IP_ANY_ADDR
	int connectionTimeoutMs;        // in milliseconds, 0 means default, < 0 means disabled
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
	int recvBufferSize;          // in bytes, <= 0 means optimized default
	int sendBufferSize;          // in bytes, <= 0 means optimized default
	int maxChunksOnQueue;        // in chunks, <= 0 means optimized default
	int initialCongestionWindow; // in MTUs, <= 0 means optimized default
	int maxBurst;                // in MTUs, 0 means optimized default, < 0 means disabled
	int congestionControlModule; // 0: RFC2581 (default), 1: HSTCP, 2: H-TCP, 3: RTCC
	int delayedSackTimeMs;       // in milliseconds, 0 means optimized default, < 0 means disabled
	int minRetransmitTimeoutMs;  // in milliseconds, <= 0 means optimized default
	int maxRetransmitTimeoutMs;  // in milliseconds, <= 0 means optimized default
	int initialRetransmitTimeoutMs; // in milliseconds, <= 0 means optimized default
	int maxRetransmitAttempts;      // number of retransmissions, <= 0 means optimized default
	int heartbeatIntervalMs;        // in milliseconds, <= 0 means optimized default
} rtcSctpSettings;

// Note: SCTP settings apply to newly-created PeerConnections only
int rtcSetSctpSettings(const rtcSctpSettings *settings);
''')
ffibuilder.cdef('''
extern "Python" void wrapper_local_description_callback(int pc, const char *sdp, const char *type, void *ptr);
extern "Python" void wrapper_local_candidate_callback(int pc, const char *cand, const char *mid, void *ptr);
extern "Python" void wrapper_state_change_callback(int pc, rtcState state, void *ptr);
extern "Python" void wrapper_ice_state_change_callback(int pc, rtcIceState state, void *ptr);
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

