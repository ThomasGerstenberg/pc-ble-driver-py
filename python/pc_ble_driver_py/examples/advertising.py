#
# Copyright (c) 2016 Nordic Semiconductor ASA
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#   1. Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
#   2. Redistributions in binary form must reproduce the above copyright notice, this
#   list of conditions and the following disclaimer in the documentation and/or
#   other materials provided with the distribution.
#
#   3. Neither the name of Nordic Semiconductor ASA nor the names of other
#   contributors to this software may be used to endorse or promote products
#   derived from this software without specific prior written permission.
#
#   4. This software must only be used in or with a processor manufactured by Nordic
#   Semiconductor ASA, or in or with a processor manufactured by a third party that
#   is used in combination with a processor manufactured by Nordic Semiconductor.
#
#   5. Any software provided in binary or object form under this license must not be
#   reverse engineered, decompiled, modified and/or disassembled.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

import sys
from threading import Condition, Lock
import Queue
from pc_ble_driver_py.observers import BLEDriverObserver

from pc_ble_driver_py import config

config.__conn_ic_id__ = "NRF52"
from pc_ble_driver_py.ble_driver import BLEDriver, BLEAdvData, BLEEvtID, BLEGapSecStatus, BLEGapSecParams, BLEGapIOCaps, \
    BLEGapSecKDist
from pc_ble_driver_py.ble_adapter import BLEAdapter


def main(serial_port):
    print("Serial port used: {}".format(serial_port))
    driver = BLEDriver(serial_port=serial_port)
    adapter = BLEAdapter(driver)
    observer = TimeoutObserver(adapter)
    adv_data = BLEAdvData(complete_local_name='Example')

    driver.observer_register(observer)
    driver.open()
    driver.ble_enable()
    driver.ble_gap_adv_data_set(adv_data)
    driver.ble_gap_adv_start()
    observer.wait_for_timeout(True)
    observer.sec_reply(driver)
    passkey = observer.q.get()

    observer.wait_for_timeout()

    print("Closing")
    driver.close()


class TimeoutObserver(BLEDriverObserver):
    def __init__(self, adapter):
        """

        :type adapter: BLEAdapter
        """
        self.cond = Condition(Lock())
        self.adapter = adapter
        self.sec_cond = Condition(Lock())
        self.conn_handle = 0
        self.q = Queue.Queue()

    def on_gap_evt_timeout(self, ble_driver, conn_handle, src):
        with self.cond:
            self.cond.notify_all()

    def wait_for_timeout(self, sec=False):
        cond = self.sec_cond if sec else self.cond
        with cond:
            cond.wait()

    def on_gap_evt_connected(self, ble_driver, conn_handle, peer_addr, role, conn_params):
        print("Connected")

    def on_gap_evt_passkey_display(self, ble_driver, conn_handle, passkey_display):
        print("Passkey Display, {}, {}, {}".format(conn_handle, passkey_display.passkey,
                                                   passkey_display.match_request))
        self.q.put(passkey_display.passkey)

    def on_gap_evt_sec_params_request(self, ble_driver, conn_handle, peer_params):
        """
        :type ble_driver: BLEDriver
        """
        print("Sec params request")
        self.conn_handle = conn_handle
        with self.sec_cond:
            self.sec_cond.notify_all()

    def sec_reply(self, ble_driver):
        print("Sending reply")
        kdist_own = BLEGapSecKDist(enc=False,
                                   id=False,
                                   sign=False,
                                   link=False)
        kdist_peer = BLEGapSecKDist(enc=False,
                                    id=False,
                                    sign=False,
                                    link=False)
        sec_params = BLEGapSecParams(bond=False,
                                     mitm=True,
                                     lesc=False,
                                     keypress=False,
                                     io_caps=BLEGapIOCaps.display_only,
                                     oob=False,
                                     min_key_size=7,
                                     max_key_size=16,
                                     kdist_own=kdist_own,
                                     kdist_peer=kdist_peer)
        ble_driver.ble_gap_sec_params_reply(self.conn_handle, BLEGapSecStatus.success, sec_params, None, None)
        print("After reply")


if __name__ == "__main__":
    if len(sys.argv) == 2:
        main(sys.argv[1])
    else:
        print("Invalid arguments. Parameters: <serial_port>")
    quit()
