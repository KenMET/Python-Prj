import sys



sys.path.append('./alphabet')
import alphabet_pro as alphabet


if __name__ == "__main__":
    print (str(alphabet.hexstr2int('0123')) + ' <-> ' + alphabet.int2hexstr(291))
    print (alphabet.hexstr2asciistr('30313233') + ' <-> ' + alphabet.asciistr2hexstr('0123'))
    print (str(alphabet.str2hexbytes('123')) + ' <-> ' + alphabet.hexbytes2str(b'\x31\x32\x33'))
    print (str(alphabet.hexstr2bytes('123abc')) + ' <-> ' + alphabet.bytes2hexstr(b'\x12\x3a\xbc'))