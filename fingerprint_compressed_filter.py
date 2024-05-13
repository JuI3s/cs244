import random

def generate_hash_functions(n):
    hash_functions = []
    for i in range(n):
        def hash_func(x, i=i):
            return hash((x, i))
        hash_functions.append(hash_func)
    return hash_functions


class FCF:
    def __init__(self, hash_fns, table_size, cells_per_bucket, fingerprint_size, deletion_window=6000000):
        assert table_size % hash_fns == 0
        self.deletion_window = deletion_window
        self.hash_fns = generate_hash_functions(hash_fns)
        self.subtable_size = table_size // hash_fns
        self.table = [[[] for _ in range(self.subtable_size)] for _ in range(hash_fns)]
        self.cells_per_bucket = cells_per_bucket
        self.fingerprint_size = fingerprint_size
        self.fingerprint_generator = lambda x: hash((x, hash_fns + 1)) % (2 ** fingerprint_size)
        self.required_memory = table_size * cells_per_bucket * (fingerprint_size + 8) # add for state
        self.num_ops = 0
        print(f"FCF requires {self.required_memory} bits of memory")
    def insert_entry(self, flow_id, state):
        indices = [fn(flow_id) % self.subtable_size for fn in self.hash_fns]
        fingerprint = self.fingerprint_generator(flow_id)
        subtable_entries = [self.table[i][indices[i]] for i in range(len(self.hash_fns))]
        # find the entry with the fewest elements
        min_index = min(range(len(subtable_entries)), key=lambda i: len(subtable_entries[i]))
        # add (fingerprint, state) to the entry
        subtable_entries[min_index].append((1, fingerprint, state))
        self.handle_deletions()
    def modify_entry(self, flow_id, state):
        indices = [fn(flow_id) % self.subtable_size for fn in self.hash_fns]
        fingerprint = self.fingerprint_generator(flow_id)
        subtable_entries = [self.table[i][indices[i]] for i in range(len(self.hash_fns))]
        for entry in subtable_entries:
            for i, (flag, f, s) in enumerate(entry):
                if f == fingerprint:
                    entry[i] = (1, fingerprint, state)
        self.handle_deletions()
    def lookup_entry(self, flow_id):
        result = None
        indices = [fn(flow_id) % self.subtable_size for fn in self.hash_fns]
        fingerprint = self.fingerprint_generator(flow_id)
        subtable_entries = [self.table[i][indices[i]] for i in range(len(self.hash_fns))]
        for entry in subtable_entries:
            for i, (flag, f, s) in enumerate(entry):
                if f == fingerprint:
                    if result is not None:
                        return "IDK"
                    entry[i] = (1, f, s)
                    result = s
        self.handle_deletions()
        return result
    def delete_entry(self, flow_id):
        indices = [fn(flow_id) % self.subtable_size for fn in self.hash_fns]
        fingerprint = self.fingerprint_generator(flow_id)
        subtable_entries = [self.table[i][indices[i]] for i in range(len(self.hash_fns))]
        for entry in subtable_entries:
            for i, (flag, f, s) in enumerate(entry):
                if f == fingerprint:
                    del entry[i]
    def handle_deletions(self):
        self.num_ops += 1
        if self.num_ops >= self.deletion_window:
            self.num_ops = 0
            for i in range(len(self.hash_fns)):
                for j in range(self.subtable_size):
                    self.table[i][j] = [(0, f, s) for (flag, f, s) in self.table[i][j] if flag == 1]

# Check accuracy of FCF
def test_fcf():
    fcf = FCF(hash_fns=4, table_size=1000, cells_per_bucket=4, fingerprint_size=8)
    # insert 2 flows
    fcf.insert_entry(1, "State 1")
    fcf.insert_entry(2, "State 2")
    # lookup 2 flows
    assert fcf.lookup_entry(1) == "State 1"
    assert fcf.lookup_entry(2) == "State 2"
    # modify flow 1
    fcf.modify_entry(1, "Modified State 1")
    # lookup flow 1
    assert fcf.lookup_entry(1) == "Modified State 1"
    # delete flow 2
    fcf.delete_entry(2)
    # lookup flow 2
    assert fcf.lookup_entry(2) == None
    # insert flow 3
    fcf.insert_entry(3, "State 3")
    # lookup flow 3 2000 times
    for _ in range(2004):
        assert fcf.lookup_entry(3) == "State 3"
    # flow 1 should be deleted by now
    assert fcf.lookup_entry(1) == None

    
test_fcf()
