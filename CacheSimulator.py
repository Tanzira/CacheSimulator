from __future__ import division
import math as m
import sys
import random 
class Cache:
    '''
    initializes cache size, way and block size
    n = way
    num_set = number of set
    '''
    def __init__(self, cache_size, block_size, n, debug, policy):
        self.cache_size = cache_size
        self.n = n
        self.block_size = block_size
        self.num_sets = int(cache_size /(block_size * n))
        self.hit_count = 0
        self.total_count = 0
        self.debug = debug
        self.policy = policy
        cache, queue = {}, {}
        for i in range(self.num_sets):
            cache[i], queue[i] = [], [-1] * self.n
            for _ in range(n):
                cache[i].append({'tag': None, 'valid': 0, 'dirty' : 0})
        self.cache, self.queue = cache, queue

    def log(self, ob, msg = ""):
        if self.debug:
            print(msg, ob)
    '''
    places an entry in a free frame
    '''
    def place_in_cache(self, address, free_frame, op):
        tag, set_idx, offset = address
        entry = self.cache[set_idx][free_frame]
        entry['tag'] = tag
        entry['valid'] = 1
        entry['dirty'] = 0
        if op == 'W':
            entry['dirty'] = 1
        


    '''
    Translates the hex to binary
    returns tag, set index and offset
    '''
    def translate(self, address):
        binary_string = bin(int(address, 16))[2:]
        gap = "".join("0" for _ in range(48 - len(binary_string)))
        binary_string = gap + binary_string
        offset_size = int(m.log(self.block_size, 2))
        offset = binary_string[-offset_size:]
        binary_string = binary_string[:-offset_size]
        set_length = int(m.log(self.num_sets, 2))
        if set_length > 0:
            set_idx = int(binary_string[ -set_length: ], 2)
            tag = binary_string[0 : -set_length]
        else:
            set_idx = 0
            tag = binary_string
        tag = int(tag, 2)
        return tag, set_idx, offset

    '''
    returns empty frame slot
    If no free frame then return None
    '''
    def get_free_frame(self, address):
        _, set_idx, _ = address
        for i in range(len(self.cache[set_idx])):
            if self.cache[set_idx][i]['tag'] == None:
                return i
        return -1
    '''
    returns a frame that needs to be overwritten
    '''
    def get_overwrite_frame(self, address):
        if self.policy == 'lru':
            _, set_idx, _ = address
            queue = self.queue[set_idx]
            tag = queue[-1]
            self.log(tag, " tag")
            for i in range(self.n):
                if tag == self.cache[set_idx][i]['tag']:
                    self.log(i, " get overwrite frame")
                    return i
        else:
            return random.randint(0, self.n)

    def record(self, address):
        if self.policy != 'lru':
            return
        tag, set_idx, _ = address
        queue = self.queue[set_idx]
        if tag not in queue:
            queue = [tag] + queue[:-1]
            self.queue[set_idx] = queue
            return
        for i in range(len(queue)):
            if tag == queue[i]:
                queue.remove(tag)
                queue = [tag] + queue
                self.queue[set_idx] = queue
                break            
    '''
    writes the value back into memory
    '''
    def write_back(self, frame, address):
        tag, set_idx, offset = address
        old_tag = self.cache[set_idx][frame]['tag']
    '''
    returns true if given address is available in cache
    '''
    def is_hit(self, address, op):
        tag, set_idx, offset = address
        for entry in self.cache[set_idx]:
            if tag == entry['tag']:
                self.log("hit")
                if op == 'W':
                    entry['dirty'] = 1
                return True
        return False
    
    '''
    returns hit rate and miss rate
    '''
    def get_stats(self):
        hit_rate = (self.hit_count/self.total_count) * 100
        miss_rate = 100 - hit_rate
        return round(hit_rate, 2), round(miss_rate, 2)
    '''
    Formats the output
    '''    
    def tostring(self):
        output = "Queue: " + str(self.queue) + "\n"
        for key in self.cache.keys():
            output += str(key) + ": " + str(self.cache[key]) + "\n"
        return output
    '''
    places the next frame where it should be gone
    '''
    def next_frame(self, address, op):
        address = self.translate(address)
        tag, set_idx, offset = address
        self.log((tag, set_idx, offset), " Next frame")
        self.total_count += 1
        
        if self.is_hit(address, op):
            self.hit_count += 1
        else:
            free_frame = self.get_free_frame(address)
            if free_frame == -1:
                free_frame = self.get_overwrite_frame(address)
                if self.cache[set_idx][free_frame]['dirty'] == 1:
                    self.write_back(free_frame, address)
            self.place_in_cache(address, free_frame, op)
        self.record(address)


def __main__():
    args_len = len(sys.argv)
    i = 1
    multiplier = {'kb': 1024, 'mb': 1048576}
    commands = {"block_size" : 64, "way" : 16, "cache_memory": 1048576, "debug": False}
    while(i < args_len):
        arg = sys.argv[i]
        if i == 1:
            if arg in ["-help", "--help", "-h"]:
                help_text = '''
Usage:
    run_sim.sh <file_name> [--option <arg>]
Options:
    -h --help                       Show this screen.
    --cache_memory <size>[B|KB|MB]  Memory size in B, KB or MB
    --block_size <size>[B|KB|MB]    Memory size in B, KB or MB
    --way <n>                       Number of ways in set associative cache
Example:
    ./run_sim.sh 1KB_64B --cache_memory 1KB --block_size 64B --way 16
                '''
                print(help_text)
                return
            file_name = arg
            i = i + 1
        elif arg[0] == "-":
            arg_old = arg + ""
            arg = arg.replace("-", "")
            if arg not in commands:
                print("Unrecognized argument: ", arg_old)
                return
            if arg == "debug":
                commands["debug"] = True
                i = i + 1
                continue
            i = i + 1
            if i > args_len:
                print("No value found for argument bal: ", arg_old)
                return
            try:
                val = sys.argv[i]
                if arg in ["cache_memory", "block_size"]:
                    if val[-2:].lower() in multiplier:
                        val = int(val[:-2]) * multiplier[val[-2:].lower()]
                    elif val[-1].lower() == 'b':
                        val = int(val[:-1])
                    else:
                        val = int(val)
                commands[arg] = int(val)
                i = i + 1
            except :
                print("Value Error!: ", val)
                return
        else:
            print("Unrecognized argument:", arg)
            return
    block_size = commands["block_size"]
    way =  commands["way"]
    cache_size = commands["cache_memory"]
    debug = commands["debug"]
    if block_size > cache_size:
        print("Block size can't be greater than cache size.")
        return
    cacheob = Cache(cache_size, block_size, way, debug, 'lru')
    with open(file_name, 'r') as file:
        for line in file.readlines():
            try:
                pc, op, add = line.split(' ')
                cacheob.next_frame(add.strip(), op.strip())
            except:
                continue
    result = cacheob.get_stats()[1]
    print("Cache miss rate: " + "{0:.2f}".format(result) + "%")
        
__main__()