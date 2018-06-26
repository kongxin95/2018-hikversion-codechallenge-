# -*- coding:utf-8 -*-
import sys
import socket
import json
import func
from time import time
from random import seed
from math import ceil
# from copy import deepcopy
# from random import choice
# from random import randint

seed(3)

# 从服务器接收一段字符串, 转化成字典的形式
def RecvJuderData(hSocket):
    nRet = -1
    Message_1 = ''
    while True:
        message = hSocket.recv(8)
        Message_1 += message
        if len(Message_1)>=8:
            break
    # print(Message_1)
    len_json = int(Message_1)

    Message = ''
    while True:
        message = hSocket.recv(1024 * 1024 * 4)
        Message+=message
        if len(Message)>=len_json:
            break
    # print 'Message:',Message
    str_json = Message.decode()
    if len(str_json) == len_json:
        nRet = 0
    Dict = json.loads(str_json)
    return nRet, Dict

# 接收一个字典,将其转换成json文件,并计算大小,发送至服务器
def SendJuderData(hSocket, dict_send):
    str_json = json.dumps(dict_send)
    len_json = str(len(str_json)).zfill(8)
    str_all = len_json + str_json
    # print 'str_all:',str_all
    ret = hSocket.sendall(str_all)
    if ret == None:
        ret = 0
    # print 'sendall', ret
    return ret

# 用户自定义函数, 返回字典FlyPlane, 需要包括 "UAV_info", "purchase_UAV" 两个key.
def AlgorithmCalculationFun(MatchStatus):
    global UAV_price_dict  ## 用飞机型号为key索引，方便查找
    global we_parking, map_range, h_low, h_high, building
    global min_value_type  ##最小飞机的型号
    global enemy_parking  ##敌方停机坪
    global up_down_flag ##停机坪上空有没有正在上升或者下降的飞机
    # global dis_parking  ##两个停机坪距离
    global min_uav_no_init, max_uav_no_init  ## 最小最大飞机编号


    UAV_we = MatchStatus["UAV_we"]
    UAV_enemy = MatchStatus['UAV_enemy']
    goods = MatchStatus['goods']
    UAV_info=[]

    goods_dict = {} #用goods的编号做key索引
    for g in goods:
        goods_dict[g['no']] = g

    UAV_we_dict = {}##用UAV_we的编号做key索引
    for uav_we in UAV_we:
        UAV_we_dict[uav_we['no']] = uav_we

    UAV_enemy_dict = {}##用UAV_enemy的编号做key索引
    for uav_enemy in UAV_enemy:
        UAV_enemy_dict[uav_enemy['no']] = uav_enemy

    num_uav_we,num_uav_enemy = len(UAV_we),len(UAV_enemy)  ##双方飞机数量
    for uav_we in UAV_we:
        if uav_we["status"]==1: ##坠毁
            num_uav_we-=1

    score_uav_goods, uav_unassigned, no_UAV_we_loading, need_charge_no,charged_unlifted_no,up_down_flag = func.classsify_category(min_uav_no_init,min_value_type,up_down_flag,UAV_price_dict,UAV_we,UAV_enemy,goods,we_parking,h_low)
    time_score = time()

    match_dict, uav_unassigned, goods_unassigned, charged_unlifted_no, match_no_set, up_down_flag = func.match_uav_goods(up_down_flag, UAV_we_dict, we_parking, h_low, score_uav_goods, charged_unlifted_no, goods, uav_unassigned)

    clear_match_dict, uav_unassigned,no_UAV_we_loading = func.clear_enemy_block(no_UAV_we_loading,uav_unassigned,goods_dict,UAV_price_dict,UAV_we_dict,UAV_enemy,UAV_enemy_dict,h_low)
    time_match = time()

    uav_unassigned, block_dict, charged_unlifted_no, need_charge_no, match_dict,up_down_flag = func.block_enemy(up_down_flag,match_dict,match_no_set,charged_unlifted_no,need_charge_no,we_parking,enemy_parking, uav_unassigned, UAV_we_dict, UAV_enemy, UAV_price_dict,goods_dict, h_low)

    for no_uav_we, block_point in block_dict.items(): ##堵敌
        type = UAV_we_dict[no_uav_we]['type']
        start_node = func.creat_node(UAV_we_dict[no_uav_we]['x'], UAV_we_dict[no_uav_we]['y'],UAV_we_dict[no_uav_we]['z'], None, -1, type)
        block_x, block_y, block_z = block_point
        end_node = func.creat_node(block_x, block_y, block_z)
        x_pre, y_pre, z_pre = start_node['x'], start_node['y'], start_node['z']

        x, y, z = func.A_star(num_uav_we,num_uav_enemy,start_node, end_node, UAV_info, UAV_enemy, h_low, h_high,map_range, building, we_parking, UAV_price_dict, goods_dict)
        uav_info_dict = {}
        # 判断是否载货
        # goods_no = UAV_we_dict[no_uav_we]['goods_no']
        # if goods_no == -1:
        #     remain_electricity = UAV_we_dict[no_uav_we]['remain_electricity']
        # else:
        #     remain_electricity = max(0,UAV_we_dict[no_uav_we]['remain_electricity'] - goods_dict[goods_no]['weight'])
        remain_electricity = UAV_we_dict[no_uav_we]['remain_electricity']
        uav_info_dict['no'], uav_info_dict['x'], uav_info_dict['y'], uav_info_dict['z'], uav_info_dict['goods_no'] = no_uav_we, x, y, z, UAV_we_dict[no_uav_we]['goods_no']
        uav_info_dict['remain_electricity'] = remain_electricity
        uav_info_dict['x_pre'], uav_info_dict['y_pre'], uav_info_dict['z_pre'] = x_pre, y_pre, z_pre
        UAV_info.append(uav_info_dict)

    for no_uav_we,no_goods_and_flag in no_UAV_we_loading.items():    #载有商品的己方无人机移动
        no_goods,can_clear_flag = no_goods_and_flag
        type = UAV_we_dict[no_uav_we]['type']
        start_node = func.creat_node(UAV_we_dict[no_uav_we]['x'], UAV_we_dict[no_uav_we]['y'],UAV_we_dict[no_uav_we]['z'],None,no_goods,type,UAV_we_dict[no_uav_we]['remain_electricity'])
        x_pre, y_pre, z_pre = start_node['x'], start_node['y'], start_node['z']
        end_node = func.creat_node(goods_dict[no_goods]['end_x'], goods_dict[no_goods]['end_y'], 0, None, no_goods)
        x, y, z = func.A_star(num_uav_we,num_uav_enemy,start_node, end_node, UAV_info,UAV_enemy, h_low, h_high, map_range,building,we_parking,UAV_price_dict,goods_dict,can_clear_flag=can_clear_flag)
        #此处注释，因为不用自己放下商品，服务器自己放
        # if x == goods_dict[no_goods]['end_x'] and y == goods_dict[no_goods]['end_y'] and z == 0:  ## 到达商品的终点，放下商品
        #     no_goods = -1
        remain_electricity = max(0,UAV_we_dict[no_uav_we]['remain_electricity'] - goods_dict[no_goods]['weight'])
        uav_info_dict = {}
        uav_info_dict['no'], uav_info_dict['x'], uav_info_dict['y'], uav_info_dict['z'], uav_info_dict['goods_no'] = no_uav_we, x, y, z, no_goods
        uav_info_dict['x_pre'], uav_info_dict['y_pre'], uav_info_dict['z_pre'] = x_pre, y_pre, z_pre
        uav_info_dict['remain_electricity'] = remain_electricity
        UAV_info.append(uav_info_dict)



    # if clear_match_dict:
    #     print clear_match_dict
    for no_uav_we,enemy_point in clear_match_dict.items(): ##清道夫
        type = UAV_we_dict[no_uav_we]['type']
        enemy_x,enemy_y,enemy_z = enemy_point
        start_node = func.creat_node(UAV_we_dict[no_uav_we]['x'], UAV_we_dict[no_uav_we]['y'],UAV_we_dict[no_uav_we]['z'], None, -1, type)
        x_pre, y_pre, z_pre = start_node['x'], start_node['y'], start_node['z']
        end_node = func.creat_node(enemy_x,enemy_y,enemy_z)
        x, y, z = func.A_star(num_uav_we, num_uav_enemy, start_node, end_node, UAV_info, UAV_enemy, h_low, h_high,map_range, building, we_parking, UAV_price_dict, goods_dict)
        remain_electricity = UAV_we_dict[no_uav_we]['remain_electricity']
        uav_info_dict = {}
        uav_info_dict['no'], uav_info_dict['x'], uav_info_dict['y'], uav_info_dict['z'], uav_info_dict['goods_no'] = no_uav_we, x, y, z, -1
        uav_info_dict['x_pre'], uav_info_dict['y_pre'], uav_info_dict['z_pre'] = x_pre, y_pre, z_pre
        uav_info_dict['remain_electricity'] = remain_electricity
        UAV_info.append(uav_info_dict)

    sorted_charged_unlifted = sorted(charged_unlifted_no,key = lambda x:(-UAV_we_dict[x]['z'],-UAV_we_dict[x]["load_weight"])) ##先未升空无人机按高度排序，高度一致则按无人机从小到大开始升空
    if sorted_charged_unlifted:##需要升空的不为空
        for no_uav_we in sorted_charged_unlifted:  ##未升空的
            if up_down_flag==-1:
                actions = [10]
                z_next = UAV_we_dict[no_uav_we]['z'] - 1
            else:
                up_down_flag = 1
                actions = [9]
                z_next = UAV_we_dict[no_uav_we]['z'] + 1
            type = UAV_we_dict[no_uav_we]['type']
            action_valid = func.avoid_we(UAV_we_dict[no_uav_we], actions, UAV_info, we_parking) ##看看上升是否会撞己方
            x_pre,y_pre,z_pre = UAV_we_dict[no_uav_we]['x'],UAV_we_dict[no_uav_we]['y'],UAV_we_dict[no_uav_we]['z']
            if action_valid:
                x, y, z = x_pre,y_pre,z_next
            else:
                x, y, z = x_pre,y_pre,z_pre
            x,y,z = func.no_cross_border(x,y,z,map_range['x'],map_range['y'],h_high)
            # if (x,y,z)==(we_parking['x'],we_parking['y'],0): ##计算剩余电量
            if z==0:##计算剩余电量
                remain_electricity = min(UAV_we_dict[no_uav_we]['remain_electricity'] + UAV_price_dict[type]['charge'],UAV_price_dict[type]['capacity'])
            else:
                remain_electricity = UAV_we_dict[no_uav_we]['remain_electricity']
            uav_info_dict = {}
            uav_info_dict['no'], uav_info_dict['x'], uav_info_dict['y'], uav_info_dict['z'], uav_info_dict['goods_no'] = no_uav_we, x, y, z, UAV_we_dict[no_uav_we]["goods_no"]
            uav_info_dict['x_pre'], uav_info_dict['y_pre'], uav_info_dict['z_pre'] = x_pre,y_pre,z_pre
            uav_info_dict['remain_electricity'] = remain_electricity
            UAV_info.append(uav_info_dict)

    for no_uav_we in need_charge_no: ##充电
        type = UAV_we_dict[no_uav_we]['type']
        start_node = func.creat_node(UAV_we_dict[no_uav_we]['x'], UAV_we_dict[no_uav_we]['y'],UAV_we_dict[no_uav_we]['z'], None, -1, type)
        x_pre, y_pre, z_pre = start_node['x'], start_node['y'], start_node['z']
        end_node = func.creat_node(we_parking['x'], we_parking['y'], 0)
        x, y, z = func.A_star(num_uav_we, num_uav_enemy, start_node, end_node, UAV_info, UAV_enemy, h_low,h_high, map_range, building, we_parking, UAV_price_dict,goods_dict,up_down_flag)
        if (x,y,z)==(we_parking['x'],we_parking['y'],0): ##计算剩余电量
            remain_electricity = min(UAV_we_dict[no_uav_we]['remain_electricity'] + UAV_price_dict[type]['charge'],UAV_price_dict[type]['capacity'])
        else:
            remain_electricity = UAV_we_dict[no_uav_we]['remain_electricity']
        uav_info_dict = {}
        uav_info_dict['no'], uav_info_dict['x'], uav_info_dict['y'], uav_info_dict['z'], uav_info_dict['goods_no'] = no_uav_we, x, y, z, UAV_we_dict[no_uav_we]['goods_no']
        uav_info_dict['x_pre'], uav_info_dict['y_pre'], uav_info_dict['z_pre'] = x_pre, y_pre, z_pre
        uav_info_dict['remain_electricity'] = remain_electricity
        UAV_info.append(uav_info_dict)

    for no_uav_we,no_goods in match_dict.items():  #指定了商品的己方空载无人机移动
        type = UAV_we_dict[no_uav_we]['type']
        start_node = func.creat_node(UAV_we_dict[no_uav_we]['x'],UAV_we_dict[no_uav_we]['y'],UAV_we_dict[no_uav_we]['z'],None,-1,type)
        end_node = func.creat_node(goods_dict[no_goods]['start_x'],goods_dict[no_goods]['start_y'],0,None,no_goods)
        x_pre,y_pre,z_pre = start_node['x'], start_node['y'],start_node['z']
        x,y,z = func.A_star(num_uav_we,num_uav_enemy,start_node,end_node,UAV_info,UAV_enemy,h_low,h_high,map_range,building,we_parking,UAV_price_dict,goods_dict)
        if x!=goods_dict[no_goods]['start_x'] or y != goods_dict[no_goods]['start_y'] or z!=0: ## 未到达商品的起点，没拿起商品
            no_goods = -1
            remain_electricity = UAV_we_dict[no_uav_we]['remain_electricity']
        else:
            remain_electricity = UAV_we_dict[no_uav_we]['remain_electricity'] - goods_dict[no_goods]['weight']

        uav_info_dict = {}
        uav_info_dict['no'],uav_info_dict['x'],uav_info_dict['y'],uav_info_dict['z'],uav_info_dict['goods_no'] = no_uav_we,x,y,z,no_goods
        uav_info_dict['x_pre'],uav_info_dict['y_pre'],uav_info_dict['z_pre'] = x_pre,y_pre,z_pre
        uav_info_dict['remain_electricity'] = remain_electricity
        UAV_info.append(uav_info_dict)

    for no_uav_we in uav_unassigned: ## 未指定的己方无人机的移动
        type = UAV_we_dict[no_uav_we]['type']
        x_pre, y_pre, z_pre = UAV_we_dict[no_uav_we]['x'], UAV_we_dict[no_uav_we]['y'], UAV_we_dict[no_uav_we]['z']
        x,y,z,up_down_flag = func.unassigned_uav_move(up_down_flag,num_uav_we,num_uav_enemy,UAV_we_dict[no_uav_we],goods_unassigned,h_low, h_high, map_range,building,UAV_info,we_parking,UAV_enemy,UAV_price_dict,goods_dict) ## 己方未指定的无人机移动方案
        x,y,z = func.no_cross_border(x,y,z,map_range['x'],map_range['y'],h_high)
        uav_info_dict = {}
        # goods_no = UAV_we_dict[no_uav_we]['goods_no']
        # if goods_no==-1:
        #     remain_electricity = UAV_we_dict[no_uav_we]['remain_electricity']
        # else:
        #     remain_electricity = max(0,UAV_we_dict[no_uav_we]['remain_electricity'] - goods_dict[goods_no]['weight'])
        if (x, y, z) == (we_parking['x'], we_parking['y'], 0):  ##计算剩余电量
            remain_electricity = min(UAV_we_dict[no_uav_we]['remain_electricity'] + UAV_price_dict[type]['charge'],UAV_price_dict[type]['capacity'])
        else:
            remain_electricity = UAV_we_dict[no_uav_we]['remain_electricity']
        uav_info_dict['no'], uav_info_dict['x'], uav_info_dict['y'], uav_info_dict['z'], uav_info_dict['goods_no'] = no_uav_we, x, y, z, UAV_we_dict[no_uav_we]['goods_no']
        uav_info_dict['x_pre'], uav_info_dict['y_pre'], uav_info_dict['z_pre'] = x_pre, y_pre, z_pre
        uav_info_dict['remain_electricity'] = remain_electricity
        UAV_info.append(uav_info_dict)

    time_Astar = time()

    type_choose_list = func.buy_policy(min_value_type,UAV_enemy_dict,num_uav_we,num_uav_enemy,we_parking,h_low,MatchStatus['we_value'],UAV_price_dict,goods_unassigned,goods_dict) #购买

    purchase_UAV = []
    for type in type_choose_list:
        purchase_UAV.append({"purchase":type})

    time_purhase = time()

    FlyPlane = {}
    for uav_info_dict in UAV_info:
        del uav_info_dict['x_pre']
        del uav_info_dict['y_pre']
        del uav_info_dict['z_pre']
    FlyPlane['UAV_info'],FlyPlane['purchase_UAV'] = UAV_info,purchase_UAV

    return FlyPlane,time_score,time_match,time_Astar,time_purhase

def main(szIp, nPort, szToken):
    print "server ip %s, prot %d, token %s\n" % (szIp, nPort, szToken)

    # Need Test // 开始连接服务器
    hSocket = socket.socket()
    hSocket.connect((szIp, nPort))

    # 接受数据  连接成功后，Judger会返回一条消息：
    nRet, _ = RecvJuderData(hSocket)
    if (nRet != 0):
        return nRet

    # // 生成表明身份的json
    token = {}
    token['token'] = szToken
    token['action'] = "sendtoken"

    # // 选手向裁判服务器表明身份(Player -> Judger)
    nRet = SendJuderData(hSocket, token)
    if nRet != 0:
        return nRet

    # //身份验证结果(Judger -> Player), 返回字典Message
    nRet, Message = RecvJuderData(hSocket)
    if nRet != 0:
        return nRet
    if Message["result"] != 0:
        print "token check error\n"
        return -1

    # // 选手向裁判服务器表明自己已准备就绪(Player -> Judger)
    stReady = {}
    stReady['token'] = szToken
    stReady['action'] = "ready"
    nRet = SendJuderData(hSocket, stReady)
    if nRet != 0:
        return nRet

    # //对战开始通知(Judger -> Player)
    nRet, Message = RecvJuderData(hSocket)
    if nRet != 0:
        return nRet
    time_start = time()

    # 初始化地图信息
    MapInfo = Message["map"]

    # 初始化比赛状态信息
    MatchStatus = {}
    MatchStatus["time"] = 0

    # 初始化飞机状态信息
    FlyPlane = {}
    FlyPlane["num_uav"] = len(MapInfo["init_UAV"])
    FlyPlane["UAV_info"] = [{} for i in range(FlyPlane["num_uav"])]
    FlyPlane['purchase_UAV'] = []

    # 每一步的飞行计划
    FlyPlane_send = {}
    FlyPlane_send["token"] = szToken
    FlyPlane_send["action"] = "flyPlane"

    global UAV_price_dict ## 用飞机型号为key索引，方便查找
    UAV_price_dict = {}
    for uav_price in MapInfo['UAV_price']:
        UAV_price_dict[uav_price["type"]] = uav_price

    global we_parking, map_range, h_low, h_high, building
    we_parking, map_range, h_low, h_high, building = MapInfo['parking'], MapInfo['map'], MapInfo['h_low'], MapInfo['h_high'], MapInfo['building']

    global enemy_parking # 敌方停机坪
    enemy_parking = dict()

    global up_down_flag  ##停机坪上空有没有正在上升或者下降的飞机 1,-1,0 分别代表上升/下降/没有
    up_down_flag=0

    global min_value_type, min_type_value ## 求最小飞机型号和价钱
    min_value_type = None  ##最小的飞机型号
    min_type_value = 65535  ##最小飞机的价钱 初始化
    for uav_price_dict in MapInfo["UAV_price"]:
        if uav_price_dict['value'] < min_type_value:
            min_value_type = uav_price_dict['type']
            min_type_value = uav_price_dict['value']

    func.func_global_variable()

    global min_uav_no_init,max_uav_no_init  ## 初始时最小最大飞机编号
    min_uav_no_init,max_uav_no_init = MapInfo["init_UAV"][0]["no"],MapInfo["init_UAV"][0]["no"] ##初始化
    min_value,max_value = 65535,0

    for i in range(FlyPlane["num_uav"]):
        FlyPlane["UAV_info"][i]["no"] = MapInfo["init_UAV"][i]["no"]
        FlyPlane["UAV_info"][i]["x"] = MapInfo["init_UAV"][i]["x"]
        FlyPlane["UAV_info"][i]["y"] = MapInfo["init_UAV"][i]["y"]
        FlyPlane["UAV_info"][i]["z"] = MapInfo["init_UAV"][i]["z"]
        FlyPlane["UAV_info"][i]["goods_no"] = MapInfo["init_UAV"][i]["goods_no"]
        FlyPlane["UAV_info"][i]["remain_electricity"] = MapInfo["init_UAV"][i]["remain_electricity"] #+ UAV_price_dict[MapInfo["init_UAV"][i]['type']]["charge"]

        value_this = UAV_price_dict[MapInfo["init_UAV"][i]["type"]]["value"]
        if value_this<min_value:
            min_uav_no_init = MapInfo["init_UAV"][i]["no"]
            min_value = value_this
        if value_this>max_value:
            max_uav_no_init = MapInfo["init_UAV"][i]["no"]
            max_value = value_this

    # // 根据服务器指令，不停的接受发送数据
    while True:
        # // 进行当前时刻的数据计算, 填充飞行计划，注意：0时刻不能进行移动，即第一次进入该循环时
        if MatchStatus["time"] != 0:
            FlyPlane,time_score,time_match,time_Astar,time_purhase = AlgorithmCalculationFun(MatchStatus)
        else:
            time_score, time_match, time_Astar, time_purhase = time_start,time_start,time_start,time_start
        FlyPlane_send['UAV_info'] = FlyPlane['UAV_info']


        #print len(FlyPlane['UAV_info'])
        FlyPlane_send['purchase_UAV'] = FlyPlane['purchase_UAV']
        # print MatchStatus["time"]
        # //发送飞行计划
        nRet = SendJuderData(hSocket, FlyPlane_send)
        if nRet != 0:
            return nRet
        time_end = time()
        if time_end-time_start < 1.0:
            print "time: %s, time_len: %.4f" % (MatchStatus["time"],time_end-time_start)
        else:
            print "time:%s  score:%.3f  match:%.3f  Astar:%.3f purhase:%.3f send:%.3f" % (MatchStatus["time"],time_score-time_start,time_match-time_score,time_Astar-time_match,time_purhase-time_Astar,time_end-time_purhase)
        # // 接受当前比赛状态
        nRet, MatchStatus = RecvJuderData(hSocket)

        if not enemy_parking:
            # global dis_parking ##两个停机坪距离
            enemy_parking['x'] = MatchStatus["UAV_enemy"][0]['x']
            enemy_parking['y'] = MatchStatus["UAV_enemy"][0]['y']
            dis_parking = func.min_step(we_parking['x'], we_parking['y'], h_low, enemy_parking['x'], enemy_parking['y'],h_low, h_low)
            if dis_parking >= len(MapInfo["init_UAV"]) - 1:
                min_uav_no_init = -1

        if nRet != 0:
            return nRet
        time_start = time()
        if MatchStatus["match_status"] == 1:
            we_uavs_value,enemy_uavs_value = 0,0
            for uav_we in MatchStatus["UAV_we"]:
                if uav_we["status"] != 1:
                    we_uavs_value += UAV_price_dict[uav_we['type']]["value"]
            for uav_enemy in MatchStatus["UAV_enemy"]:
                if uav_enemy["status"] != 1:
                    enemy_uavs_value += UAV_price_dict[uav_enemy['type']]["value"]
            print "game over, we value %d, enemy value %d" % (MatchStatus["we_value"], MatchStatus["enemy_value"])
            print "game over, we uavs value %d, enemy uavs value %d" % (we_uavs_value, enemy_uavs_value)
            print "game over, we total value %d, enemy total value %d" % (MatchStatus["we_value"] + we_uavs_value, MatchStatus["enemy_value"] + enemy_uavs_value)
            hSocket.close()
            return 0

if __name__ == "__main__":
    if len(sys.argv) == 4:
        print "Server Host: " + sys.argv[1]
        print "Server Port: " + sys.argv[2]
        print "Auth Token: " + sys.argv[3]
        main(sys.argv[1], int(sys.argv[2]), sys.argv[3])
    else:
        print "need 3 arguments"