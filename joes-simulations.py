import random
import datetime
from collections import deque

def generate_hash_fn(seed):
    def hash_fn(x):
        random.seed(hash((x, seed)))
        result = random.randint(0, 2**64)
        random.seed(int(datetime.datetime.now().timestamp()))
        return result
    return hash_fn

def generate_hash_functions(n):
    hash_functions = []
    for i in range(n):
        hash_functions.append(generate_hash_fn(i))
    return hash_functions

class DBF:
    def __init__(self, hash_fns, table_size, deletion_window=6000000):
        self.table = [(0, "unused")] * table_size
        self.hash_fns = generate_hash_functions(hash_fns)
        self.deletion_window = deletion_window
        self.time_before_deletion = self.deletion_window
    def insert_entry(self, flow_id, state):
        indices = [hash_fn((flow_id, state)) % len(self.table) for hash_fn in self.hash_fns]
        # increment the count of each index
        for index in indices:
            self.table[index] = (min(4, self.table[index][0] + 1), "used")
    def delete_entry(self, flow_id, state):
        indices = [hash_fn((flow_id, state)) % len(self.table) for hash_fn in self.hash_fns]
        # decrement the count of each index
        for index in indices:
            self.table[index] = (max(self.table[index][0] - 1, 0), self.table[index][1]) # preserve the state
    def handle_deletions(self):
        self.time_before_deletion = self.deletion_window
        print("deleting {0} entries".format(len([entry for entry in self.table if entry[1] == "unused" and entry[0] > 0])))
        for i in range(len(self.table)):
            if self.table[i][1] == "unused":
                self.table[i] = (0, "unused")
            else:
                self.table[i] = (self.table[i][0], "unused")
    def modify_entry(self, flow_id, og_state, new_state):
        self.delete_entry(flow_id, og_state)
        self.insert_entry(flow_id, new_state)
    def process_packet(self, flow_id, packet):
        self.time_before_deletion -= 1
        if packet == (1, 2): # first real packet
            self.insert_entry(flow_id, 2)
        elif -1 not in packet:
            self.modify_entry(flow_id, packet[0], packet[1])
        if self.time_before_deletion <= 0:
            self.handle_deletions()
    def lookup_entry(self, flow_id, state):
        indices = [hash_fn((flow_id, state)) % len(self.table) for hash_fn in self.hash_fns]
        counts = [self.table[index][0] for index in indices]
        return all(count > 0 for count in counts)

class FCF:
    def __init__(self, hash_fns, table_size, cells_per_bucket, fingerprint_size, deletion_window=6000000):
        self.cells_per_bucket = cells_per_bucket
        self.hash_fns = generate_hash_functions(hash_fns)
        self.subtable_size = table_size // hash_fns
        self.table = [[[] for __ in range (self.subtable_size)] for _ in range(hash_fns)]
        self.deletion_window = deletion_window
        self.time_before_deletion = self.deletion_window
        fingerprint_hasher = generate_hash_fn(hash_fns + 8)
        self.fingerprint_fn = lambda x: fingerprint_hasher(x) % (2 ** fingerprint_size)
        self.started_ids = set()
        
    def insert_entry(self, flow_id, state):
        if(self.lookup_entry(flow_id) != None):
            return
        potential_indices = [hash_fn(flow_id) % self.subtable_size for hash_fn in self.hash_fns]
        sizes = [len(self.table[i][potential_indices[i]]) for i in range(len(potential_indices))]
        smallest_bucket_index = sizes.index(min(sizes))
        self.table[smallest_bucket_index][potential_indices[smallest_bucket_index]].append((self.fingerprint_fn(flow_id), state, 1))
        if len(self.table[smallest_bucket_index][potential_indices[smallest_bucket_index]]) > self.cells_per_bucket:
            cnt = 0
            for st in self.table:
                for cl in st:
                    cnt += len(cl)
            print("utilization: ", cnt / (self.subtable_size * self.cells_per_bucket * len(self.hash_fns)))
            self.handle_deletions()
            print(f"WARNING: Bucket overflow. total of {len(self.started_ids)} flows started.")
        
    def modify_entry(self, flow_id, og_state, new_state):
        deletions = self.delete_entry(flow_id, og_state)
        if deletions > 0:
            self.insert_entry(flow_id, new_state)
        
    def lookup_entry(self, flow_id, st=None):
        potential_indices = [hash_fn(flow_id) % self.subtable_size for hash_fn in self.hash_fns]
        # if the fingerprint occurs more than once, return IDK
        result = None
        for i in range(len(potential_indices)):
            for fingerprint, state, _ in self.table[i][potential_indices[i]]:
                if fingerprint == self.fingerprint_fn(flow_id):
                    if result is not None:
                        return "IDK"
                    result = state
        if st is None:
            return result
        return result == st

    def delete_entry(self, flow_id, og_state):
        potential_indices = [hash_fn(flow_id) % self.subtable_size for hash_fn in self.hash_fns]
        num_deleted = 0
        for i in range(len(potential_indices)):
            for j, (fingerprint, state, _) in enumerate(self.table[i][potential_indices[i]]):
                if fingerprint == self.fingerprint_fn(flow_id) and state == og_state:
                    num_deleted += 1
                    del self.table[i][potential_indices[i]][j]
        return num_deleted
        
    def process_packet(self, flow_id, packet):
        self.time_before_deletion -= 1
        if -1 not in packet and flow_id not in self.started_ids:
            self.started_ids.add(flow_id)
            self.insert_entry(flow_id, max(1, packet[1]))
        elif -1 not in packet:
            self.modify_entry(flow_id, packet[0], packet[1])
        if self.time_before_deletion <= 0:
            self.handle_deletions()

    def handle_deletions(self):
        self.time_before_deletion = self.deletion_window
        # delete all entries with flag 0
        for i in range(len(self.table)):
            for j in range(len(self.table[i])):
                self.table[i][j] = [(id, state, 0) for (id,state, flag) in self.table[i][j] if flag == 1]


next_flow_id = 0
def make_flow_id():
    global next_flow_id
    next_flow_id += 1
    return next_flow_id

def make_packets(num_transitions):
    numpackets = random.randint(60, 140)
    packets = [(-1, -1) for _ in range(numpackets)]
    state = 1
    indices = sorted(random.sample(range(numpackets), num_transitions))
    for i in indices:
        packets[i] = (state, state + 1)
        state += 1
    return deque(packets)
    
def make_flow(typ):
    if typ == 'i':
        return ('i', make_flow_id(), make_packets(9))
    elif typ == 'n':
        return ('n', make_flow_id(), make_packets(8))
    else:
        return ('r', make_flow_id(), make_packets(0))

def make_flows(num_flows):
    types = ['i'] * 3 + ['n'] * 3 + ['r'] * 3
    return [make_flow(random.choice(types)) for _ in range(num_flows)] 


"""
We can define rules for the various operations. Below,
where we say hash the flow, we mean the operation takes
effect at each cell the flow hashes to.
• Insertion. Hash the flow. If the cell counter is 0, write
the new value and set the count to 1. If the cell value
is DK, increment the count. If the cell value equals
the flow value, increment the count. If the cell value
does not equal the flow value, increment the count but
change the cell to DK.
• Modify. Hash the flow. If the cell value is DK, leave
it. If the current count is 1, change the cell value. If
current count is exceeds 1, change the cell value to DK.
• Deletion. Hash the flow. If the count is 1, reset cell to
0. If the count it at least 1, decrement count, leaving
the value or DK as is.
• Lookup. Check all cells associated with a flow. If all
cell values are DK, return DK. If all cell values have
value i or DK (and at least one cell has value i), return
i. If there is more than one value in the cells, the item
is not in the set.
    """
class SBF:
    def __init__(self, hash_fns, table_size, deletion_window=6000000):
        self.table = [(0, 0, "unused")] * table_size # (state, count, used flag)
        self.hash_fns = generate_hash_functions(hash_fns)
        self.deletion_window = deletion_window
        self.time_before_deletion = self.deletion_window
    def insert_entry(self, flow_id, state):
        indices = [hash_fn(flow_id) % len(self.table) for hash_fn in self.hash_fns]
        for index in indices:
            if self.table[index][1] == 0:
                self.table[index] = (state, 1, "used")
            elif self.table[index][0] == state:
                self.table[index] = (state, self.table[index][1] + 1, "used")
            elif self.table[index][0] != state:
                self.table[index] = ("IDK", self.table[index][1] + 1, "used")
    def modify_entry(self, flow_id, state):
        indices = [hash_fn(flow_id) % len(self.table) for hash_fn in self.hash_fns]
        for index in indices:
            if self.table[index][1] == 1:
                self.table[index] = (state, self.table[index][1], "used")
            else:
                self.table[index] = ("IDK", self.table[index][1], "used")
    def process_packet(self, flow_id, packet):
        self.time_before_deletion -= 1
        if packet == (1, 2): # first real packet
            self.insert_entry(flow_id, 2)
        elif -1 not in packet:
            self.modify_entry(flow_id, packet[1])
        if self.time_before_deletion <= 0:
            self.handle_deletions()
    def handle_deletions(self):
        self.time_before_deletion = self.deletion_window
        for i in range(len(self.table)):
            if self.table[i][2] == "unused":
                self.table[i] = (0, 0, "unused")
            else:
                self.table[i] = (self.table[i][0], self.table[i][1], "unused")
    def lookup_entry(self, flow_id, state):
        indices = [hash_fn(flow_id) % len(self.table) for hash_fn in self.hash_fns]
        states = [self.table[index][0] for index in indices]
        # We can only have state and IDK in the table
        if all(s == "IDK" for s in states):
            return "IDK"
        return all(s == "IDK" or s == state for s in states)


filters = [
    SBF(3, 256*1024),
    SBF(4, 512*1024),
    SBF(5, 1024*1024),
    DBF(3, 256*1024),
    DBF(4, 512*1024),
    DBF(5, 1024*1024),
    FCF(3, 6*1024, 6, 10),
    FCF(4, 8*1024, 6, 10),
    FCF(4, 16*1024, 6, 18)
]
for fcf in filters:
    flows = make_flows(60000)
    finished_flows = 0
    fn = 0
    fp = 0
    idk = 0
    total = 0
    while finished_flows < 1000000:
        total += 1
        # pick a random flow
        flow = random.choice(flows)
        # pop the first packet
        packet = flow[2].popleft()
        # process the packet
        fcf.process_packet(flow[1], packet)
        # if the flow is done, increment finished_flows, remove the flow, and make a new flow of the same type
        if not flow[2]:
            if fcf.lookup_entry(flow[1], 10) == "IDK":
                idk += 1
            # if flow is i and state is not 10, increment fn
            elif flow[0] == 'i' and not fcf.lookup_entry(flow[1], 10):
                fn += 1
            # if flow is not i and state is 10, increment fp
            elif flow[0] != 'i' and fcf.lookup_entry(flow[1], 10):
                fp += 1
            finished_flows += 1
            flows.remove(flow)
            flows.append(make_flow(flow[0]))

    # every 1000 flows, print the number of IDKs, FNs, and FPs and the total number of flows processed
    print(f"IDK: {idk}, FN: {fn}, FP: {fp}, Total: {finished_flows}, Total packets: {total}")