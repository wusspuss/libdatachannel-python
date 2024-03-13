from _libdatachannel_cffi import ffi, lib
import asyncio
import libdatachannel
import unittest
example_rtp_packet = b"\x80\x80\n\xa8\xbd.\x0b\x1d/(\xfe\x9cbY[TV_`ZWWZ[[\\YXXW]"
b"_^do\xf8\xf7mge]^biknkfg_\\Z^bWOONLLKHHHHIJNQNMLLOPRTWTOSZagillf__]["
track_description = '\n'.join([
            "audio 9 UDP/TLS/RTP/SAVPF 0",
            "c=IN IP4 0.0.0.0",
            "a=rtpmap:0 PCMU/8000",
            "a=mid:audio",
            "a=sendrecv",
            "a=rtcp-mux",
            "a=rtcp:9 IN IP4 0.0.0.0",
])
# libdatachannel.init_logger(libdatachannel.LogLevel.LOG_DEBUG)

def have_glib():
    """
    Used to skip GLib-related tests if it's not installed
    """
    try:
        import gi
        gi.require_version('GLib', '2.0')
        from gi.repository import GLib
    except (ImportError, ValueError):
        return False
    return True


class PeerConnectionTest(unittest.IsolatedAsyncioTestCase):
    def test_init_no_args(self):
        pc=libdatachannel.PeerConnection()
        self.assertIsInstance(pc,libdatachannel.PeerConnection)
        pc.delete()

    
    def test_init_ice_servers(self):
        # at least it doesn't crash...
        pc=libdatachannel.PeerConnection(['lol', 'kek'])
        pc.delete()
    
    async def test_local_send_and_receive_message(self):
        """
        Create two peer connections, send message from one to the other.
        Uses the asyncio event loop and manually wraps callbacks to have them
        invoked in the main thread.
        """
        loop=asyncio.get_event_loop()
        def gathering_state_change_cb(state, future):
            if state==libdatachannel.GatheringState.GATHERING_COMPLETE:
                loop.call_soon_threadsafe(future.set_result, None)
                

        pc1=libdatachannel.PeerConnection()
        pc2=libdatachannel.PeerConnection()

        track_description = '\n'.join([
            "audio 9 UDP/TLS/RTP/SAVPF 0",
            "c=IN IP4 0.0.0.0",
            "a=rtpmap:0 PCMU/8000",
            "a=mid:audio",
            "a=sendrecv",
            "a=rtcp-mux",
            "a=rtcp:9 IN IP4 0.0.0.0",
        ])
        tr2_future=asyncio.Future()
        
        tr1 = pc1.add_track(track_description)
        pc1_future=asyncio.Future()
        pc2_future=asyncio.Future()
        pc1.gathering_state_change_callback=lambda st:gathering_state_change_cb(st,pc1_future)
        pc2.gathering_state_change_callback=lambda st:gathering_state_change_cb(st,pc2_future)

        # send offer from pc1 to pc2
        pc1.set_local_description()
        await pc1_future
        pc2.track_callback=lambda tr: loop.call_soon_threadsafe(tr2_future.set_result, tr)
        pc2.set_remote_description(pc1.local_description, 'offer')
        await pc2_future
        # send answer from pc2 to pc1
        pc1.set_remote_description(pc2.local_description, 'answer')

        tr1_open_future=asyncio.Future()
        tr2_open_future=asyncio.Future()
        tr2=await tr2_future
        tr2.open_callback=lambda: loop.call_soon_threadsafe(tr2_open_future.set_result, None)
        tr1.open_callback=lambda: loop.call_soon_threadsafe(tr1_open_future.set_result, None)
        await asyncio.gather(tr1_open_future, tr2_open_future)

        tr1_message_future=asyncio.Future()
        tr1.message_callback=lambda msg: loop.call_soon_threadsafe(tr1_message_future.set_result, msg)
        tr2.send_message(example_rtp_packet)

        
        await tr1_message_future
        # at least the message got through - but the rtp packet bytes are different
        
        pc1.delete()
        pc2.delete()

    async def test_local_send_and_receive_message_with_async_with_scheduler(self):
        """
        Create two peer connections, send message from one to the other.
        Uses the asyncio event loop and libdatachannel.threadsafe_scheduler to have callbacks
        transparently invoked in the main thread.
        """
        libdatachannel.threadsafe_scheduler=asyncio.get_event_loop().call_soon_threadsafe
        def gathering_state_change_cb(state, future):
            if state==libdatachannel.GatheringState.GATHERING_COMPLETE:
                future.set_result(None)
                

        pc1=libdatachannel.PeerConnection()
        pc2=libdatachannel.PeerConnection()
        tr2_future=asyncio.Future()
        
        tr1 = pc1.add_track(track_description)
        pc1_future=asyncio.Future()
        pc2_future=asyncio.Future()
        pc1.gathering_state_change_callback=lambda st:gathering_state_change_cb(st,pc1_future)
        pc2.gathering_state_change_callback=lambda st:gathering_state_change_cb(st,pc2_future)

        # send offer from pc1 to pc2
        pc1.set_local_description()
        await pc1_future
        pc2.track_callback=tr2_future.set_result
        pc2.set_remote_description(pc1.local_description, 'offer')
        await pc2_future
        # send answer from pc2 to pc1
        pc1.set_remote_description(pc2.local_description, 'answer')

        tr1_open_future=asyncio.Future()
        tr2_open_future=asyncio.Future()
        tr2=await tr2_future
        tr2.open_callback=lambda: tr2_open_future.set_result(None)
        tr1.open_callback=lambda: tr1_open_future.set_result(None)
        await asyncio.gather(tr1_open_future, tr2_open_future)

        tr1_message_future=asyncio.Future()
        tr1.message_callback=tr1_message_future.set_result
        tr2.send_message(example_rtp_packet)

        
        await tr1_message_future
        # at least the message got through - but the rtp packet bytes are different
        
        pc1.delete()
        pc2.delete()
        libdatachannel.threadsafe_scheduler=lambda f, *args: f(*args)

    @unittest.skipIf(not have_glib(), "GLib not installed")
    def test_local_send_and_receive_message_with_glib_with_scheduler(self):
        """
        Create two peer connections, send message from one to the other.
        Uses the GLib event loop and libdatachannel.threadsafe_scheduler to have callbacks
        transparently invoked in the main thread.
        Fugly...
        """
        from gi.repository import GLib
        libdatachannel.threadsafe_scheduler=GLib.idle_add
        loop = GLib.MainLoop()
        pc1=libdatachannel.PeerConnection()
        pc2=libdatachannel.PeerConnection()
        tr1 = pc1.add_track(track_description)
        def when_pc1_gathering_state_cb(st):
            if st==libdatachannel.GatheringState.GATHERING_COMPLETE:
                def when_pc2_gathering_state_cb(st):
                    if st==libdatachannel.GatheringState.GATHERING_COMPLETE:
                        pc1.set_remote_description(pc2.local_description, 'answer')
                def when_pc2_on_track(tr):
                    tr2=tr
                    def when_tr2_open():
                        tr2.send_message(example_rtp_packet)
                    def on_tr1_message(msg):
                        loop.quit()
                    tr2.open_callback=when_tr2_open
                    tr1.message_callback=on_tr1_message
                    
                pc2.track_callback=when_pc2_on_track
                pc2.gathering_state_change_callback=when_pc2_gathering_state_cb
                pc2.set_remote_description(pc1.local_description, 'offer')
                
        pc1.gathering_state_change_callback=when_pc1_gathering_state_cb
        pc1.set_local_description()
        loop.run()
        pc1.delete()
        pc2.delete()
        libdatachannel.threadsafe_scheduler=lambda f, *args: f(*args)

    @unittest.skipIf(not have_glib(), "GLib not installed")
    def test_local_send_and_receive_message_with_glib_with_scheduler_with_receive_mesage(self):
        """
        Create two peer connections, send message from one to the other.
        Uses the GLib event loop and libdatachannel.threadsafe_scheduler to have callbacks
        transparently invoked in the main thread.
        Use track.receive_message instead of message_callback
        """
        from gi.repository import GLib
        libdatachannel.threadsafe_scheduler=GLib.idle_add
        loop = GLib.MainLoop()
        pc1=libdatachannel.PeerConnection()
        pc2=libdatachannel.PeerConnection()
        tr1 = pc1.add_track(track_description)
        def when_pc1_gathering_state_cb(st):
            if st==libdatachannel.GatheringState.GATHERING_COMPLETE:
                def when_pc2_gathering_state_cb(st):
                    if st==libdatachannel.GatheringState.GATHERING_COMPLETE:
                        pc1.set_remote_description(pc2.local_description, 'answer')
                def when_pc2_on_track(tr):
                    tr2=tr
                    def when_tr2_open():
                        with self.assertRaises(libdatachannel.NotAvail):
                            tr1.receive_message()
                        tr2.send_message(example_rtp_packet)
                    def on_tr1_available():
                        print('available')
                        tr1.receive_message()
                        loop.quit()
                    tr2.open_callback=when_tr2_open
                    # tr1.message_callback=on_tr1_message
                    tr1.available_callback=on_tr1_available
                    
                pc2.track_callback=when_pc2_on_track
                pc2.gathering_state_change_callback=when_pc2_gathering_state_cb
                pc2.set_remote_description(pc1.local_description, 'offer')
                
        pc1.gathering_state_change_callback=when_pc1_gathering_state_cb
        pc1.set_local_description()
        loop.run()
        pc1.delete()
        pc2.delete()
        libdatachannel.threadsafe_scheduler=lambda f, *args: f(*args)


if __name__ == '__main__':
    unittest.main()
