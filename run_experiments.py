from urllib.parse import _ResultMixinStr
from state_machine import StateMachine
from packet_generator import generate_flows
#from direct_bloom_filter import DirectBloomFilter
from fingerprint_compressed_filter import FCF

def simulate_filter(filter_class, config, filter_name):
    flows = generate_flows()
    results = []

    for memory_size, table_size, hash_functions, cells_per_bucket, fingerprint_size in config:
        bloom_filter = filter_class(hash_fns=hash_functions, table_size=table_size, cells_per_bucket=cells_per_bucket, fingerprint_size=fingerprint_size)
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
                
                if (filter_name == 'Stateful Bloom Filter' or filter_name == 'Fingerprint Compressed Filter'):
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
            'Hash Functions': hash_functions,
            'Cells per Bucket': cells_per_bucket,
            'False Positive': false_positives / 60000,
            'False Negative': false_negatives / 60000,
            "Don't Know": dont_knows / 60000
        })
    print(results)
    return results
simulate_filter(FCF,  [(516096, 6000, 3, 6, 10)], 'Fingerprint Compressed Filter')