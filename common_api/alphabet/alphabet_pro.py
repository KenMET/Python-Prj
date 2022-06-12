#python3 - alphabet_pro
#Creat by Ken in 2020-02-29
#Ver = 1.0
#Modify Log:
#
import binascii
import string


#hex str -> byte
#e.g.   '123abc' -> b'\x12:\xbc'
def hexstr2bytes(str_tmp):
    #return bytearray.fromhex(str_tmp)   #res as bytearray(b'\x12:\xbc')
    return bytes.fromhex(str_tmp)       #res as b'\x12:\xbc'
#byte -> hex str
#e.g.   b'\x12\x3a\xbc' -> '123abc'
def bytes2hexstr(bytes_tmp):
    return bytes_tmp.hex()              #res as '123abc' python ver over 3.5
    #return ''.join(['%02x' % b for b in bytes_tmp])              #res as '123abc' python ver under 3.5
#print (str(hexstr2bytes('123abc')) + ' <-> ' + bytes2hexstr(b'\x12\x3a\xbc'))


#str -> hex byte
#e.g.   '123' -> b'\x31\x32\x33'(b'123')
def str2hexbytes(str_tmp):
    return str_tmp.encode('utf8')
#hex byte -> str
#e.g.   b'\x31\x32\x33' -> '123'
def hexbytes2str(bytes_tmp):
    return bytes_tmp.decode('utf8')  #arvg 'gbk' for Chinese
#print (str(str2hexbytes('123')) + ' <-> ' + hexbytes2str(b'\x31\x32\x33'))


#hex str -> ascii str
#e.g.   '30313233' -> '0123'
def hexstr2asciistr(str_tmp):
    return bytearray.fromhex(str_tmp).decode('ascii')
#ascii str -> hex str
#e.g.   '0123' -> '30313233'
def asciistr2hexstr(str_tmp):
    return "".join([format(ord(i), "02X") for i in str_tmp])
#print (hexstr2asciistr('30313233') + ' <-> ' + asciistr2hexstr('0123'))  

#hex str -> dec number
#e.g.   '0123' -> 291(0x0123)
def hexstr2int(str_tmp):
    return int(str_tmp, 16)
#dec number -> hex str
#e.g.   291(0x0123) -> '0123'
def int2hexstr(number):
    tmp = str(hex(number)).replace('0x','')
    if len(tmp) % 2 == 0:
        return tmp
    else:
        return '0' + tmp
#print (str(hexstr2int('0123')) + ' <-> ' + int2hexstr(291))
#more:
# e.g.   '0b10000'         '0o20'            '16'          '0x10'
#  ↓        bin             oct              dec            hex 
# bin        -          bin(int(x,8))   bin(int(x,10))   bin(int(x,16))
# oct   oct(int(x,2))        -          oct(int(x,10))   oct(int(x,16))
# dec   str(int(x,2))   str(int(x,8))         -          str(int(x,16))
# hex   hex(int(x,2))   hex(int(x,8))   hex(int(x,10))       -









