import datetime

import nacl.bindings
import nacl.public
import base64
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
import struct
import hashlib
from Crypto.Hash import BLAKE2s
import hmac
import random
import tai64
import time
#################### Constants ########################
SERVER_STATIC_PUBLIC_KEY=b'f,^\xc0Cb\xf3\x937\xbf\x11\x14"\xed\x13\x0b\x9f\xe7\xaf;\x94\xb0p\x13\xe1\x94\xdd\x85\xcf\x01\x0bC'

#################### End of Constants #################
####Personal


"""Used to generate secret"""
def DH(private_key, public_key):
    return nacl.bindings.crypto_scalarmult(n=private_key, p=public_key)

def DH_Generate():
    private_key = nacl.public.PrivateKey.generate()
    return (private_key, private_key.public_key)

def AEAD_encrypt(key, counter, plain_text, auth_text):
    chacha = ChaCha20Poly1305(key)
    # 'I' is 32-bit unsigned (4 bytes) -> 0
    # 'Q' is 64-bit unsigned (8 bytes) -> counter, '<' ensures Little-Endian
    #counter = struct.pack('<IQ', 0, counter)
    return chacha.encrypt(counter, plain_text, auth_text)
    

def AEAD_decrypt(key, counter, encrypted_data, auth_text):
    chacha = ChaCha20Poly1305(key)
    #will be used for conversion from int to byte literal
    #counter = struct.pack('<IQ', 0, counter)
    return chacha.decrypt(counter,encrypted_data,auth_text)

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
def timestamp():
    t = time.time()
    secs = int(t) + 10 + (1 << 62)  # TAI64: Unix time + leap offset + 2^62 flag
    nsecs = int((t % 1) * 1e9)       # fractional seconds → nanoseconds
    return struct.pack('>QI', secs, nsecs)

class Message:
    def __init__(self):
        self.message_type = 0
        self.reserved_zero = 0
        self.sender_index =0
        self.unencrypted_ephemeral =0
        self.encrypted_static =0
        self.encrypted_timestamp =0
        self.mac1 =0

class Initiator:
    def __init__(self,static_public,static_private):
        self.chaining_key = Hash(b'Noise_IKpsk2_25519_ChaChaPoly_BLAKE2s')
        self.hash = Hash(Hash(self.chaining_key | b'WireGuard v1 zx2c4 Jason@zx2c4.com') | SERVER_STATIC_PUBLIC_KEY)
        self.E_priv_i , self.E_pub = DH_Generate()
        self.ephemeral_private = self.E_priv_i
        self.last_received_cookie
        self.static_public=static_public
        self.static_private=static_private
    def handshake_message(self):
        msg = Message()
        
        msg.message_type = 1
        
        msg.reserved_zero = {0,0,0}
        msg.sender_index = int.from_bytes(random.getrandbits(32), byteorder='little')
        
        
        msg.unencrypted_ephemeral = self.E_pub_i
        self.hash = Hash(self.hash|msg.unencrypted_ephemeral)
        
        temp = HMac(self.chaining_key,msg.unencrypted_ephemeral)
        self.chaining_key = HMac(temp,b'0x1')
        
        temp = HMac(self.chaining_key,DH(self.ephemeral_private,SERVER_STATIC_PUBLIC_KEY))
        self.chaining_key = HMac(temp,b'\x01')
        key = HMac(temp,self.chaining_key|b'\x02')        

        msg.encrypted_static = AEAD_encrypt(key, 0, self.static_public, self.hash)#! set my static public aka key 
        self.hash = Hash(self.hash | msg.encrypted_static)
        
        temp = HMac(self.chaining_key, DH(self.static_private, SERVER_STATIC_PUBLIC_KEY))#! set my static private aka key 
        self.chaining_key = HMac(temp, b'\x01')
        key = HMac(temp, self.chaining_key | b'\x02')
        
        msg.encrypted_timestamp = AEAD_encrypt(key, 0, timestamp(), self.hash)
        self.hash = Hash(self.hash | msg.encrypted_timestamp)
        
        concat_msg = msg = (
        msg.message_type.to_bytes(1,"little")                           
        + b'\x00' * 3                        
        + msg.sender_index.to_bytes(4, 'little')    
        + self.E_pub.to_bytes(1,"little")                    
        + msg.encrypted_static.to_bytes(1,"little")                        
        + msg.encrypted_timestamp.to_bytes(1,"little")                    
        )
        
        msg.mac1 = Mac(Hash('mac1----' | SERVER_STATIC_PUBLIC_KEY), concat_msg)
        return {
            "type": msg.message_type,
            "reserved":msg.reserved_zero,
            "sender":msg.sender_index,
            "ephemeral ":msg.unencrypted_ephemeral,
            "static":msg.encrypted_static,
            "timestamp ":msg.encrypted_timestamp,
            "mac1":msg.mac1,
            "mac2":None,
        }
        
    
        
        



         


