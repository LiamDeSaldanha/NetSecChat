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

def DH(private_key, public_key):
    """Used to generate secret"""
    return nacl.bindings.crypto_scalarmult(n=private_key, p=public_key)

def DH_Generate():
    """Generate public-private keypair"""
    private_key = nacl.public.PrivateKey.generate()
    return (bytes(private_key), bytes(private_key.public_key))

def AEAD_encrypt(key, counter, plain_text, auth_text):
    """Encryption using nonce and authentication text"""
    chacha = ChaCha20Poly1305(key)
    # 'I' is 32-bit unsigned (4 bytes) -> 0
    # 'Q' is 64-bit unsigned (8 bytes) -> counter, '<' ensures Little-Endian
    counter = struct.pack('<IQ', 0, counter)
    
    return chacha.encrypt(counter, plain_text, auth_text)
    

def AEAD_decrypt(key, counter, encrypted_data, auth_text):
    """Decryption using nonce and authentication text"""
    chacha = ChaCha20Poly1305(key)
    #will be used for conversion from int to byte literal
    counter = struct.pack('<IQ', 0, counter)
    return chacha.decrypt(counter,encrypted_data,auth_text)

#XAEAD encrypt and decrypt used for mac2 calculation
def XAEAD_decrypt(key, counter, plain_text, auth_text):
    return nacl.bindings.crypto_aead_xchacha20poly1305_ietf_encrypt(
            plain_text, auth_text, counter, key
        )

def XAEAD_decrypt(key, counter, encrypted_data, auth_text):
    return nacl.bindings.crypto_aead_xchacha20poly1305_ietf_decrypt(
        encrypted_data, auth_text, counter, key
    )

def Hash(inp):
    """Blake2s hash"""
    h = hashlib.blake2s()
    # = input.encode('utf-8')
    h.update(inp)

    hash = h.hexdigest()
    return bytes.fromhex(hash)

def MixHash(input1, input2):
    """Hash concatenated strings"""
    string =  input1 + input2
    h = hashlib.blake2s()
    h.update(string)
    hash = h.hexdigest()
    return bytes.fromhex(hash)

def Mac(key, inp):
    """Mac calculation"""
    h = BLAKE2s.new(key=key, digest_bytes = 16)
    h.update(inp)
    mac_tag = h.digest()
    mac_tag = mac_tag.hex()
    return bytes.fromhex(mac_tag)

def HMac(key, inp):
    """Hash-based Mac using Blake2s"""
    h = hmac.new(key=key,msg=inp,digestmod = hashlib.blake2s)
    return h.digest()

def Kdf1(key, message):
    """Key derivation chain of length 1. HKDF from the WireGuard definitional paper"""
    t_0 = HMac(key, message)
    t_1 = HMac(t_0, b'\x01')
    return (t_1)
 
def Kdf2(key, message):
    """Key derivation chain of length 2. HKDF from the WireGuard definitional paper"""
    t_0 = HMac(key, message)
    #chaing from the paper, using the previous HMac and 
    t_1 = HMac(t_0, b'\x01')
    t_2 = HMac(t_0, t_1 + b'\x02')
    return (t_1, t_2)

def Kdf3(key, message):
    """Key derivation chain of length 3. HKDF from the WireGuard definitional paper"""
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
    secs = int(t) + 10 + 2**62    # TAI64: Unix time + leap offset + 2^62 flag
    nsecs = int((t % 1) * 1e6)    # fractional seconds → nanoseconds
    timestamp_ret = secs.to_bytes(8,"big")+nsecs.to_bytes(4,"big")
    return timestamp_ret

class Message:
    """Message class is the structure and content of the handshake for encrypted (standard and mac2) connections"""
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
    """Initiator class is responsible for initiating the handshake with the server for encrypted connections. It has methods for handling 
    standard encryption where the mac2 value is 16 0s and a method for calculating the mac2 value when received from the server"""
    def __init__(self,static_public,static_private):
        self.initial_chaining_key = Hash(b'Noise_IKpsk2_25519_ChaChaPoly_BLAKE2s')
        self.initial_hash = Hash(self.initial_chaining_key + b'WireGuard v1 zx2c4 Jason@zx2c4.com')
        
        self.initial_hash = Hash(self.initial_hash + SERVER_STATIC_PUBLIC_KEY)
        #set working variables--must be overwritten for threading to work
        self.chaining_key = self.initial_chaining_key
        self.hash = self.initial_hash
        
        self.E_priv_i , self.E_pub_i = DH_Generate()
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
        """Initiate handshake with the server for encrypted connections. Standard encryption uses sixteen 0s for mac 2 and 
        if there is a mac2 value, then it is parsed"""
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
        #if a cookie was received from the server then use it to calculate the mac2 value
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
        """Process and decrypt the cookie received from the server"""
        msg_type     = b'\x03'
        reserved     = raw_response[1:4]
        receiver     = int.from_bytes(raw_response[4:8], 'little')
        nonce = raw_response[8:32]
        encrypted_cookie = raw_response[32:64] #encrypted cookie (16 bytes) and auth text (16 bytes)
        decrypted_cookie = XAEAD_decrypt(Hash(b"cookie--" + SERVER_STATIC_PUBLIC_KEY), nonce, encrypted_cookie, self.last_sent_mac1)
        self.last_received_cookie = decrypted_cookie
        return self.new_handshake()     

    def create_wireguard_transport_message(self,P):
        """Method to create transport messages by padding them for the wireguard protocol"""
        type = b'\x04'
        P_byte = P#msgpack.packb(P)
        msg_packet = AEAD_encrypt(self.T_I_send,self.N_I_send,P,b'')     
        msg = (type+b'\x00' * 3+self.server_index.to_bytes(4,"little")+self.N_I_send.to_bytes(8,"little")+msg_packet)        
        self.N_I_send+=1
        return msg
    
    def handle_wireguard_response(self,raw_response):
        """Method to unpack and decrypt wireguard response messages"""    
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