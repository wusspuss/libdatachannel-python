import socket
import json
import libdatachannel

libdatachannel.init_logger(libdatachannel.LogLevel.LOG_DEBUG)

def onGatheringStateChange(state, pc):
    print("Gathering State:", state)
    if state == libdatachannel.GatheringState.GATHERING_COMPLETE:
        print(json.dumps({'sdp': pc.local_description, 'type': 'offer'}))

def onMessage(message):
    sock.sendto(message, ('127.0.0.1', 5000))
    print('.', end='', flush=True)

pc = libdatachannel.PeerConnection()

pc.gathering_state_change_callback = lambda state: onGatheringStateChange(state, pc)    
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
track = pc.add_track('\n'.join(["video 52313 UDP/TLS/RTP/SAVPF 96",
                                "a=mid:video",
                                "a=recvonly",
                                "b=AS:3000",
                                "a=rtpmap:96 H264/90000",
                                "a=rtcp-fb:96 nack",
                                "a=rtcp-fb:96 nack pli",
                                "a=rtcp-fb:96 goog-remb",
                                "a=fmtp:96 profile-level-id=42e01f;packetization-mode=1;"
                                "level-asymmetry-allowed=1",
                                 ]))
track.message_callback = onMessage
pc.set_local_description()
pc.remote_description=json.loads(input("Remote description:"))['sdp']
input()

