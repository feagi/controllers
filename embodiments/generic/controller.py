from time import sleep
from feagi_connector import feagi_interface as feagi
from feagi_connector import pns_gateway as pns
from feagi_connector.version import __version__
from random import randrange

feagi.validate_requirements('requirements.txt')  # you should get it from the boilerplate generator
runtime_data = {}

if __name__ == "__main__":
    print("Ready...")
    config = feagi.build_up_from_configuration()
    feagi_settings = config['feagi_settings'].copy()
    agent_settings = config['agent_settings'].copy()
    default_capabilities = config['default_capabilities'].copy()
    message_to_feagi = config['message_to_feagi'].copy()
    capabilities = config['capabilities'].copy()

    # # # FEAGI registration # # #
    feagi_settings, runtime_data, api_address, feagi_ipu_channel, feagi_opu_channel = \
        feagi.connect_to_feagi(feagi_settings, runtime_data, agent_settings,
                               capabilities,
                               __version__)
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    while True:
        message_from_feagi = pns.message_from_feagi

        # Fetch data such as motor, servo, etc and pass to a function (you make ur own action.
        if message_from_feagi is not None:
            pns.check_genome_status_no_vision(message_from_feagi)
            feagi_settings['feagi_burst_speed'] = pns.check_refresh_rate(
                message_from_feagi, feagi_settings['feagi_burst_speed'])
            obtained_signals = pns.obtain_opu_data(message_from_feagi)

        sleep(feagi_settings['feagi_burst_speed'])  # bottleneck

        message_to_feagi = {"data": {"sensory_data": {"generic_ipu": {
            "iv00_C": {
                (randrange(0, 30), randrange(0, 30), 0): 100
            },
            "o__mot": {
                (0, 0, 0): 100, (2, 0, 0): 20, (4, 0, 0): 60
            }
        }}}}
        pns.signals_to_feagi(message_to_feagi, feagi_ipu_channel,
                             agent_settings, feagi_settings)
        message_to_feagi.clear()
