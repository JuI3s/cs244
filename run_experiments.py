from urllib.parse import _ResultMixinStr
from state_machine import StateMachine
from packet_generator import generate_flows
from direct_bloom_filter import DirectBloomFilter
from fingerprint_compressed_filter import FCF

def simulate_fcf_filter(config):
    flows = generate_flows()
    results = []

    for memory_size, table_size, hash_functions, cells_per_bucket, fingerprint_size in config:
        bloom_filter = FCF(hash_fns=hash_functions, table_size=table_size, cells_per_bucket=cells_per_bucket, fingerprint_size=fingerprint_size)
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
                if response == "IDK":
                    dont_knows += 1

                if (flow_type != 'interesting' and response == 10):
                    false_positives += 1
                if (flow_type == 'interesting' and index == len(flows) - 1):
                    if (response != 10):
                        false_negatives += 1

        results.append({
            'Memory Size': memory_size,
            'Hash Functions': hash_functions,
            'Cells per Bucket': cells_per_bucket,
            'False Positive': false_positives / 60000,
            'False Negative': false_negatives / 60000,
            "Don't Know": dont_knows / 60000
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
            'False Positive': false_positives / 60000,
            'False Negative': false_negatives / 60000,
            "Don't Know": dont_knows / 60000
        })
    print(results)
    return results
simulate_fcf_filter([(516096, 6000, 3, 6, 10)])
simulate_dbf_sbf_filter(DirectBloomFilter,  [(786432, 256000, 3)], 'Direct Bloom Filter')