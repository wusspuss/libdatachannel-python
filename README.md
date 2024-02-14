Attempt at bindings for [libdatachannel](https://github.com/paullouisageneau/libdatachannel). Attempts to offer a Pythonic interface, like:
```
import libdatachannel
pc = libdatachanel.PeerConnection()
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
`media_receiver.py` can be used the same way that libdatachannel's `examples/media-receiver/` is. It needs `main.html` from there to open in the browser as client.

Some manual overrides are still needed, e.g. because it cannot automatically detect if an argument is optional. Also, some names are rather awkward, like `dc.data_channel_label` when it should ideally be `dc.label`. These could be fixed by specifying optional args in a comment inside the rtc.h header in some consistent manner and using more consistent function naming, respectively.
This is a quick-and-dirty evening boredom-driven development project, so convert.tcl can probably be much shorter, especially if some hints/even more consistency is added to rtc.h.

It wraps PeerConnection, DataChannel and apparently some other thing into classes, fills those classes with mehods, fields for callbacks, and also wraps getters and setters in Python properties (all demonstrated in the above example). It wraps enums in Python enum, so in callbacks you get enum names, not just numbers. It translates errors in Python Exceptions.

Uses libdatachannel's C API with python-cffi. The wrapping code in `src/libdatachannel/__init__.py` is generated from `libdatachannel_inc.py` using `convert.tcl` (so needs a Tcl interpreter to build).

This is all very messy. I made convert.tcl in Tcl just because I had fresh memory of working with regexp in Tcl and not Python. I did whatever got it to work and don't yet have the time to get it to work properly, so it may as well be some of the worst code you'll ever see.

Now it can be installed with pip.
The `src/libdatachannel/__init__.py` has to exactly match your libdatachannel version. It can be generated no the spot with just `tclsh conver.tcl`, given that you have  `/usr/include/rtc/rtc.h`, or you can just give it a different path in the file itself. After that, you can do the usual `pip install .` or `python -m build`. 

TODO:
	- rewrite convert.tcl cleanly in python
	- include convert.tcl into `python -m build` or whatever
	- give the pip package the same version as the libdatachannel it targets?
