
import dill
import pythonate_interactive_5_module_sysc
body = dill.loads(b'\x80\x04\x95\xe3\x01\x00\x00\x00\x00\x00\x00\x8c.deltalanguage.wiring._node_classes.node_bodies\x94\x8c\x11PyInteractiveBody\x94\x93\x94)\x81\x94}\x94\x8c\x08callback\x94\x8c\ndill._dill\x94\x8c\x10_create_function\x94\x93\x94(h\x06\x8c\x0c_create_code\x94\x93\x94(K\x01K\x00K\x00K\x04K\x04KCC\\|\x00\xa0\x00\xa1\x00d\x01\x19\x00}\x01t\x01d\x02|\x01\x9b\x00\x9d\x02\x83\x01\x01\x00|\x00\xa0\x00\xa1\x00d\x03\x19\x00}\x02|\x02r8t\x01d\x04|\x02\x9b\x00\x9d\x02\x83\x01\x01\x00|\x00\xa0\x00\xa1\x00d\x05\x19\x00}\x03|\x00\xa0\x02|\x01|\x03\x17\x00d\x06\x17\x00\xa1\x01\x01\x00q\x00d\x00S\x00\x94(N\x8c\x03num\x94\x8c\x0freceived num = \x94\x8c\x03opt\x94\x8c\rreceived opt=\x94\x8c\x03val\x94K\x01t\x94\x8c\x07receive\x94\x8c\x05print\x94\x8c\x04send\x94\x87\x94(\x8c\x04node\x94h\x0ch\x0eh\x10t\x94\x8c\x16test/test_pythonate.py\x94\x8c\x10interactive_func\x94K\x0eC\x0e\x00\x03\x0c\x01\x0e\x01\x0c\x01\x04\x01\x0e\x01\x0c\x01\x94))t\x94R\x94}\x94\x8c\x05print\x94h\x06\x8c\t_get_attr\x94\x93\x94\x8c\x08builtins\x94\x8c\x05print\x94\x86\x94R\x94sh\x19NN}\x94Nt\x94R\x94sb.')
sysc_num = dill.loads(b'...')
sysc_val = dill.loads(b'...')
sysc_opt = dill.loads(b'...')
sysc_output = dill.loads(b'...')
class SysBridgeNode:
    def __init__(self): 
        self.in_queues = dict.fromkeys(["num", "val", "opt"]) 
    def send(self, output=None):
        if output is not None:
            pythonate_interactive_5_module_sysc.send("output", sysc_output.pack(output))
    def receive(self, *args: str):
        if args: 
            in_queue = {name: in_q for name, in_q in self.in_queues.items() if name in args}
        else: 
            in_queue = self.in_queues 
        values = {} 
        if in_queue: 
             for req in in_queue: 
                 values[req] = pythonate_interactive_5_module_sysc.receive(req)
        if len(values) == 1 and args: 
            return values[list(values)[0]] 
        else: 
            return values
node = SysBridgeNode()
