import socket
import json
import libdatachannel

libdatachannel.init_logger(libdatachannel.LogLevel.LOG_VERBOSE)

def onGatheringStateChange(state, pc):
    print("Gathering State:", state)
    if state == libdatachannel.GatheringState.GATHERING_COMPLETE:
        print(json.dumps({'sdp': pc.local_description, 'type': 'offer'}))

def onMessage(message, size):
    sock.sendto(message, ('127.0.0.1', 5000))
    # print('.', end='', flush=True)

pc = libdatachannel.PeerConnection()
# with libdatachannel.PeerConnection() as pc:
pc.gathering_state_change_callback = lambda state: onGatheringStateChange(state, pc)    
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
track = pc.add_track(b'\n'.join([b"video 52313 UDP/TLS/RTP/SAVPF 96",
                                 b"a=mid:video",
                                 b"a=recvonly",
                                 b"b=AS:3000",
                                 b"a=rtpmap:96 H264/90000",
                                 b"a=rtcp-fb:96 nack",
                                 b"a=rtcp-fb:96 nack pli",
                                 b"a=rtcp-fb:96 goog-remb",
                                 b"a=fmtp:96 profile-level-id=42e01f;packetization-mode=1;"
                                 b"level-asymmetry-allowed=1",
                                 ]))
track.message_callback = onMessage
pc.set_local_description()
pc.remote_description=json.loads(input("Remote description:"))['sdp'].encode()
input()

