import mmh3
from bitarray import bitarray
import sys 

class DirectBloomFilter(object):
    def __init__(self, num_cells, hash_count, phase_duration=1000):
        self.num_cells = num_cells
        self.size = num_cells * 3  # Each cell has 3 bits
        self.phase_duration = phase_duration
        self.hash_count = hash_count
        self.bit_array = bitarray(self.size)
        self.bit_array.setall(0)
        self.operations = phase_duration
        self.states = [] # the states that the filter can have at the beginning will be empty 

    def total_size(self):
        int_size = sys.getsizeof(int()) * 8  # Size of an integer in bits
        metadata_size = 5 * int_size  # There are 5 integer attributes
        # Calculate the size of the bit_array attribute
        bit_array_size = self.size  # Size of bit_array in bits
        #function_size = (sys.getsizeof(self.removeExpiredEntries) + sys.getsizeof(self.total_size)) * 8
        # Return the total size
        return metadata_size + bit_array_size # + function_size

    # function that will track the time and remove the entries that are expired based on the 
    # phase_duration
    def handleDeletions(self):
        self.operations -= 1
        if self.operations == 0:
            for i in range(0, self.size, 3):
                if self.bit_array[i] == 0: # if the flag is not set, then the entry should be reset, 
                    self.bit_array[i] = 0
                    self.bit_array[i+1] = 0
                    self.bit_array[i+2] = 0
                else: # reset just the flag timer 
                    self.bit_array[i] = 0
            self.operations = self.phase_duration
        
            
    def insert_entry(self, flow_id, state):
        if state not in self.states:
            self.states.append(state)
        item = f"{flow_id}_{state}"
        for i in range(self.hash_count):
            idx = mmh3.hash(item, i) % self.num_cells
            # Set first bit as timer
            self.bit_array[(idx * 3) % self.size] = 1
            # Get the current counter value
            counter = (self.bit_array[(idx * 3 + 1) % self.size] << 1) | self.bit_array[(idx * 3 + 2) % self.size]
            # Increment the counter, and wrap around to 0 if it's currently 3 (11 in binary)
            counter = (counter + 1) % 4
            # Set the counter bits
            self.bit_array[(idx * 3 + 1) % self.size] = (counter >> 1) & 1
            self.bit_array[(idx * 3 + 2) % self.size] = counter & 1
        self.handleDeletions()
        
    
   
    def delete_entry(self, flow_id):
        
        # lookup the flow and get the old state
        oldstate = self.lookup_entry(flow_id)
        if not oldstate or oldstate == "IDK":
            return False
        
        item = f"{flow_id}_{oldstate}"
        for i in range(self.hash_count):
            idx = mmh3.hash(item, i) % self.num_cells
            # timer bit - paper says not to set the timer flag
            # Get the current counter value
            counter = (self.bit_array[(idx * 3 + 1) % self.size] << 1) | self.bit_array[(idx * 3 + 2) % self.size]
            # Decrement the counter, and set it to 0 if it's currently 0
            counter = max(0, counter - 1)
            # Set the counter bits
            self.bit_array[(idx * 3 + 1) % self.size] = (counter >> 1) & 1
            self.bit_array[(idx * 3 + 2) % self.size] = counter & 1
        self.handleDeletions()



    def modify_entry(self, flow,  newstate):
        
        if newstate not in self.states:
            self.states.append(newstate)
        
        self.delete_entry(flow)
        self.insert_entry(flow, newstate)
    

    def lookup_entry(self, flow_id):
        # go through all the possible states and check if the flow_id is present
        # change to a set
        matches = set()
        for state in self.states:
            item = f"{flow_id}_{state}"
            for i in range(self.hash_count):
                digest = mmh3.hash(item, i) % self.num_cells
                if self.bit_array[(digest * 3) % self.size] == 0: #
                    self.bit_array[(digest * 3) % self.size] = 1
                if not any(self.bit_array[(digest * 3 + 1 + j) % self.size] for j in range(2)):
                    next
                else: 
                    matches.add(state)
        self.handleDeletions()
        if len(matches) == 0:
            return None
        elif len(matches) > 1:
            return "IDK"
        else:
            return matches.pop()
    
  
    # Print bits 3 at a time since each "cell" has 3 bits
    def print_bits(self):
        print("----------------------------------------------------------")
        for i in range(0, self.size, 3):
            chunk = self.bit_array[i:i+3]
            print("".join(map(str, chunk)))
        print("----------------------------------------------------------")

# --------------------------------------------------------------------------------------------
# --------------------------------- Test Functions -----------------------------------------



# Check accuracy of dbf # Joe's test function
def test_dbf():
    dbf = DirectBloomFilter(hash_count=4, num_cells=1000)
    # insert 2 flows
    dbf.insert_entry(1, "State 1") 
    dbf.insert_entry(2, "State 2")
    # lookup 2 flows
 
    assert dbf.lookup_entry(1)  == "State 1"

    assert dbf.lookup_entry(2) == "State 2"
    # modify flow 1
    dbf.modify_entry(1, "Modified State 1")
    # lookup flow 1
    assert dbf.lookup_entry(1) == "Modified State 1"
    # delete flow 2
    dbf.delete_entry(2)
    # lookup flow 2
    assert dbf.lookup_entry(2) == None
    # insert flow 3
    dbf.insert_entry(3, "State 3")
    # lookup flow 3 2000 times
    for _ in range(2004):
        assert dbf.lookup_entry(3) == "State 3"
    # flow 1 should be deleted by now
    assert dbf.lookup_entry(1) == None

    
test_dbf()


