#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: Not titled yet
# Author: muaddib
# GNU Radio version: 3.9.4.0

from bottle import request, Bottle, abort, static_file
from gevent.pywsgi import WSGIServer
from geventwebsocket import WebSocketError
from geventwebsocket.handler import WebSocketHandler
from gnuradio import analog
from gnuradio import blocks
from gnuradio import gr
from gnuradio.filter import firdes
from gnuradio.fft import window
import sys
import signal
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
from gnuradio.fft import logpwrfft
import argparse
import fft_receiver_fft_broadcast as fft_broadcast  # embedded python block
import json
import numpy as np


def snipfcn_app_vars(self):
    self.app = Bottle()
    self.connections = set()
    self.opts = {}
    self.fft_broadcast.set_tb(self)

def snipfcn_server(self):
    server = WSGIServer(("0.0.0.0", 8000), self.app,
                        handler_class=WebSocketHandler)
    try:
        server.serve_forever()
    except Exception:
        sys.exit(0)

    self.opts['center'] = self.frequency
    self.opts['span'] = self.samp_rate

def snipfcn_websocket(self):
    @self.app.route('/websocket')
    def handle_websocket():
        wsock = request.environ.get('wsgi.websocket')
        if not wsock:
            abort(400, 'Expected WebSocket request.')

        self.connections.add(wsock)

        # Send center frequency and span
        wsock.send(json.dumps(self.opts))

        while True:
            try:
                wsock.receive()
            except WebSocketError:
                break

        self.connections.remove(wsock)


    @self.app.route('/')
    def index():
        return static_file('index.html', root='.')


    @self.app.route('/<filename>')
    def static(filename):
        return static_file(filename, root='.')


def snippets_main_after_init(tb):
    snipfcn_app_vars(tb)
    snipfcn_websocket(tb)

def snippets_main_after_start(tb):
    snipfcn_server(tb)


class fft_receiver(gr.top_block):

    def __init__(self, frequency=750e6):
        gr.top_block.__init__(self, "Not titled yet", catch_exceptions=True)

        ##################################################
        # Parameters
        ##################################################
        self.frequency = frequency

        ##################################################
        # Variables
        ##################################################
        self.samp_rate = samp_rate = 10e6
        self.fft_size = fft_size = 4096

        ##################################################
        # Blocks
        ##################################################
        self.logpwrfft_x_0 = logpwrfft.logpwrfft_c(
            sample_rate=samp_rate,
            fft_size=fft_size,
            ref_scale=1,
            frame_rate=30,
            avg_alpha=1.0,
            average=False,
            shift=False)
        self.fft_broadcast = fft_broadcast.fft_broadcast_sink(fft_size=fft_size)
        self.blocks_throttle_0 = blocks.throttle(gr.sizeof_gr_complex*1, samp_rate,True)
        self.analog_fastnoise_source_x_0 = analog.fastnoise_source_c(analog.GR_GAUSSIAN, 1, 0, 8192)



        ##################################################
        # Connections
        ##################################################
        self.connect((self.analog_fastnoise_source_x_0, 0), (self.blocks_throttle_0, 0))
        self.connect((self.blocks_throttle_0, 0), (self.logpwrfft_x_0, 0))
        self.connect((self.logpwrfft_x_0, 0), (self.fft_broadcast, 0))


    def get_frequency(self):
        return self.frequency

    def set_frequency(self, frequency):
        self.frequency = frequency

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.blocks_throttle_0.set_sample_rate(self.samp_rate)
        self.logpwrfft_x_0.set_sample_rate(self.samp_rate)

    def get_fft_size(self):
        return self.fft_size

    def set_fft_size(self, fft_size):
        self.fft_size = fft_size



def argument_parser():
    parser = ArgumentParser()
    parser.add_argument(
        "-f", "--frequency", dest="frequency", type=eng_float, default=eng_notation.num_to_str(float(750e6)),
        help="Set frequency [default=%(default)r]")
    return parser


def main(top_block_cls=fft_receiver, options=None):
    if options is None:
        options = argument_parser().parse_args()
    tb = top_block_cls(frequency=options.frequency)
    snippets_main_after_init(tb)
    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        sys.exit(0)

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    tb.start()
    snippets_main_after_start(tb)
    tb.wait()


if __name__ == '__main__':
    main()
