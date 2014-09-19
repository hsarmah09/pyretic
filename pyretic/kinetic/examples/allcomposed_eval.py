from pyretic.lib.corelib import *
from pyretic.lib.std import *

from pyretic.kinetic.fsm_policy import *
from pyretic.kinetic.drivers.json_event import JSONEvent
from pyretic.kinetic.smv.model_checker import *


from pyretic.kinetic.apps.auth_web import *
from pyretic.kinetic.apps.auth_8021x import *
from pyretic.kinetic.apps.ids import *
from pyretic.kinetic.apps.gardenwall import *
from pyretic.kinetic.apps.mac_learner import *
from pyretic.kinetic.apps.rate_limiter import *
from pyretic.kinetic.apps.monitor import *

#####################################################################################################
# App launch
#  - pyretic.py pyretic.kinetic.apps.allcomposed
#
# Mininet Generation
#  - sudo mn --controller=remote,ip=127.0.0.1 --mac --arp --switch ovsk --link=tc --custom example_topos.py --topo=ratelimit
#
# Events to allow traffic "h1 ping h2"
#  - python json_sender.py -n auth -l True --flow="{srcip=10.0.0.1}" -a 127.0.0.1 -p 50001}
#  - python json_sender.py -n auth -l True --flow="{srcip=10.0.0.2}" -a 127.0.0.1 -p 50001}
#
# Events to block traffic "h1 ping h2"
#  - python json_sender.py -n infected -l True --flow="{srcip=10.0.0.1}" -a 127.0.0.1 -p 50001}
#
#
#
#####################################################################################################


def main():

    pol1 = auth_web()
    pol2 = auth_8021x()
    pol3 = ids()
    pol4 = rate_limiter()

    # For NuSMV
    cfsm_def, smv_str = fsm_def_compose(pol1.fsm_def, pol2.fsm_def,'+')
    cfsm_def2, smv_str = fsm_def_compose(cfsm_def, pol3.fsm_def,'>>')
    cfsm_def3, smv_str = fsm_def_compose(cfsm_def2, pol4.fsm_def,'>>')
    mc = ModelChecker(smv_str,'allcomposed')  

    ## Add specs 
    mc.add_spec("FAIRNESS\n  authenticated_web;")
    mc.add_spec("FAIRNESS\n  authenticated_1x;")
    mc.add_spec("FAIRNESS\n  infected;")

    org_smv_str = mc.get_smv_str()

    verify_time_list_map = {}   #  { nspec : [list of measurements] } 
    nspec = [1,20,40,60,80,100]
    for i in nspec:
        mc.set_smv_str(org_smv_str)
        spec_list = mc.spec_builder(cfsm_def3,i)
        for s in spec_list:
            mc.add_spec(s)
    
        mc.save_as_smv_file()
        verify_time_list = []
    
        for j in range(1000):
            verify_time_list.append(mc.verify()*1000)
            time.sleep(0.05)
        verify_time_list_map[i] = verify_time_list
    
    print 'Save result. '
    pickle_fd = open('./verify_composed_map.p','wb')
    pickle.dump(verify_time_list_map,pickle_fd)
    pickle_fd.close() 

    print "=== Verification takes (ms): ",verify_time_list[0],"===\n"

    ask_deploy()

    return ( (pol1 + pol2) >> pol3 >> pol4 ) >> monitor(50004)
