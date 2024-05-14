import random
from urllib.parse import _ResultMixinStr
from state_machine import StateMachine
from packet_generator import generate_flows
from direct_bloom_filter import DirectBloomFilter
from fingerprint_compressed_filter import FCF
from stateful_bloom_filter import StatefulBloomFilter
from collections import deque
from packet_generator import generate_packets

def simulate_fcf_filter(config):
    results = []
    flows = generate_flows()
    # give every flow also a "result" field that is either fp, fn, dk, or tp
    flows = [["Haven't Started", flow_id, flow_type, deque(packet)] for (flow_id, flow_type, packet) in flows]
    for memory_size, table_size, hash_functions, cells_per_bucket, fingerprint_size in config:
        bloom_filter = FCF(hash_fns=hash_functions, table_size=table_size, cells_per_bucket=cells_per_bucket, fingerprint_size=fingerprint_size)
        false_positives = 0
        false_negatives = 0
        dont_knows = 0

        total_flows = 0
        target_flows = 1000
        while total_flows < target_flows:
            # pick a random flow index
            flow_index = random.randint(0, len(flows) - 1)
            result, flow_id, flow_type, packets = flows[flow_index]
            # If the flow has not started yet, start it
            packet = packets.popleft()
            if result == "Haven't Started" and -1 not in packet:
                bloom_filter.insert_entry(flow_id, 0)
                flows[flow_index][0] = "Started"
            # Process the packet if it hasn't been given a result already
            if -1 not in packet:
                curr_state, next_state = packet
                read_state = bloom_filter.lookup_entry(flow_id)
                if read_state == curr_state:
                    bloom_filter.delete_entry(flow_id)
                    bloom_filter.insert_entry(flow_id, next_state)
                if read_state == 10 and flow_type == "interesting":
                    flows[flow_index][0] = "TP"
                    bloom_filter.delete_entry(flow_id)
                if read_state == 10 and flow_type != "interesting":
                    flows[flow_index][0] = "FP"
                    bloom_filter.delete_entry(flow_id)
                elif flows[flow_index][0] == "TP": # If we have already marked as TP, don't change it
                    flows[flow_index][0] = "TP"
                elif read_state == "IDK":
                    flows[flow_index][0] = "IDK"
                elif flow_type == "interesting" and read_state != 10 and len(packets) == 0:
                    flows[flow_index][0] = "FN"
            if len(packets) == 0:
                result = flows[flow_index][0]
                if result == "FP":
                    false_positives += 1
                elif result == "FN":
                    false_negatives += 1
                elif result == "IDK":
                    dont_knows += 1
                flows.pop(flow_index)
                total_flows += 1
                flows.append(["Haven't Started", flow_id, flow_type, deque(generate_packets(random.randint(60, 140), flow_type))])
        # get the next

        results.append({
            'Memory Size': memory_size,
            'Table Size': table_size,
            'Hash Functions': hash_functions,
            'Cells per Bucket': cells_per_bucket,
            'False Positive': 100 * false_positives / target_flows,
            'False Negative': 100 * false_negatives / target_flows,
            "Don't Know": 100 * dont_knows / target_flows
        })
    print(results)
    return results

def simulate_dbf_sbf_filter(filter_class, config, filter_name):
    flows = generate_flows()
    results = []

    for memory_size, num_cells, hash_count in config:
        bloom_filter = filter_class(num_cells=num_cells, hash_count=hash_count)
        false_positives = 0
        false_negatives = 0
        dont_knows = 0

        for index, (flow_id, flow_type, packets) in enumerate(flows):
            state_machine = StateMachine()

            for (state_from, state_to) in packets:
                current_state = state_machine.get_state()
                if state_from != -1: 
                    state_machine.transition_state() 
                    bloom_filter.insert_entry(flow_id, state_to) 

                # Check state in Bloom Filter
                response = bloom_filter.lookup_entry(flow_id)
                
                if (filter_name == 'Stateful Bloom Filter'):
                # check dont know 
                    if response == "IDK":
                        dont_knows += 1

                if (flow_type != 'interesting' and response == 10):
                    false_positives += 1
                if (flow_type == 'interesting' and index == len(flows) - 1):
                    if (response != 10):
                        false_negatives += 1

        results.append({
            'Memory Size': memory_size,
            'Hash Functions': hash_count,
            'Num Cells': num_cells,
            'False Positive': 100 * false_positives / 60000,
            'False Negative': 100 * false_negatives / 60000,
            "Don't Know": 100 * dont_knows / 60000
        })
    print(results)
    return results

simulate_fcf_filter([(516096, 6 * 1024, 3, 6, 10)])
simulate_fcf_filter([(1081344, 8* 1024, 4, 6, 18)])
simulate_fcf_filter([(2162688, 16*1024, 4, 6, 18)])
# simulate_dbf_sbf_filter(DirectBloomFilter,  [(786432, 256000, 3)], 'Direct Bloom Filter')
# simulate_dbf_sbf_filter(DirectBloomFilter,  [(1572864, 512000, 4)], 'Direct Bloom Filter')
# simulate_dbf_sbf_filter(DirectBloomFilter,  [(3145728, 1000000, 5)], 'Direct Bloom Filter')

simulate_dbf_sbf_filter(StatefulBloomFilter,  [(524288, 128000, 3)], 'Stateful Bloom Filter')
simulate_dbf_sbf_filter(StatefulBloomFilter,  [(1048576, 256000, 4)], 'Stateful Bloom Filter')
simulate_dbf_sbf_filter(StatefulBloomFilter,  [(2097152, 512000, 5)], 'Stateful Bloom Filter')


