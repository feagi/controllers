"""
Copyright 2016-present Neuraville Inc. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
==============================================================================
"""
import numpy as np
import sounddevice as sd
from scipy.signal import stft
import queue
import sys
from time import sleep
from configuration import *
from datetime import datetime
from feagi_connector import pns_gateway as pns
from feagi_connector import sensors as sensors
from feagi_connector import feagi_interface as FEAGI
from version import __version__


# Parameters
fs = 44100  # Sampling rate
nperseg = 1024  # Length of each segment for STFT

# Create a queue to hold incoming audio frames
audio_q = queue.Queue()


# Callback function to capture audio from the microphone
def audio_callback(indata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
    # Put the incoming audio data into the queue
    audio_q.put(indata.copy())


# # FEAGI REACHABLE CHECKER # #
print("Waiting on FEAGI...")
# while not feagi_flag:
#     print("ip: ", os.environ.get('FEAGI_HOST_INTERNAL', feagi_settings["feagi_host"]))
#     print("here: ", int(os.environ.get('FEAGI_OPU_PORT', "30000")))
#     feagi_flag = FEAGI.is_FEAGI_reachable(
#         os.environ.get('FEAGI_HOST_INTERNAL', feagi_settings["feagi_host"]),
#         int(os.environ.get('FEAGI_OPU_PORT', "30000")))
#     sleep(2)

runtime_data = {"cortical_data": {}, "current_burst_id": None,
                "stimulation_period": 0.01, "feagi_state": None,
                "feagi_network": None}

feagi_auth_url = feagi_settings.pop('feagi_auth_url', None)
print("FEAGI AUTH URL ------- ", feagi_auth_url)
# # FEAGI REACHABLE CHECKER COMPLETED # #
# # # FEAGI registration # # # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# - - - - - - - - - - - - - - - - - - #
feagi_settings, runtime_data, api_address, feagi_ipu_channel, feagi_opu_channel = \
    FEAGI.connect_to_feagi(feagi_settings, runtime_data, agent_settings, capabilities,
                           __version__)
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
msg_counter = runtime_data["feagi_state"]['burst_counter']

# default_capabilities = {}  # It will be generated in process_visual_stimuli. See the
# # overwrite manual
# default_capabilities = pns.create_runtime_default_list(default_capabilities, capabilities)

# Start the audio stream
stream = sd.InputStream(callback=audio_callback, channels=1, samplerate=fs)
with stream:
    try:
        # Continuously process the incoming audio
        while True:
            # Retrieve a frame of audio data from the queue
            data = audio_q.get()

            # Adjust nperseg if it's larger than the length of the data
            current_nperseg = min(len(data), nperseg)
            noverlap = current_nperseg // 2  # Set noverlap to half of current_nperseg

            # Compute the STFT
            frequencies, times, Zxx = stft(data[:, 0], fs=fs, nperseg=current_nperseg, noverlap=noverlap)
            Zxx = np.abs(Zxx)  # Get the magnitude

            # Normalize and scale the magnitude data
            max_magnitude = Zxx.max() if Zxx.size > 0 else 1
            scaled_magnitude = (Zxx / max_magnitude) * 25  # Scale to range [0, 25]
            scaled_magnitude = scaled_magnitude.astype(int)  # Convert to integer for discrete levels

            # Normalize and scale frequency data
            min_freq, max_freq = frequencies[0], frequencies[-1]
            scaled_frequencies = (frequencies - min_freq) / (max_freq - min_freq) * 99  # Scale to range [0, 99]
            scaled_frequencies = scaled_frequencies.astype(int)  # Convert to integer for discrete levels

            # Create a dictionary for the frame
            frame_data = {}
            for freq, mag in zip(scaled_frequencies, scaled_magnitude[:, 0]):
                if mag > 0:  # Only consider points where magnitude is greater than zero
                    frame_data[f"{freq}-{mag}-0"] = 0

            # Print the frame data as a dictionary
            # if frame_data:  # Only print if there's data in the frame
            # #     # print(f"Frame (time index): {times[0]:.2f} seconds")
            #     print(frame_data)

            # Optional: Break after a certain condition or time
            # if some_condition:
            #     break
            message_from_feagi = pns.message_from_feagi
            # OPU section STARTS
            if message_from_feagi:
                pns.check_genome_status_no_vision(message_from_feagi)
                feagi_settings['feagi_burst_speed'] = pns.check_refresh_rate(message_from_feagi,
                                                                             feagi_settings[
                                                                                 'feagi_burst_speed'])
            # message_to_feagi = sensors.add_sound_to_feagi_data(frame_data, message_to_feagi)
            # # message_to_feagi['hearing'] = {"i__hear": frame_data}
            # print(message_to_feagi)
            # message_to_feagi['timestamp'] = datetime.now()
            # message_to_feagi['counter'] = msg_counter
            try:
                if "data" not in message_to_feagi:
                    message_to_feagi["data"] = dict()
                if "sensory_data" not in message_to_feagi["data"]:
                    message_to_feagi["data"]["sensory_data"] = dict()
                # message_to_feagi["data"]["sensory_data"]['hearing'] = dict()
                message_to_feagi['i_hear'] = frame_data
            except Exception as e:
                print("ERROR: ", e)
            message_to_feagi['timestamp'] = datetime.now()
            message_to_feagi['counter'] = msg_counter
            sleep(feagi_settings['feagi_burst_speed'])
            print(message_to_feagi)
            pns.signals_to_feagi(message_to_feagi, feagi_ipu_channel, agent_settings, feagi_settings)
            message_to_feagi.clear()

    except KeyboardInterrupt:
        print("\nStreaming stopped by user")
