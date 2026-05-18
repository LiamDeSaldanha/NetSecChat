import nacl.bindings
import nacl.public
import base64
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
import struct
import hashlib
from Crypto.Hash import BLAKE2s
import hmac

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

def Hash(input):
    h = hashlib.blake2s()
    # = input.encode('utf-8')
    h.update(input)

    hash = h.hexdigest()
    return bytes.fromhex(hash)

def MixHash(input1, input2):
    string =  input1 + input2
    h = hashlib.blake2s()
    h.update(string)
    hash = h.hexdigest()
    return bytes.fromhex(hash)

def Mac(key, input):
    h = BLAKE2s.new(key=key, digest_bytes = 16)
    h.update(input)
    mac_tag = h.digest()
    mac_tag = mac_tag.hex()
    return bytes.fromhex(mac_tag)

def HMac(key, input):
    h = hmac.new(key=key,msg=input,digestmod = hashlib.blake2s)
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

               



#TIMESTAMP: ADD 10^6 and ADD 10 not 30 something

#input1 = b'a'*50
#input2 = b'b'*50

#(MixHash(input1, input2))
#key = b':\xb6\x90\xbd\n:\x18Z88"\xd8a\x08\x9f\xa7\x9c\xc7\xcb\x01\x99-\xfd\x9cGX\xdc\x9dO\x0c\xb3@'
#input = b'I am a message without a MAC, but only for now.'
#print(Mac(key, input))
#input = "Noise_IKpsk2_25519_ChaChaPoly_BLAKE2s"
#print(Hash(b'Noise_IKpsk2_25519_ChaChaPoly_BLAKE2s'))

#key = b':\xb6\x90\xbd\n:\x18Z88"\xd8a\x08\x9f\xa7\x9c\xc7\xcb\x01\x99-\xfd\x9cGX\xdc\x9dO\x0c\xb3@'
#input = b'I am a message without an HMAC, but only for now.'
#print(HMac(key, input))

key = b':\xb6\x90\xbd\n:\x18Z88"\xd8a\x08\x9f\xa7\x9c\xc7\xcb\x01\x99-\xfd\x9cGX\xdc\x9dO\x0c\xb3@'
input = b'Choose your LLM adventure folks.'
print(Kdf1(key,input))
print(Kdf2(key, input))
print(Kdf3(key, input))


    
key = b':\xb6\x90\xbd\n:\x18Z88"\xd8a\x08\x9f\xa7\x9c\xc7\xcb\x01\x99-\xfd\x9cGX\xdc\x9dO\x0c\xb3@'
counter = b'\x00'*12 # Read the standard carefully for how this must be formatted
plaintext = b"attack at dawn"
authtext = b'\x8e2\x89\xe2\x14\xfd\x16\x19o\x06\xc9\xb2\xd9\xe8F\xfd\xdaf\xdc\xa4\xf9\xe9\x98\xbc\xd8x\xb9\x90\x1e\n\xac\x98'

encrypted_data = AEAD_encrypt(key, counter, plaintext, authtext)

#print(encrypted_data)

#print(AEAD_decrypt(key, counter, encrypted_data, authtext))

#raw_bytes = base64.b64decode(string)
#convert string to bytes before calling DH()
#private_key = b'\xb0)e\xdbZ\x01\x8f\x0f\xf5\x91\x88<\xab\x15\x14\x95\xb3\x92\xbd&3\xfe\x18<\x8f\xd6P\xeb\xd0k\xdb\x7f'
#public_key = b'\x14\xde\xd1\x90m?\x0eaBa\xbb\xf8\\\x08\xdd\xfd\x08\xa7?^\x9f\xcb\x16Y\xdf\xa1\\B\x9d\t7k'

#print(DH(private_key, public_key))
