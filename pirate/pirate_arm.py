#Created in 2020-01-02 V03
import sys
import time
import signal
import binascii
import string

def enqueen_info(dict, index, list):
    dict_tmp = {index : list}
    dict.update(dict_tmp)

def byte_hex_to_str(byte_buff):
    hex_str = ''
    if type(byte_buff) == type(2):
        hex_str = byte_buff.encode('hex')
        if byte_buff < 16:
             hex_str = '0' + hex_str
    else:
        for index in byte_buff:
            if index < 16:
                hex_str += ('0' + index.encode('hex'))
            else:
                hex_str += index.encode('hex')
    return hex_str.replace('0x', '').strip()

def count_dict(dict, key_words):
    count = 0
    for index in dict:
        tmp = dict.get(index, ['NULL', '00', 'Nothing'])
        res = tmp[2]
        if res.find(key_words) >= 0:
            count += 1
    return count

def get_list_by_macid(obu_dict, cpc_dict, mac_id):
    tmp = obu_dict.get(mac_id, ['NULL', '00', 'Nothing'])
    if tmp[0] != 'NULL':
        return tmp
    return cpc_dict.get(mac_id, ['NULL', '00', 'Nothing'])

def is_trade_ok(obu_dict, cpc_dict, mac_id):
    tmp = obu_dict.get(mac_id, ['NULL', '00', 'Nothing'])
    res = tmp[2]
    if res.find('Trade OK') >= 0 or \
        res.find('Refusal') >= 0 or \
        res.find('err[04]') >= 0 or \
        res.find('err[10]') >= 0:
        return True
    tmp = cpc_dict.get(mac_id, ['NULL', '00', 'Nothing'])
    if res.find('Trade OK') >= 0:
        return True
    return False
        
def obu_cpc_enqueen(obu_dict, cpc_dict, macid, list):
    bytes_macid = macid.lower()
    if bytes_macid[0] >= 'a':#a
        enqueen_info(cpc_dict, macid, list)
    else:
        enqueen_info(obu_dict, macid, list)

def analyze_info(log_file):
    obu_dict = {}
    cpc_dict = {}
    obu_result = {}
    cpc_result = {}
    
    with open('%s'%(log_file.strip().replace(' ', '')), 'r') as f:
        for line in f.readlines():
            if line.find(' - FFFF') > 0:
                tmp = line[line.find(' - FFFF') + 19:]
                if tmp.find(' - ') > 0: #[INFO | 2020-01-02 10:18:05,004] | cf - CF00[INFO | 2020-01-02 10:58:58,838] |
                    continue            #in case for break off frame
                hex_buff = binascii.a2b_hex(tmp.strip().replace(' ', '').replace('\n', '').replace('\t', '').replace('\r', '').strip())
                frame_type = byte_hex_to_str(hex_buff[0])
                if frame_type.find('b') != 0:
                    continue
                mac_id = byte_hex_to_str(hex_buff[1:5])
                err_code = byte_hex_to_str(hex_buff[5])
                if is_trade_ok(obu_dict, cpc_dict, mac_id) == True:
                    continue
                if frame_type == 'b2':
                    obu_cpc_enqueen(obu_dict, cpc_dict, mac_id, ['b2', err_code, 'send b2'])
                elif frame_type == 'b4':
                    obu_cpc_enqueen(obu_dict, cpc_dict, mac_id, ['b4', err_code, 'send b4'])
                elif frame_type == 'b5':
                    obu_cpc_enqueen(obu_dict, cpc_dict, mac_id, ['b5', err_code, 'send b5'])
                elif frame_type == 'b7':
                    obu_cpc_enqueen(obu_dict, cpc_dict, mac_id, ['b7', err_code, 'send b7'])
            elif line.find(' - C') > 0:
                tmp = line[line.find(' - ') + 3:]
                if tmp.find(' - ') > 0: #[INFO | 2020-01-02 10:18:05,004] | cf - CF00[INFO | 2020-01-02 10:58:58,838] |
                    continue            #in case for break off frame
                hex_buff = binascii.a2b_hex(tmp.strip().replace(' ', '').replace('\n', '').replace('\t', '').replace('\r', '').strip())
                frame_type = byte_hex_to_str(hex_buff[0])
                if frame_type.find('c') != 0:
                    continue
                if frame_type != 'cf':
                    mac_id = byte_hex_to_str(hex_buff[1:5])
                    if is_trade_ok(obu_dict, cpc_dict, mac_id) == True:
                        continue
                    tmp_list = get_list_by_macid(obu_dict, cpc_dict, mac_id)
                    if frame_type == 'c1':
                        if tmp_list[0] == 'b2' and tmp_list[1] == '00':
                            obu_cpc_enqueen(obu_dict, cpc_dict, mac_id, ['%s'%(tmp_list[0]), '00', 'Prepare b4'])
                        elif tmp_list[0] == 'b5' and tmp_list[1] == '00':
                            obu_cpc_enqueen(obu_dict, cpc_dict, mac_id, ['%s'%(tmp_list[0]), '00', 'Trade OK'])
                        elif tmp_list[0] == 'b7' and tmp_list[1] == '00':
                            obu_cpc_enqueen(obu_dict, cpc_dict, mac_id, ['%s'%(tmp_list[0]), '00', 'Trade OK'])
                    elif frame_type == 'c6':
                        if tmp_list[0] == 'b4' and tmp_list[1] == '00':
                            obu_cpc_enqueen(obu_dict, cpc_dict, mac_id, ['%s'%(tmp_list[0]), '00', 'Prepare b5'])
                    elif frame_type == 'c7':
                        if tmp_list[0] == 'b5' and tmp_list[1] == '00':
                            obu_cpc_enqueen(obu_dict, cpc_dict, mac_id, ['%s'%(tmp_list[0]), '00', 'Prepare b7'])
                    elif frame_type == 'c2':
                        if tmp_list[1] == '00':
                            obu_cpc_enqueen(obu_dict, cpc_dict, mac_id, ['%s'%(tmp_list[0]), '00', 'Active Refusal %s'%(tmp_list[0])])
                        else:
                            obu_cpc_enqueen(obu_dict, cpc_dict, mac_id, ['%s'%(tmp_list[0]), '00', '%s-err[%s]'%(tmp_list[0], tmp_list[1])])

    enqueen_info(obu_result, 'Access', len(obu_dict))
    enqueen_info(obu_result, 'Trade_OK', count_dict(obu_dict, 'Trade OK'))
    enqueen_info(obu_result, 'Active_Refusal', count_dict(obu_dict, 'Refusal'))
    enqueen_info(obu_result, 'No_Card', count_dict(obu_dict, 'b4-err[04]'))
    enqueen_info(obu_result, 'Army', count_dict(obu_dict, 'b4-err[10]'))
    enqueen_info(obu_result, 'b4-err[01]', count_dict(obu_dict, 'b4-err[01]'))
    enqueen_info(obu_result, 'b4-err[05]', count_dict(obu_dict, 'b4-err[05]'))
    enqueen_info(obu_result, 'b4-err[07]', count_dict(obu_dict, 'b4-err[07]'))
    enqueen_info(obu_result, 'b4-err[08]', count_dict(obu_dict, 'b4-err[08]'))
    enqueen_info(obu_result, 'b4-err[09]', count_dict(obu_dict, 'b4-err[09]'))
    enqueen_info(obu_result, 'b4-err[0b]', count_dict(obu_dict, 'b4-err[0b]'))
    enqueen_info(obu_result, 'b4-err[0c]', count_dict(obu_dict, 'b4-err[0c]'))
    enqueen_info(obu_result, 'b4-err[0d]', count_dict(obu_dict, 'b4-err[0d]'))
    enqueen_info(obu_result, 'b4-err[0e]', count_dict(obu_dict, 'b4-err[0e]'))
    enqueen_info(obu_result, 'b5-err[01]', count_dict(obu_dict, 'b5-err[01]'))
    enqueen_info(obu_result, 'b5-err[03]', count_dict(obu_dict, 'b5-err[03]'))
    enqueen_info(obu_result, 'b5-err[04]', count_dict(obu_dict, 'b5-err[04]'))
    enqueen_info(obu_result, 'b5-err[05]', count_dict(obu_dict, 'b5-err[05]'))
    enqueen_info(obu_result, 'b5-err[06]', count_dict(obu_dict, 'b5-err[06]'))
    enqueen_info(obu_result, 'b5-err[07]', count_dict(obu_dict, 'b5-err[07]'))
    enqueen_info(obu_result, 'b5-err[0c]', count_dict(obu_dict, 'b5-err[0c]'))
    enqueen_info(obu_result, 'b5-err[0d]', count_dict(obu_dict, 'b5-err[0d]'))
    enqueen_info(obu_result, 'b5-err[0e]', count_dict(obu_dict, 'b5-err[0e]'))
    enqueen_info(obu_result, 'b5-err[0f]', count_dict(obu_dict, 'b5-err[0f]'))
    enqueen_info(obu_result, 'b7-err[01]', count_dict(obu_dict, 'b7-err[01]'))
    enqueen_info(obu_result, 'b7-err[03]', count_dict(obu_dict, 'b7-err[03]'))
    enqueen_info(obu_result, 'b7-err[04]', count_dict(obu_dict, 'b7-err[04]'))
    enqueen_info(obu_result, 'b7-err[05]', count_dict(obu_dict, 'b7-err[05]'))
    
    enqueen_info(cpc_result, 'Access', len(cpc_dict))
    enqueen_info(cpc_result, 'Trade_OK', count_dict(cpc_dict, 'Trade OK'))
    enqueen_info(cpc_result, 'Active_Refusal', count_dict(cpc_dict, 'Refusal'))
    enqueen_info(cpc_result, 'No_Card', count_dict(cpc_dict, 'b4-err[04]'))
    enqueen_info(cpc_result, 'Army', count_dict(cpc_dict, 'b4-err[10]'))
    enqueen_info(cpc_result, 'b4-err[01]', count_dict(cpc_dict, 'b4-err[01]'))
    enqueen_info(cpc_result, 'b4-err[05]', count_dict(cpc_dict, 'b4-err[05]'))
    enqueen_info(cpc_result, 'b4-err[07]', count_dict(cpc_dict, 'b4-err[07]'))
    enqueen_info(cpc_result, 'b4-err[08]', count_dict(cpc_dict, 'b4-err[08]'))
    enqueen_info(cpc_result, 'b4-err[09]', count_dict(cpc_dict, 'b4-err[09]'))
    enqueen_info(cpc_result, 'b4-err[0b]', count_dict(cpc_dict, 'b4-err[0b]'))
    enqueen_info(cpc_result, 'b4-err[0c]', count_dict(cpc_dict, 'b4-err[0c]'))
    enqueen_info(cpc_result, 'b4-err[0d]', count_dict(cpc_dict, 'b4-err[0d]'))
    enqueen_info(cpc_result, 'b4-err[0e]', count_dict(cpc_dict, 'b4-err[0e]'))
    enqueen_info(cpc_result, 'b5-err[01]', count_dict(cpc_dict, 'b5-err[01]'))
    enqueen_info(cpc_result, 'b5-err[03]', count_dict(cpc_dict, 'b5-err[03]'))
    enqueen_info(cpc_result, 'b5-err[04]', count_dict(cpc_dict, 'b5-err[04]'))
    enqueen_info(cpc_result, 'b5-err[05]', count_dict(cpc_dict, 'b5-err[05]'))
    enqueen_info(cpc_result, 'b5-err[06]', count_dict(cpc_dict, 'b5-err[06]'))
    enqueen_info(cpc_result, 'b5-err[07]', count_dict(cpc_dict, 'b5-err[07]'))
    enqueen_info(cpc_result, 'b5-err[0c]', count_dict(cpc_dict, 'b5-err[0c]'))
    enqueen_info(cpc_result, 'b5-err[0d]', count_dict(cpc_dict, 'b5-err[0d]'))
    enqueen_info(cpc_result, 'b5-err[0e]', count_dict(cpc_dict, 'b5-err[0e]'))
    enqueen_info(cpc_result, 'b5-err[0f]', count_dict(cpc_dict, 'b5-err[0f]'))
    enqueen_info(cpc_result, 'b7-err[01]', count_dict(cpc_dict, 'b7-err[01]'))
    enqueen_info(cpc_result, 'b7-err[03]', count_dict(cpc_dict, 'b7-err[03]'))
    enqueen_info(cpc_result, 'b7-err[04]', count_dict(cpc_dict, 'b7-err[04]'))
    enqueen_info(cpc_result, 'b7-err[05]', count_dict(cpc_dict, 'b7-err[05]'))

    return obu_result, cpc_result


def check_trade(log_file):
    obu_result, cpc_result = analyze_info(log_file)
    enum = [obu_result.get('Access', 0), obu_result.get('Trade_OK', 0),
            obu_result.get('Active_Refusal', 0), obu_result.get('No_Card', 0),obu_result.get('Army', 0),
            obu_result.get('b4-err[01]', 0), obu_result.get('b4-err[05]', 0), obu_result.get('b4-err[07]', 0),
            obu_result.get('b4-err[08]', 0), obu_result.get('b4-err[09]', 0), obu_result.get('b4-err[0b]', 0),
            obu_result.get('b4-err[0c]', 0), obu_result.get('b4-err[0d]', 0), obu_result.get('b4-err[0e]', 0),
            obu_result.get('b5-err[01]', 0), obu_result.get('b5-err[03]', 0), obu_result.get('b5-err[04]', 0),
            obu_result.get('b5-err[05]', 0), obu_result.get('b5-err[06]', 0), obu_result.get('b5-err[07]', 0),
            obu_result.get('b5-err[0c]', 0), obu_result.get('b5-err[0d]', 0), obu_result.get('b5-err[0e]', 0),
            obu_result.get('b5-err[0f]', 0), obu_result.get('b7-err[01]', 0), obu_result.get('b7-err[03]', 0),
            obu_result.get('b7-err[04]', 0), obu_result.get('b7-err[05]', 0),
            cpc_result.get('Access', 0), cpc_result.get('Trade_OK', 0),
            cpc_result.get('Active_Refusal', 0), cpc_result.get('No_Card', 0), cpc_result.get('Army', 0),
            cpc_result.get('b4-err[01]', 0), cpc_result.get('b4-err[05]', 0), cpc_result.get('b4-err[07]', 0),
            cpc_result.get('b4-err[08]', 0), cpc_result.get('b4-err[09]', 0), cpc_result.get('b4-err[0b]', 0),
            cpc_result.get('b4-err[0c]', 0), cpc_result.get('b4-err[0d]', 0), cpc_result.get('b4-err[0e]', 0),
            cpc_result.get('b5-err[01]', 0), cpc_result.get('b5-err[03]', 0), cpc_result.get('b5-err[04]', 0),
            cpc_result.get('b5-err[05]', 0), cpc_result.get('b5-err[06]', 0), cpc_result.get('b5-err[07]', 0),
            cpc_result.get('b5-err[0c]', 0), cpc_result.get('b5-err[0d]', 0), cpc_result.get('b5-err[0e]', 0),
            cpc_result.get('b5-err[0f]', 0), cpc_result.get('b7-err[01]', 0), cpc_result.get('b7-err[03]', 0),
            cpc_result.get('b7-err[04]', 0), cpc_result.get('b7-err[05]', 0),]
    print (enum)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("arg Err")
        exit()
    log_file = sys.argv[1]
    check_trade(log_file)
    
    
