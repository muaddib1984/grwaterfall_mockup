"""
Embedded Python Blocks:

Each time this file is saved, GRC will instantiate the first class it finds
to get ports and parameters of your block. The arguments to __init__  will
be the parameters. All of them are required to have default values!
"""

import numpy as np
from gnuradio import gr
import json

class fft_broadcast_sink(gr.sync_block):
    def __init__(self, fft_size=4096):
        gr.sync_block.__init__(self,
                               name="plotter",
                               in_sig=[(np.float32, fft_size)],
                               out_sig=[])
        self.tb=None
    def set_tb(self,ext_tb):
        self.tb=ext_tb
    def work(self, input_items, output_items):
        ninput_items = len(input_items[0])

        for bins in input_items[0]:
            p = np.around(bins).astype(int)
            p = np.fft.fftshift(p)
            for c in self.tb.connections.copy():
                try:
                    c.send(json.dumps({'s': p.tolist()}, separators=(',', ':')))
                except Exception:
                    self.tb.connections.remove(c)

        self.consume(0, ninput_items)

        return 0
