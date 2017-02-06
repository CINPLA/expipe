import expipe.io
from expipe.io.axona import AxonaFilerecord
import datetime
import numpy as np


def test_load_experiment():
    project = expipe.io.get_project("ida_tracking")
    action = project.require_action('test')
    #action.location = {'gampræva': 'nordnorge'}
    tracking = action.require_module("test2", template="analysis_analysis")
    # tracking._firebase.set({"blah": "græv"})
    print(tracking._firebase.get("box_size"))
    # print(action)
    # print(action.modules)
    # print("Modules:")
    # for i in action.modules:
    #     print(i)
    # if "tracking" in action.modules:
    #     print(action.modules["tracking"].attrs)
    # 
    # afr = action.require_filerecord(AxonaFilerecord)
    # afr.import_file("/home/svenni/Dropbox/studies/cinpla/cinpla-shared/project/axonaio/grid_data/03011701.set")
    # afr.parse_tracking()
    
    
