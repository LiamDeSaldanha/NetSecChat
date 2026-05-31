import datetime
import msgpack
import nacl.bindings
import nacl.public
import base64
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
import struct
import hashlib
from Crypto.Hash import BLAKE2s
import hmac
import random
import time
#################### Constants ########################
SERVER_STATIC_PUBLIC_KEY=b'f,^\xc0Cb\xf3\x937\xbf\x11\x14"\xed\x13\x0b\x9f\xe7\xaf;\x94\xb0p\x13\xe1\x94\xdd\x85\xcf\x01\x0bC'

#################### End of Constants #################



"""Used to generate secret"""
def DH(private_key, public_key):
    return nacl.bindings.crypto_scalarmult(n=private_key, p=public_key)

def DH_Generate():
    private_key = nacl.public.PrivateKey.generate()
    return (bytes(private_key), bytes(private_key.public_key))

def AEAD_encrypt(key, counter, plain_text, auth_text):
    chacha = ChaCha20Poly1305(key)
    # 'I' is 32-bit unsigned (4 bytes) -> 0
    # 'Q' is 64-bit unsigned (8 bytes) -> counter, '<' ensures Little-Endian
    counter = struct.pack('<IQ', 0, counter)
    
    return chacha.encrypt(counter, plain_text, auth_text)
    

def AEAD_decrypt(key, counter, encrypted_data, auth_text):
    chacha = ChaCha20Poly1305(key)
    #will be used for conversion from int to byte literal
    counter = struct.pack('<IQ', 0, counter)
    return chacha.decrypt(counter,encrypted_data,auth_text)

def XAEAD_decrypt(key, counter, plain_text, auth_text):
    return nacl.bindings.crypto_aead_xchacha20poly1305_ietf_encrypt(
            plain_text, auth_text, counter, key
        )

def XAEAD_decrypt(key, counter, encrypted_data, auth_text):
    return nacl.bindings.crypto_aead_xchacha20poly1305_ietf_decrypt(
        encrypted_data, auth_text, counter, key
    )

def Hash(inp):
    h = hashlib.blake2s()
    # = input.encode('utf-8')
    h.update(inp)

    hash = h.hexdigest()
    return bytes.fromhex(hash)

def MixHash(input1, input2):
    string =  input1 + input2
    h = hashlib.blake2s()
    h.update(string)
    hash = h.hexdigest()
    return bytes.fromhex(hash)

def Mac(key, inp):
    h = BLAKE2s.new(key=key, digest_bytes = 16)
    h.update(inp)
    mac_tag = h.digest()
    mac_tag = mac_tag.hex()
    return bytes.fromhex(mac_tag)

def HMac(key, inp):
    h = hmac.new(key=key,msg=inp,digestmod = hashlib.blake2s)
    return h.digest()

"""Key derivation chain 1"""
def Kdf1(key, message):
    t_0 = HMac(key, message)
    t_1 = HMac(t_0, b'\x01')
    return (t_1)

"""Key derivation chain 2""" 
def Kdf2(key, message):
    t_0 = HMac(key, message)
    t_1 = HMac(t_0, b'\x01')
    t_2 = HMac(t_0, t_1 + b'\x02')
    return (t_1, t_2)

def Kdf3(key, message):
    t_0 = HMac(key, message)
    t_1 = HMac(t_0, b'\x01')
    t_2 = HMac(t_0, t_1 + b'\x02')
    t_3 = HMac(t_0, t_2 + b'\x03')
    return (t_1, t_2, t_3)

def timestamp1():
    t = time.time()
    print("t",t)
    secs = int(t) + 10 + (1 << 62)  # TAI64: Unix time + leap offset + 2^62 flag
    nsecs = int((t % 1) * 1e6)       # fractional seconds → nanoseconds
    return struct.pack('>QI', secs, nsecs)

def timestamp():
    t = time.time()
    print("t",t)
    #t = 1744377020.21733
    #t =1744366282.5143921
    secs = int(t) + 10 + 2**62
    nsecs = int((t % 1) * 1e6)
    timestamp_ret = secs.to_bytes(8,"big")+nsecs.to_bytes(4,"big")
    return timestamp_ret

class Message:
    def __init__(self):
        self.message_type = 0
        self.reserved_zero = 0
        self.sender_index =0
        self.unencrypted_ephemeral =0
        self.encrypted_static =0
        self.encrypted_timestamp =0
        self.mac1 =0
        self.mac2 = 0

class Initiator:
    def __init__(self,static_public,static_private):
        self.initial_chaining_key = Hash(b'Noise_IKpsk2_25519_ChaChaPoly_BLAKE2s')
        #print(f"# chain_key = Hash(Construction) {self.chaining_key}")
        self.initial_hash = Hash(self.initial_chaining_key + b'WireGuard v1 zx2c4 Jason@zx2c4.com')
        #print(f"# hash = Hash(chain_key || Identifier) {self.hash}")
        
        self.initial_hash = Hash(self.initial_hash + SERVER_STATIC_PUBLIC_KEY)
        #print(f"# hash = Hash(hash || S_R_pub) {self.hash}")
        #set working variables--must be overwritten for threading to work
        self.chaining_key = self.initial_chaining_key
        self.hash = self.initial_hash
        
        self.E_priv_i , self.E_pub_i = DH_Generate()
        #self.E_priv_i =  b'\xac\x03\x18b0\xc4\xf7\xd4*\xa7-\x81&\xfb\xc7\xb3PG0\xae\xa4y0\x90\xe2\xe4\xe2\xa0g\\\x83\xb6'
        #self.E_pub_i = b"\xb1\x13\xb4\xd3\x00R'\x8b\x80\xd1\xcc\xc8X\x1bYf(4\xce&\xd0V\xde\x97\xff\xba2$u\x9b\xe3G"
        print(f"(E_I_priv, E_I_pub) = DH-Generate()  ")
        print(f"E_I_priv {self.E_priv_i}")
        print(f"E_I_pub {self.E_pub_i}")

        
        self.ephemeral_private = self.E_priv_i
        
        self.static_public=static_public
        self.static_private=static_private
        self.last_received_cookie = None
        self.last_sent_mac1 = None
        self.last_received_cookie = None
        
    def new_handshake(self):
        #client_private_key = b'\x99x\x93eP\xdd\xb7h\xd5dJ\xc7\xa5~\x83\xbdX\x04M\xe29\x15\xe2\xf1\xe8\xd8VFk0\xf8\xa1'
        #server_public_key = b'f,^\xc0Cb\xf3\x937\xbf\x11\x14"\xed\x13\x0b\x9f\xe7\xaf;\x94\xb0p\x13\xe1\x94\xdd\x85\xcf\x01\x0bC'
        self.chaining_key = self.initial_chaining_key
        self.hash = self.initial_hash

        msg = Message()
        msg.sender_index =  random.getrandbits(32)#4001697114
        msg.message_type = b'\x01'
        
        msg.reserved_zero = b'\x00\x00\x00'
        
        self.chaining_key = Kdf1(self.chaining_key,self.E_pub_i)
        print(f"chain_key = Kdf1(chain_key, E_I_pub) {self.chaining_key}")
        
        msg.unencrypted_ephemeral = self.E_pub_i
        self.hash = Hash(self.hash+msg.unencrypted_ephemeral)
        print(f"hash = Hash(hash || E_I_pub) {self.hash}")
        
        self.chaining_key,k = Kdf2(self.chaining_key,DH(self.E_priv_i,SERVER_STATIC_PUBLIC_KEY))
        print(f"(chain_key, key1) = Kdf2(chain_key, DH(E_I_priv, S_R_pub))")
        print(F"chain key {self.chaining_key}") 
        print(F"key1 {k}") 
        msg.encrypted_static = AEAD_encrypt(k,0,self.static_public,self.hash)
        print(f"msg_static = AEAD(key1, 0, S_I_pub, hash), an encryption operation {msg.encrypted_static}")
        
        self.hash = Hash(self.hash+msg.encrypted_static)
        print(f"# hash = Hash(hash || msg_static) {self.hash}")
        
        self.chaining_key,k = Kdf2(self.chaining_key,DH(self.static_private,SERVER_STATIC_PUBLIC_KEY))
        print(f"# (chain_key, key2) = Kdf2(chain_key, DH(S_I_priv, S_R_pub))")
        print(f"chainkey {self.chaining_key}")
        print(f"key2 {k}")
        ts = timestamp()
        print(ts)
        msg.encrypted_timestamp = AEAD_encrypt(k,0,ts,self.hash)
        
        print(f"timestamp = AEAD(key2, 0, Timestamp(), hash), an encryption operation {msg.encrypted_timestamp}")
        
        self.hash = Hash(self.hash+msg.encrypted_timestamp)
        print(f" hash = Hash(hash || msg_timestamp) {self.hash}")
        
        concat_msg  = (
        msg.message_type                        
        + msg.reserved_zero                       
        + msg.sender_index.to_bytes(4, 'little')    
        + self.E_pub_i                   
        + msg.encrypted_static                     
        + msg.encrypted_timestamp                    
        )
        print(f"concat message {concat_msg}")
        msg.mac1 = Mac(Hash(b'mac1----' + SERVER_STATIC_PUBLIC_KEY), concat_msg)
        self.last_sent_mac1 = msg.mac1
        msg_beta = msg.message_type + msg.reserved_zero + msg.sender_index.to_bytes(4, 'little') + msg.unencrypted_ephemeral + msg.encrypted_static + msg.encrypted_timestamp + msg.mac1

        if self.last_received_cookie == None:
            msg.mac2 = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        else:
            msg.mac2 = Mac(self.last_received_cookie, msg_beta)


        print(f"mac {msg.mac1}")
        final_msg = {
            "type": msg.message_type,
            "reserved":msg.reserved_zero,
            "sender":msg.sender_index,
            "ephemeral":self.E_pub_i,
            "static":msg.encrypted_static,
            "timestamp":msg.encrypted_timestamp,
            "mac1":msg.mac1,
            "mac2":msg.mac2,
        }
        print(f"no serialised {final_msg}")

        print(len(self.E_pub_i))       
        print(len(msg.encrypted_static))  
        print(len(msg.encrypted_timestamp))  
        print(len(msg.mac1))            
        return final_msg
    
    def process_response(self, raw_response):
        msg_type     = raw_response[0:1]
        reserved     = raw_response[1:4]
        sender       = int.from_bytes(raw_response[4:8], 'little')
        receiver     = int.from_bytes(raw_response[8:12], 'little')
        E_R_pub      = raw_response[12:44]
        msg_empty    = raw_response[44:60]
        mac1         = raw_response[60:76]
        mac2         = raw_response[76:92]
        #E_R_pub      = b'\xe5\xd0!\x98z\x12\xb5\xf8&\x17\xfe\x14K\x9exe(\x1bK\xc2\x8e\x15T\x81\xcc\xbe\xceq$\x82v\x7f'
        #self.chaining_key = b'\xe0\\UH\\\x12\x9a\xb4\xcc\xd0\r\xa9\xd2\xac\xc7\xb1]ky\xdc\xc2\x18\xb8\x95]NQ\xf9=\xcd\xa5\xc3'
        #self.hash = b'r\xdb\rg\x14\xa2\xff\x13h\xf8K\x9dL\xec\x81\xbf\xa6Q\x15\xf3\xeb\xd7{\x87\xa5\x8bs\xc8\xb4k\x8e\x1e'
        #self.E_priv_i= b'\xac\x03\x18b0\xc4\xf7\xd4*\xa7-\x81&\xfb\xc7\xb3PG0\xae\xa4y0\x90\xe2\xe4\xe2\xa0g\\\x83\xb6'
        #self.E_pub_i = b"\xb1\x13\xb4\xd3\x00R'\x8b\x80\xd1\xcc\xc8X\x1bYf(4\xce&\xd0V\xde\x97\xff\xba2$u\x9b\xe3G"
        #self.static_private = b'\x99x\x93eP\xdd\xb7h\xd5dJ\xc7\xa5~\x83\xbdX\x04M\xe29\x15\xe2\xf1\xe8\xd8VFk0\xf8\xa1'
        
        print(f"msg_type: {msg_type}")
        print(f"sender (server session ID): {sender}")
        print(f"receiver (should match your sender): {receiver}")
        print(f"E_R_pub: {E_R_pub}")
        print(f"msg_empty: {msg_empty}")
        
        self.chaining_key = Kdf1(self.chaining_key, E_R_pub)
        print(f"chaining_key after Kdf1(chain_key, E_R_pub): {self.chaining_key}")
        
        self.hash = Hash(self.hash + E_R_pub)
        print(f"hash after Hash(hash || E_R_pub): {self.hash}")
        
        self.chaining_key = Kdf1(self.chaining_key, DH(self.E_priv_i, E_R_pub))
        print(f"chaining_key after Kdf1(chain_key, DH(E_priv_i, E_R_pub)): {self.chaining_key}")
        
        self.chaining_key = Kdf1(self.chaining_key, DH(self.static_private, E_R_pub))
        print(f"chaining_key after Kdf1(chain_key, DH(S_priv_i, E_R_pub)): {self.chaining_key}")
        
        Q = b'\x00' * 32
        self.chaining_key, tmp, key3 = Kdf3(self.chaining_key, Q)
        print(f"chaining_key after Kdf3: {self.chaining_key}")
        print(f"tmp: {tmp}")
        print(f"key3: {key3}")
        
        self.hash = Hash(self.hash + tmp)
        print(f"hash after Hash(hash || tmp): {self.hash}")
        
        empty = AEAD_decrypt(key3, 0, msg_empty, self.hash)
        print(f"empty (should be b''): {empty}")
        assert empty == b'', "Handshake failed!"
        
        self.hash = Hash(self.hash + empty)
        print(f"hash after Hash(hash || empty): {self.hash}")
        
        self.T_I_send, self.T_I_recv = Kdf2(self.chaining_key, b'')
        print(f"T_I_send: {self.T_I_send}")
        print(f"T_I_recv: {self.T_I_recv}")
        
        self.N_I_send = self.N_I_recv = 0
        self.server_index = sender
        print("Handshake successful!")

    def process_response_cookie(self, raw_response):
        msg_type     = b'\x03'
        reserved     = raw_response[1:4]
        receiver     = int.from_bytes(raw_response[4:8], 'little')
        nonce = raw_response[8:32]
        encrypted_cookie = raw_response[32:64] #encrypted cookie (16 bytes) and auth text (16 bytes)
        decrypted_cookie = XAEAD_decrypt(Hash(b"cookie--" + SERVER_STATIC_PUBLIC_KEY), nonce, encrypted_cookie, self.last_sent_mac1)
        self.last_received_cookie = decrypted_cookie
        return self.new_handshake()     

    def create_wireguard_transport_message(self,P):
        type = b'\x04'
        P_byte = P#msgpack.packb(P)
        msg_packet = AEAD_encrypt(self.T_I_send,self.N_I_send,P,b'')
        
        msg = (type+b'\x00' * 3+self.server_index.to_bytes(4,"little")+self.N_I_send.to_bytes(8,"little")+msg_packet)
        
        self.N_I_send+=1
        return msg
    def handle_wireguard_response(self,raw_response):
        
        
        type     = raw_response[0:1]
        reserved     = raw_response[1:4]
        receiver     = int.from_bytes(raw_response[4:8], 'little')
        counter      = int.from_bytes(raw_response[8:16], 'little')
        packet    = raw_response[16:]
        
        
        
        
        
        plaintext = AEAD_decrypt(self.T_I_recv, counter, packet, b'')
        self.N_I_recv += 1
        
        
        msg =plaintext
        print(f"Received: {msg}")
        return msg
        
        
        
#I = Initiator(0,0)
#I.process_response(b'\x02\x00\x00\x00\x15\x0b\xae\xd4)\x89\x000\xb4W\x17\xd2\x8b\x9fJ\xdb\xb5\xd1yq\xdd\xf6C*\x9c\xa5\xb7A\x05\x8e#5H\x12\xf9Z\x95I:@\xbc%\xab\x930\x04\x85_\x93\xb3\x94\xe3e\xad\xbf\xbd^|5\xef\x95f]\xd2\xef\xc3\x12v\xb6\xe4\xd7\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
        
        
        
    
   
        
    
        
        



         


