import expipe.io
import expipe.io.axona
import datetime
import os
import shutil

# TODO add test data


def test_import_axona_data():
    # experiment = expipe.io.load_experiment("vistrack-lasse-2016-03-02-1")
    # experiment = expipe.io.load_experiment(project="vistrack", subject="lasse", date="2016-03-02")
    if os.path.exists('/tmp/test'):
        shutil.rmtree('/tmp/test')
    os.mkdir('/tmp/test')
    
    exdir_path = "/tmp/test/test.exdir"
    
    axona_filename = "/home/milad/Dropbox/repos/neuroscience/mros/DATA/r1692_151116_Bars/r1692d151116s13.set"
    # axona_filename = "/home/milad/Dropbox/cinpla-shared/project/axonaio/2016-03-02-083928-1596/raw/02031602.set"
    
    if not os.path.exists(axona_filename):
        print("Sorry, this test cannot be run. We need an open Axona test file.")
        return
    
    expipe.io.axona.convert(axona_filename, exdir_path)
    
    expipe.io.axona.generate_analog_signals(exdir_path)
    expipe.io.axona.generate_spike_trains(exdir_path)
    expipe.io.axona.generate_clusters(exdir_path)
    expipe.io.axona.generate_units(exdir_path)    
    expipe.io.axona.generate_inp(exdir_path)    
    expipe.io.axona.generate_tracking(exdir_path)    
