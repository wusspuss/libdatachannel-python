Attempt at bindings for libdatachannel. Attempts to offer a Pythonic interface, like:
```
import libdatachannel
with libdatachanel.PeerConnection() as pc:
    pc.gathering_state_change_callback = print
    pc.state_change_callback = lambda *args: print("State:", args)
    pc.gathering_state_callback = lambda *args: print("GatheringState:", args)
    pc.add_track(b"m=video 52313 UDP/TLS/RTP/SAVPF 96\na=mid:video")
    pc.set_local_description()
    print(
        "local description:\n",
        json.dumps({"type": "offer", "sdp": pc.local_description}),
    )
```

Some manual overrides are still needed, e.g. because it cannot automatically detect if an argument is optional. Also, some names are rather awkward, like `dc.data_channel_label` when it should ideally be `dc.label`. These could be fixed by specifying optional args in a comment inside the rtc.h header in some consistent manner and using more consistent function naming, respectively.
This is a quick-and-dirty evening boredom-driven development project, so convert.tcl can probably be much shorter, especially if some hints/even more consistency is added to rtc.h.

It wraps PeerConnection, DataChannel and apparently some other thing into classes, fills those classes with mehods, fields for callbacks, and also wraps getters and setters in Python properties (all demonstrated in the above example). It wraps enums in Python enum, so in callbacks you get enum names, not just numbers. It translates errors in Python Exceptions.

Uses libdatachannel's C API with python-cffi. The wrapping code in libdatachannel.py is generated from libdatachannel_inc.py using convert.tcl (so needs a Tcl interpreter to build).