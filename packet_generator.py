import random

def generate_packets(num_packets, flow_type):
    # contains a list of triggers 
    # each trigger is a pair of state_from and state_to
    # if there is no trigger, the value is of state_from and state_to is -1
    # we never end up using state_to in the code but keeping in case we should 
    packets = [] 
    if flow_type == 'interesting':
        # sequential transitions 
        for i in range(num_packets):
            state_from = i % 10 + 1
            state_to = (i + 1) % 10 + 1
            packets.append((state_from, state_to))
    elif flow_type == 'noise':
        # random transitions
        for i in range(num_packets):
            state_from = random.randint(1, 9)
            state_to = random.randint(2, 10)
            # no complete transition from 9 to 10
            if state_from != 9 or state_to != 10:
                packets.append((state_from, state_to))
            else:
                packets.append((-1, -1))
    else:
        packets = [(-1, -1) for i in range(num_packets)]
    return packets
""" 
when you call this, you will get a list of 60k flows such 
that each flow has a list of the packets which contain the triggers

it is already random so we don't need to randomly choose a flow
"""
def generate_flows():
    # There are n ≈ 60, 000 active flows in the system.
    num_flows = 60000 
    flows = []
    for i in range(num_flows):
        flow_type = random.choices(['interesting', 'noise', 'random'], weights=(30, 30, 40), k=1)[0]
        # Each flow is made up of m≈100±40 packets.
        num_packets = random.randint(60, 140) 
        packets = generate_packets(num_packets, flow_type)
        flows.append((i, flow_type, packets))
    # returns the flow_id, flow type, and packets associated with the flow type 
    return flows
