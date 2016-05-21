import ripe.atlas.cousteau

def on_result_response(*args):
    print args[0]


atlas_stream = ripe.atlas.cousteau.AtlasStream()
atlas_stream.timeout(seconds=5)
atlas_stream.connect()
# Measurement results
channel = "result"
# Bind function we want to run with every result message received
atlas_stream.bind_channel(channel, on_result_response)
# Subscribe to new stream for 1001 measurement results
stream_parameters = {"msm": 1001}
atlas_stream.start_stream(stream_type="result", **stream_parameters)

atlas_stream.disconnect()
