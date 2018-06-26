# -*- coding: utf-8 -*-
from copy import deepcopy
from random import choice
from random import randint
from time import time


def func_global_variable():
    global remain_need_coefficient, buy_small_coefficient, H_coefficient, enough_pick_proportion, dis_left_proportion, A_star_time_limit,buy_enemy_num_proportion
    global enemy_total_value_proportion ##一架敌机的总价值中，货物价值的系数
    enemy_total_value_proportion = 0.5 ##一架敌机的总价值中，货物价值的系数
    remain_need_coefficient = 1.5  ##匹配无人机和物品时，剩余电量和所需最低电量的比例
    buy_small_coefficient = 1.8  ##买了无人机以后，如果还有钱并且自己的飞机不到对方的buy_small_coefficient倍，就接着买小的
    H_coefficient = 1.5  ##A星算法中H的系数
    enough_pick_proportion = 0.1  ##某uav可以拿起并电量足以送到的商品数量占他可以拿起数量的系数
    dis_left_proportion = 0.6  ##买飞机时，某飞机距离和商品剩余时间的比例
    A_star_time_limit = 0.08  ##A星算法一次的搜索时间限制,提交的版本改成0.1
    buy_enemy_num_proportion = 0.8 ##敌机大于我们这个倍数时，全买最小的


def move(x, y, z, action):
    action_dict = {0: [0, 0, 0], 1: [0, 1, 0], 2: [1, 1, 0], 3: [1, 0, 0], 4: [1, -1, 0], 5: [0, -1, 0],
                   6: [-1, -1, 0], 7: [-1, 0, 0], 8: [-1, 1, 0], 9: [0, 0, 1], 10: [0, 0, -1]}
    xx = x + action_dict[action][0]
    yy = y + action_dict[action][1]
    zz = z + action_dict[action][2]
    return xx, yy, zz


def judge_action(x_pre, y_pre, z_pre, x, y, z):  ##判断该移动是哪个动作
    actions = [i for i in range(11)]
    for action in actions:
        if (x, y, z) == move(x_pre, y_pre, z_pre, action):
            return action


def buy_policy(min_value_type, UAV_enemy_dict, num_uav_we, num_uav_enemy, parking, h_low, surplus_value_we,UAV_price_dict, goods_unassigned, goods_dict):
    type_choose = None
    type_choose_list = []
    max_score = 0
    global dis_left_proportion,buy_enemy_num_proportion
    min_type_value = UAV_price_dict[min_value_type]["value"]  ##最小飞机型号的价钱
    # if ((num_uav_we==2 and num_uav_enemy>2) or num_uav_we==1 or num_uav_enemy>1.2*num_uav_we) and surplus_value_we>=min_type_value: ##需要紧急买小飞机，并且钱够
    if surplus_value_we < min_type_value:  ##连最小的飞机都买不起
        return type_choose_list
    while num_uav_we <= 2 or num_uav_enemy >= num_uav_we * buy_enemy_num_proportion:  ##需要紧急买小飞机
        type_choose_list.append(min_value_type)
        surplus_value_we -= min_type_value
        if surplus_value_we < min_type_value:
            return type_choose_list
    for type in UAV_price_dict:
        if UAV_price_dict[type]["value"] > surplus_value_we:
            continue

        for no_goods in goods_unassigned:
            if UAV_price_dict[type]["load_weight"] < goods_dict[no_goods]["weight"]:  ##装不下该货物
                continue
            dis_we = min_step(parking['x'], parking['y'], 0, goods_dict[no_goods]['start_x'],
                              goods_dict[no_goods]['start_y'], 0, h_low)
            if dis_we >= goods_dict[no_goods]["left_time"] * dis_left_proportion:  ##时间不够
                continue
            continue_flag = False  ##判断有没有更近的能装下该货物的敌机
            for no_uav_enemy, uav_enemy in UAV_enemy_dict.items():  ##判断有没有更近的能装下该货物的敌机
                if uav_enemy["status"] == 0 and uav_enemy["goods_no"] == -1 and UAV_price_dict[uav_enemy['type']]["load_weight"] >= goods_dict[no_goods]["weight"]:
                    dis_enemy = min_step(uav_enemy['x'], uav_enemy['y'], uav_enemy['z'],
                                         goods_dict[no_goods]['start_x'], goods_dict[no_goods]['start_y'], 0, h_low)
                    if goods_dict[no_goods]["left_time"] > dis_enemy < dis_we:
                        continue_flag = True  ##找到更有优势的敌机
                        break
            if continue_flag:
                continue
            # score = (2 - (dis_we + 0.00001) / goods_dict[no_goods]["left_time"]) * goods_dict[no_goods]["weight"] / UAV_price_dict[type]["load_weight"]
            score = (2 - (dis_we + 0.00001) / goods_dict[no_goods]["left_time"]) * goods_dict[no_goods]["value"] / UAV_price_dict[type]["value"]
            if score > max_score:
                type_choose = type
                max_score = score

    if type_choose:  ##找到其他合适购买的飞机
        type_choose_list.append(type_choose)
        global buy_small_coefficient  ###买了无人机以后，如果还有钱并且自己的飞机不到对方的buy_small_coefficient倍，就接着买
        if num_uav_we < buy_small_coefficient * num_uav_enemy and surplus_value_we - UAV_price_dict[type_choose][
            "value"] >= min_type_value:  ##剩余钱购买最小的飞机就买
            type_choose_list.append(min_value_type)
    return type_choose_list


def min_step(a_x, a_y, a_z, b_x, b_y, b_z, h_low):  # 从a的位置到b的位置最短需要走几步
    dis_x = abs(a_x - b_x)
    dis_y = abs(a_y - b_y)
    dis_flat = max(dis_x, dis_y)  # 斜着走min(dis_x,dis_y)步，再直着走max()-min()步

    if a_z < h_low and (a_x != b_x or a_y != b_y):
        dis_vertical = abs(h_low - b_z) + h_low - a_z
    else:
        dis_vertical = abs(a_z - b_z)

    dis = dis_vertical + dis_flat
    return dis


def unassigned_uav_move(up_down_flag,num_uav_we, num_uav_enemy, uav_we, goods_unassigned, h_low, h_high, map_range, building,UAV_info, we_parking, UAV_enemy, UAV_price_dict, goods_dict):
    if uav_we['z'] < h_low:
        actions = [0, 9, 10]
        action_valid = avoid_we(uav_we, actions, UAV_info, we_parking)
        if 9 in action_valid:
            action = 9  ##上升
            up_down_flag = 1
        elif 0 in action_valid:
            action = 0
        else:
            action = 10
            if uav_we['z'] <= 0:
                action = 0
    else:
        actions = [i for i in range(11)]
        action_avoid_we = avoid_we(uav_we, actions, UAV_info, we_parking)
        action_avoid_build = avoid_build_board(uav_we, h_low, h_high, map_range, building, action_avoid_we)
        action_avoid_enemy = action_avoid_build
        for uav_enemy in UAV_enemy:
            dis = min_step(uav_we['x'], uav_we['y'], uav_we['z'], uav_enemy['x'], uav_enemy['y'], uav_enemy['z'], h_low)
            if dis <= 2:
                action_avoid_enemy = avoid_enemy(num_uav_we, num_uav_enemy, uav_we, uav_enemy, action_avoid_enemy,
                                                 UAV_price_dict, goods_dict, h_low, we_parking)
        if action_avoid_enemy:  ##是否有可行动作
            action = choice(action_avoid_enemy)
        elif action_avoid_build:
            action = choice(action_avoid_build)
        elif action_avoid_we:
            action = choice(action_avoid_we)
        else:
            action = choice(actions)
    x, y, z = move(uav_we['x'], uav_we['y'], uav_we['z'], action)
    return x, y, z,up_down_flag


def creat_node(x, y, z, parent_str=None, goods_no=-1, type=None,remain_electricity=0,load_weight=0):
    node = {}
    node['parent_str'] = parent_str
    node['x'], node['y'], node['z'], node['G'], node['H'], node['F'] = x, y, z, 0, 0, 0
    node['action_valid'] = []
    node["goods_no"] = goods_no
    node["type"] = type
    node['load_weight'] = load_weight
    node['remain_electricity']=remain_electricity
    return node


def avoid_build_board(node, h_low, h_high, map_range, building, actions):  # 躲避障碍物
    action_valid = actions[:]
    # 太低不可以水平飞
    if node['z'] < h_low:
        if node['z'] == 0:
            action_valid = [0, 9]
            # action_suicide = [1,2,3,4,5,6,7,8,10]
        else:
            action_valid = [0, 9, 10]  # 不可以水平
            # action_suicide = [1, 2, 3, 4, 5, 6, 7, 8]
        return action_valid  # ,action_suicide
    # action_suicide = []
    remove_set = set()
    for action in action_valid:
        x, y, z = move(node['x'], node['y'], node['z'], action)
        if x < 0 or x >= map_range['x'] or y < 0 or y >= map_range['y'] or z < 0 or z > h_high:  # 越界
            remove_set.add(action)
            continue
        for build in building:
            if build['x'] <= x <= (build['x'] + build['l'] - 1) and build['y'] <= y <= (
                    build['y'] + build['w'] - 1) and z < build['h']:
                remove_set.add(action)
                break
    for action in remove_set:
        action_valid.remove(action)
    return action_valid  # , action_suicide


## 躲避己方飞机
def avoid_we(node, actions, UAV_info, we_parking, up_down_flag=0, h_low=0):
    action_valid = actions[:]
    next_posi_got = set()  # next_posi_got：已经得到下一步位置的无人机及所去的结点,传入的应该是正在生成中的UAV_info
    step_mid = set()  ## 已经规划好的无人机行动前后位置的中点
    for uav_info_dict in UAV_info:
        x, y, z, x_pre, y_pre, z_pre = uav_info_dict['x'], uav_info_dict['y'], uav_info_dict['z'], uav_info_dict[
            'x_pre'], uav_info_dict['y_pre'], uav_info_dict['z_pre']

        next_posi_got.add(str(x) + '_' + str(y) + '_' + str(z))
        # step_mid[(str((x+x_pre)/2.0) + '_' + str((y+y_pre)/2.0) + '_' + str((z+z_pre)/2.0))] = [(x_pre,y_pre,z_pre),(x,y,z)]
        step_mid.add(str(x + x_pre) + '_' + str(y + y_pre) + '_' + str(z + z_pre))

    x_pre, y_pre, z_pre = node['x'], node['y'], node['z']
    remove_set = set()
    for action in action_valid:
        x, y, z = move(x_pre, y_pre, z_pre, action)
        posi_str = str(x) + '_' + str(y) + '_' + str(z)
        # step_mid_str = str((x+x_pre)/2.0) + '_' + str((y+y_pre)/2.0) + '_' + str((z+z_pre)/2.0)##动作前后的中点
        step_mid_str = str(x + x_pre) + '_' + str(y + y_pre) + '_' + str(z + z_pre)
        if (x, y, z) != (we_parking['x'], we_parking['y'], 0) and (posi_str in next_posi_got or step_mid_str in step_mid):  # 停机坪不算撞
            remove_set.add(action)
        elif up_down_flag == 1 and (x, y) == (we_parking['x'], we_parking['y']) and z <= h_low:  ##有己方刚刚升空,针对回家充电的飞机不可以堵住家门
            remove_set.add(action)
    for action in remove_set:
        action_valid.remove(action)

        # if (x, y, z) != (we_parking['x'], we_parking['y'], 0):
        #     if posi_str in next_posi_got:
        #         action_valid.remove(action)
        #     elif step_mid_str in step_mid:
        #         action_valid.remove(action)

    return action_valid


## 躲避敌人时，是否值得冒险，宁可撞击
def if_worth_risk(num_uav_we, num_uav_enemy, uav_we, uav_enemy, UAV_price_dict, goods_dict, h_low, we_parking,can_clear_flag=False):
    risk_flag = False
    global enemy_total_value_proportion  ##一架敌机的总价值中，货物价值的系数
    goods_no = uav_we["goods_no"]
    if goods_no!=-1:
        score_we = UAV_price_dict[uav_we['type']]["value"] + goods_dict[uav_we["goods_no"]]["value"] * enemy_total_value_proportion
    else:
        score_we = UAV_price_dict[uav_we['type']]["value"]

    if uav_enemy["goods_no"] != -1:
        score_enemy = (UAV_price_dict[uav_enemy['type']]["value"] + goods_dict[uav_enemy["goods_no"]]["value"]) * enemy_total_value_proportion  # / dis
    else:
        score_enemy = UAV_price_dict[uav_enemy['type']]["value"]

    if (num_uav_we == 2 and num_uav_enemy > 2) or num_uav_we == 1:  # 飞机太少不冒险，否则没有飞机直接判输
        risk_flag = False
    elif num_uav_enemy == 1 and num_uav_we > 1:  ##敌机全毁，直接赢
        risk_flag = True
    elif goods_no == -1:
        # if UAV_price_dict[uav_we['type']]["value"] == UAV_price_dict[uav_enemy['type']]["value"] and num_uav_we >= num_uav_enemy:
        #     risk_flag = True
        # elif UAV_price_dict[uav_we['type']]["value"] < UAV_price_dict[uav_enemy['type']]["value"]:
        #     risk_flag = True
        if score_we<score_enemy or (UAV_price_dict[uav_we['type']]["value"] == UAV_price_dict[uav_enemy['type']]["value"]):
            risk_flag = True
        elif we_parking["x"] == uav_enemy['x'] and we_parking["y"] == uav_enemy['y'] and uav_enemy['z'] <= h_low + 1:  ##敌机堵家门口
            risk_flag = True
        elif uav_enemy['z'] == h_low and (abs(uav_enemy['x'] - we_parking["x"]) + abs(uav_enemy['y'] - we_parking["y"]) <= 2):
            risk_flag = True
    elif uav_we['z'] <= h_low:  ##自己有货物，被敌机堵了出口或者入口
        if (uav_enemy['x'], uav_enemy['y']) == (uav_we['x'], uav_we['y']) == (goods_dict[goods_no]['start_x'], goods_dict[goods_no]['start_y']):
            risk_flag = True
            # print 'a uav_we was blocked at goods start point'
        elif (uav_enemy['x'], uav_enemy['y']) == (goods_dict[goods_no]['end_x'], goods_dict[goods_no]['end_y']):
            min_step_need = min_step(uav_we['x'], uav_we['y'],uav_we['z'],goods_dict[goods_no]['end_x'], goods_dict[goods_no]['end_y'],0,h_low)
            if uav_we["remain_electricity"]/goods_dict[goods_no]["weight"]<=min_step_need+2:
                risk_flag = True
            # print 'a uav_we was blocked at goods end point'
    elif (uav_enemy['x'],uav_enemy['y'],uav_enemy['z'])==(goods_dict[goods_no]['end_x'], goods_dict[goods_no]['end_y'],h_low):##堵住我们的放货入口
        if not can_clear_flag:
            risk_flag = True
    else:  ## 有货，没被堵
        if score_we < score_enemy:
            risk_flag = True
    return risk_flag


## 躲避敌人
def avoid_enemy(num_uav_we, num_uav_enemy, uav_we, uav_enemy, actions, UAV_price_dict, goods_dict, h_low,we_parking,can_clear_flag=False):  # a是己方的飞机对象，返回己方的动作列表。距离为1或者2步的时候，才需要躲避
    action_valid = actions[:]
    remove_set = set()
    for action_we in action_valid:
        ax, ay, az = move(uav_we['x'], uav_we['y'], uav_we['z'], action_we)
        for action_enemy in range(11):
            if (ax, ay, az) == move(uav_enemy['x'], uav_enemy['y'], uav_enemy['z'], action_enemy):  # 函数返回多个值是tuple
                risk_flag = if_worth_risk(num_uav_we, num_uav_enemy, uav_we, uav_enemy, UAV_price_dict, goods_dict,h_low, we_parking,can_clear_flag)  ## 是否值得冒险尝试撞敌方
                if not risk_flag:
                    remove_set.add(action_we)
                break
    for action_we in remove_set:
        action_valid.remove(action_we)
    return action_valid


def A_star(num_uav_we, num_uav_enemy, start_node, end_node, UAV_info, UAV_enemy, h_low, h_high, map_range, building,we_parking, UAV_price_dict, goods_dict, up_down_flag=0,can_clear_flag=False):
    time_A_star_start = time()
    go_on_flag = True  ##是否结束求取路径，决定是否继续接着求
    all_actions = [i for i in range(11)]
    global A_star_time_limit
    path = []  ##初始化路径
    action = 0  ##初始化

    action_avoid_we = avoid_we(start_node, all_actions, UAV_info, we_parking, up_down_flag, h_low)
    action_avoid_build = avoid_build_board(start_node, h_low, h_high, map_range, building, action_avoid_we)
    action_avoid_enemy = deepcopy(action_avoid_build)
    for uav_enemy in UAV_enemy:
        if uav_enemy["status"] == 0:
            dis_we_enemy = min_step(start_node['x'], start_node['y'], start_node['z'], uav_enemy['x'], uav_enemy['y'],
                                    uav_enemy['z'], h_low)
            if dis_we_enemy <= 2:
                action_avoid_enemy = avoid_enemy(num_uav_we, num_uav_enemy, start_node, uav_enemy, action_avoid_enemy,
                                                 UAV_price_dict, goods_dict, h_low, we_parking,can_clear_flag)

    if (start_node['x'], start_node['y']) == (end_node['x'], end_node['y']):  # 在目标点上空
        if start_node['z'] == end_node['z']:  ##就在商品的目标点上
            action = 0
        elif start_node['z'] < end_node['z']:
            action = 9
        else:
            action = 10
        if action_avoid_enemy:
            if action not in action_avoid_enemy:
                action = choice(action_avoid_enemy)
        elif action_avoid_build:
            if action not in action_avoid_build:
                action = choice(action_avoid_build)
        elif action_avoid_we:
            if action not in action_avoid_we:
                action = choice(action_avoid_we)
        else:
            print 'zhuang ji zhuang ji \n\n\n\n\n\n\n\n\n'

        x, y, z = move(start_node['x'], start_node['y'], start_node['z'], action)
        path = [(start_node['x'], start_node['y'], start_node['z']), (x, y, z)]
    else:  ##未在目标点上空时
        end_node_z = h_low  ##用h_low替换目标点的高度坐标，减少计算，相当于只规划到目标点上空可横飞点的路径
        open_dict, close_dict = dict(), dict()  ### 示例{'24_32_60':node}
        end_node_str = str(end_node['x']) + '_' + str(end_node['y']) + '_' + str(end_node_z)
        start_node_str = str(start_node['x']) + '_' + str(start_node['y']) + '_' + str(start_node['z'])
        open_dict[start_node_str] = start_node

        while True:
            time_now = time()
            if time_now - time_A_star_start > A_star_time_limit:  ##提交的时候换成0.1
                print 'a star time out.........',
                path = []
                go_on_flag = False  ##不用继续搜索路径了
                break
            current_node_str, current_node = min(open_dict.items(), key=lambda x: x[1]['F'])
            # 对当前结点得到有效的动作
            action_valid = avoid_build_board(current_node, h_low, h_high, map_range, building, all_actions)
            if current_node_str == start_node_str:  # 一次规划只走一步，起始结点的下一步位置不可以和自己飞机位置相同
                action_valid = deepcopy(action_avoid_enemy)
            if 0 in action_valid:  # 删去原地不动的动作0
                action_valid.remove(0)
            current_node['action_vaild'] = action_valid[:]

            close_dict[current_node_str] = deepcopy(current_node)
            del open_dict[current_node_str]
            if current_node_str == end_node_str:
                break
            for action in current_node['action_vaild']:
                near_x, near_y, near_z = move(current_node['x'], current_node['y'], current_node['z'], action)
                near_node_str = str(near_x) + '_' + str(near_y) + '_' + str(near_z)
                if near_node_str in close_dict:
                    continue
                global H_coefficient  ##A星算法中H的系数
                if near_node_str not in open_dict:
                    near_node = creat_node(near_x, near_y, near_z, current_node_str)
                    near_node['G'] = current_node['G'] + 1
                    near_node['H'] = min_step(near_node['x'], near_node['y'], near_node['z'], end_node['x'],
                                              end_node['y'], end_node_z, h_low)
                    near_node['F'] = near_node['G'] + (near_node['H']) * H_coefficient
                    open_dict[near_node_str] = deepcopy(near_node)

                else:
                    if current_node['G'] + 1 < open_dict[near_node_str]['G']:
                        open_dict[near_node_str]['parent_str'] = current_node_str
                        open_dict[near_node_str]['G'] = current_node['G'] + 1
                        open_dict[near_node_str]['F'] = open_dict[near_node_str]['G'] + (open_dict[near_node_str][
                                                                                             'H']) * H_coefficient
            if not open_dict:
                path = []
                go_on_flag = False  ##不用继续搜索路径了
                break
        if go_on_flag:
            path = [(end_node['x'], end_node['y'], end_node_z)]
            parent_str = close_dict[end_node_str]['parent_str']
            while parent_str:
                time_now = time()
                if time_now - time_A_star_start > 1:
                    print 'find parent_str time out..........................................'
                    path = []
                    go_on_flag = False  ##不用继续搜索路径了
                    break
                parent_node = close_dict[parent_str]
                parent_position = (parent_node['x'], parent_node['y'], parent_node['z'])
                path.insert(0, parent_position)
                parent_str = close_dict[parent_str]['parent_str']
    if not path:  ##未找到路径
        action = choice(all_actions)
        if action_avoid_enemy:
            action = choice(action_avoid_enemy)
        elif action_avoid_build:
            action = choice(action_avoid_build)
        elif action_avoid_we:
            action = choice(action_avoid_we)
        # else:
        #     print 'zhuang ji zhuang ji \n\n\n\n\n\n\n\n\n'
        x, y, z = move(start_node['x'], start_node['y'], start_node['z'], action)
    elif len(path) == 1:  ##当前点就是终点
        x, y, z = path.pop(0)
    else:
        x, y, z = path.pop(1)
    x, y, z = no_cross_border(x, y, z, map_range['x'], map_range['y'], h_high)
    return x, y, z


def classsify_category(min_uav_no_init,min_value_type,up_down_flag, UAV_price_dict, UAV_we, UAV_enemy, goods, we_parking, h_low):  ## 分类无人机的用途、状态
    score_uav_goods = dict()
    uav_unassigned = set()  # ## 己方无人机中，未撞毁的已升空的空闲着的尚未指定的无人机编号
    need_charge_no = set()  ##己方无人机中，需要充电的，编号
    charged_unlifted_no = set()  ## 己方无人机中，还未升空，不用再充电的飞机编号
    no_UAV_we_loading = {}  ## 己方无人机中，未撞毁的正载有货物的  无人机编号:商品编号
    global enough_pick_proportion  ##某uav可以拿起并电量足以送到的商品数量占他可以拿起数量的比例

    zero_flag = True ##己方停机坪是否没有上升或者下降的飞机
    for uav_we in UAV_we:
        if (uav_we['x'], uav_we['y']) == (we_parking['x'], we_parking['y']) and 0<uav_we['z'] <= h_low:
            zero_flag = False
            break
    if zero_flag:
        up_down_flag = 0

    for uav_we in UAV_we:
        if uav_we["status"] == 1:  ##已经撞毁
            continue
        elif uav_we["goods_no"] != -1:  ## 该无人机未撞毁但是已经在载货
            no_UAV_we_loading[uav_we['no']] = [uav_we["goods_no"],False]
        else:  ## 未撞毁而且空载
            uav_load_weight = UAV_price_dict[uav_we["type"]]["load_weight"]
            uav_value = UAV_price_dict[uav_we["type"]]["value"]
            can_pick_num = 0  ##不考虑电量的话，可以走到并拿起的商品数量
            electricity_enough_num = 0  ##对可以到达的商品都电量充足的个数
            for g in goods:
                electricity_need = min_step(g['start_x'], g['start_y'], 0, g['end_x'], g['end_y'], 0, h_low) * g["weight"]
                if g['status'] == 0 and uav_load_weight >= g['weight'] and uav_we["remain_electricity"] >= electricity_need:
                    dis_we = min_step(uav_we['x'], uav_we['y'], uav_we['z'], g['start_x'], g['start_y'], 0, h_low)
                    continue_flag = False
                    for uav_enemy in UAV_enemy:  ##看看有没有敌机更有优势
                        if (uav_enemy['x'], uav_enemy['y']) == (g['start_x'], g['start_y']) and uav_enemy['z'] <= h_low \
                                and dis_we > uav_enemy['z'] and UAV_price_dict[uav_enemy["type"]]["load_weight"] >= g['weight'] \
                                and uav_enemy["remain_electricity"] >= electricity_need:
                            continue_flag = True
                            break
                    if continue_flag:
                        continue
                    if dis_we < g['left_time']:  # 有可能到达
                        can_pick_num += 1  ##不考虑电量的话，可以到达
                        global remain_need_coefficient  ##匹配无人机和物品时，剩余电量和所需最低电量的比例
                        if uav_we["remain_electricity"] >= electricity_need * remain_need_coefficient:
                            electricity_enough_num += 1
                            # score_uav_goods[str(uav_we['no']) + '_' + str(g['no'])] = 1.0 * g['value'] ** 3 / uav_value / (dis_we + 0.001) * (uav_we["remain_electricity"] / electricity_need)
                            score_uav_goods[str(uav_we['no']) + '_' + str(g['no'])] = 1.0 * g['value'] ** 3 / uav_value / (dis_we + 0.001) ** 0.3
                            # score_uav_goods[str(uav_we['no']) + '_' + str(g['no'])] = 1.0 * g['value']**3 / uav_value / (dis_we + 0.001)**0.5 * (uav_we["remain_electricity"] / electricity_need)**0.5
                            # score_uav_goods[str(uav_we['no']) + '_' + str(g['no'])] = 1.0 * g['value'] ** 3 / uav_value / (dis_we + 0.001) * (uav_we["remain_electricity"] / electricity_need) ** 0.5

            if (uav_we['x'], uav_we['y']) == (we_parking['x'], we_parking['y']) and uav_we['z'] <= h_low:  ##在停机坪没完全升起
                if uav_we["remain_electricity"] < UAV_price_dict[uav_we["type"]]['capacity']:
                    # if (uav_we["no"] == min_uav_no_init or uav_we["type"] == min_value_type) and uav_we['z'] < h_low:
                    #     charged_unlifted_no.add(uav_we["no"])
                    # else:
                    need_charge_no.add(uav_we["no"])
                    if uav_we['z'] > 0 and up_down_flag != 1:
                        up_down_flag = -1
                else:
                    uav_unassigned.add(uav_we["no"])
            elif electricity_enough_num < can_pick_num * enough_pick_proportion:  ##在停机坪外面，有可以拿起的飞机，但是电量只够部分商品的运送
                need_charge_no.add(uav_we["no"])
            else:
                uav_unassigned.add(uav_we["no"])

    return score_uav_goods, uav_unassigned, no_UAV_we_loading, need_charge_no,charged_unlifted_no, up_down_flag


def match_uav_goods(up_down_flag, UAV_we_dict, we_parking, h_low, score_uav_goods,charged_unlifted_no, goods, uav_unassigned):
    goods_unassigned = set()  ## 可拾起的商品是否已被己方某无人机认定
    for g in goods:
        if g['status'] == 0:
            goods_unassigned.add(g['no'])  # 该编号的商品没有被指定

    u_g_str_list = sorted(score_uav_goods, key=lambda x: score_uav_goods[x], reverse=True)  ## 按配对的得分从大到小排序
    match_dict = dict()  ## key为己方无人机编号，value为对应物品编号
    match_no_set = set()  ## 存储已经配对的己方编号
    for u_g_str in u_g_str_list:
        no_uav, no_goods = map(int, u_g_str.split('_'))
        if no_uav in uav_unassigned and no_goods in goods_unassigned:
            uav_unassigned.remove(no_uav)
            goods_unassigned.remove(no_goods)
            match_dict[no_uav] = no_goods

    del_set = set()
    for no_uav in match_dict:  ##看看哪个飞机还在停机坪上空没升到h_low
        if (UAV_we_dict[no_uav]['x'], UAV_we_dict[no_uav]['y']) == (we_parking['x'], we_parking['y']) and UAV_we_dict[no_uav]['z'] < h_low:
            charged_unlifted_no.add(no_uav)
            if UAV_we_dict[no_uav]['z'] > 0 and up_down_flag != -1:  ##不在停机坪，已经在上升
                up_down_flag = 1
            del_set.add(no_uav)
        else:
            match_no_set.add(no_uav)
    for no_uav in del_set:
        del match_dict[no_uav]

    return match_dict, uav_unassigned, goods_unassigned, charged_unlifted_no, match_no_set, up_down_flag


def block_enemy(up_down_flag, match_dict, match_no_set, charged_unlifted_no, need_charge_no, we_parking, enemy_parking,uav_unassigned, UAV_we_dict, UAV_enemy, UAV_price_dict, goods_dict, h_low):
    block_dict = dict()  ##key是己方编号，value是堵口位置
    uav_block_list = list()  ##每个元素都是一个小列表,[uav_we_no,block_x, block_y, block_z,score]
    global enemy_total_value_proportion
    for uav_we_no in uav_unassigned | need_charge_no | charged_unlifted_no | match_no_set:  # 其他已经分配的飞机也可以用来堵
    # for uav_we_no in uav_unassigned | need_charge_no:  # 缺电的飞机也可以用来堵
        x_we, y_we, z_we = UAV_we_dict[uav_we_no]['x'], UAV_we_dict[uav_we_no]['y'], UAV_we_dict[uav_we_no]['z']
        uav_we_value = UAV_price_dict[UAV_we_dict[uav_we_no]['type']]["value"]

        z_max_enemy_parking, value_max_enemy_parking = 0, 0
        for uav_enemy in UAV_enemy:
            x_enemy, y_enemy, z_enemy = uav_enemy['x'], uav_enemy['y'], uav_enemy['z']
            if (x_enemy, y_enemy) == (enemy_parking['x'], enemy_parking['y']) and z_enemy <= h_low:
                if z_enemy > z_max_enemy_parking:
                    z_max_enemy_parking = z_enemy
                enemy_value = UAV_price_dict[uav_enemy['type']]['value']
                if enemy_value > value_max_enemy_parking:
                    value_max_enemy_parking = enemy_value

        for uav_enemy in UAV_enemy:
            block_flag = False  ##True分别代表确定可以堵住，False代表不确定
            enemy_value = UAV_price_dict[uav_enemy['type']]['value']
            if uav_enemy["goods_no"]!=-1:
                enemy_total_value = enemy_value + goods_dict[uav_enemy["goods_no"]]["value"] * enemy_total_value_proportion
            else:
                enemy_total_value = enemy_value
            x_enemy, y_enemy, z_enemy = uav_enemy['x'], uav_enemy['y'], uav_enemy['z']
            # if (x_enemy, y_enemy) == (enemy_parking['x'], enemy_parking['y']) and z_enemy < z_max_enemy_parking:
            if (x_enemy, y_enemy) == (enemy_parking['x'], enemy_parking['y']) and enemy_value < value_max_enemy_parking:
                continue
            block_x, block_y, block_z = x_enemy, y_enemy, h_low  ##要去堵口的位置
            if z_enemy < h_low:
                if (x_we, y_we) == (x_enemy, y_enemy) and z_we > z_enemy:
                    block_z = 0
                    block_flag = True
                else:
                    step_enemy = h_low - z_enemy  ##初始化敌机需要飞行的步数
                    if uav_enemy['goods_no'] == -1:  ##敌机空载
                        for goods_no, goods in goods_dict.items():
                            if goods['status'] == 0 and (goods['start_x'], goods['start_y']) == (x_enemy, y_enemy) and \
                                            goods["weight"] <= UAV_price_dict[uav_enemy['type']]["load_weight"]:  ##敌机要下去拿货
                                step_enemy = z_enemy + h_low  ##敌机先下去拿，后上升到h_low的步数
                                break
                    else:  ##敌机负载
                        if (goods_dict[uav_enemy['goods_no']]['end_x'], goods_dict[uav_enemy['goods_no']]['end_y']) == (x_enemy, y_enemy):  ##敌机要下去放货
                            step_enemy = z_enemy + h_low  ##敌机先下去放，后上升到h_low的步数
            elif uav_enemy['goods_no'] != -1:  ##可以横飞而且有负载
                dis_enemy_end = min_step(x_enemy, y_enemy, z_enemy, goods_dict[uav_enemy['goods_no']]['end_x'],goods_dict[uav_enemy['goods_no']]['end_y'], 0, h_low)
                step_enemy = h_low + dis_enemy_end  ##放下货物后还要上来
                # dis_enemy_end = min_step(x_enemy, y_enemy, z_enemy, goods_dict[uav_enemy['goods_no']]['end_x'],goods_dict[uav_enemy['goods_no']]['end_y'], h_low, h_low)
                # step_enemy = dis_enemy_end  ##不让他下去
                block_x, block_y = goods_dict[uav_enemy['goods_no']]['end_x'], goods_dict[uav_enemy['goods_no']]['end_y']
            else:  ##可以横飞但是空载
                continue
            # if (x_we,y_we)==(block_x, block_y) and z_we <= h_low and step_enemy!=0:
            #     dis = 0
            #     if z_enemy<z_we: ##敌机在下面就冲下去撞，否则block_z保持h_low，堵住敌机的入口，让敌机放不下货物或者找不到路超时犯规
            #         block_z=0
            if not block_flag:
                dis = min_step(x_we, y_we, z_we, block_x, block_y, block_z, h_low)
                if dis <= step_enemy and uav_we_value <= enemy_total_value:
                    if uav_we_no in match_dict:
                        xx, yy, zz = goods_dict[match_dict[uav_we_no]]['start_x'], goods_dict[match_dict[uav_we_no]]['start_y'], 0
                        step_match = min_step(x_we, y_we, z_we, xx, yy, zz, h_low)
                        if step_match < dis:
                            continue
                        else:
                            score = (2.0 - dis / (step_enemy + 0.01)) * (enemy_total_value / uav_we_value) * (2 - dis / (step_match + 0.1))
                    else:
                        score = (2.0 - dis / (step_enemy + 0.01)) * (enemy_total_value / uav_we_value)
                    uav_block_list.append([uav_we_no, block_x, block_y, block_z, score])
            elif uav_we_value <= enemy_total_value:  ##可以堵住而且价值比对方低
                score = 2.0 * enemy_total_value / uav_we_value
                uav_block_list.append([uav_we_no, block_x, block_y, block_z, score])

    uav_block_list.sort(key=lambda x: x[4], reverse=True)

    uav_block_assigned = set()  ##已经指定了的无人机编号
    block_point_assigned = set()  ##已经指定了的堵口位置
    for uav_block in uav_block_list:
        uav_we_no, block_x, block_y, block_z = uav_block[:4]
        if uav_we_no not in uav_block_assigned and (block_x, block_y) not in block_point_assigned:
            uav_block_assigned.add(uav_we_no)
            block_point_assigned.add((block_x, block_y))
            block_dict[uav_we_no] = (block_x, block_y, block_z)
            if uav_we_no in uav_unassigned:  ## uav_unassigned里面的
                uav_unassigned.remove(uav_we_no)
            elif uav_we_no in need_charge_no:  ## need_charge_no里面的
                need_charge_no.remove(uav_we_no)
            elif uav_we_no in charged_unlifted_no:
                charged_unlifted_no.remove(uav_we_no)
            else:  ##match_no_set 里面的
                del match_dict[uav_we_no]

    del_set = set()
    for uav_we_no in block_dict:  ##看看堵敌用的飞机里面哪个飞机还在停机坪上空没升到h_low
        if (UAV_we_dict[uav_we_no]['x'], UAV_we_dict[uav_we_no]['y']) == (we_parking['x'], we_parking['y']) and UAV_we_dict[uav_we_no]['z'] < h_low:
            charged_unlifted_no.add(uav_we_no)
            if UAV_we_dict[uav_we_no]['z'] > 0 and up_down_flag != -1:
                up_down_flag = 1
            del_set.add(uav_we_no)
    for uav_we_no in del_set:
        del block_dict[uav_we_no]

    remove_set = set()
    for uav_we_no in uav_unassigned:  ##看看未指定的里面哪个飞机还在停机坪上空没升到h_low
        if (UAV_we_dict[uav_we_no]['x'], UAV_we_dict[uav_we_no]['y']) == (we_parking['x'], we_parking['y']) and UAV_we_dict[uav_we_no]['z'] < h_low:
            if UAV_we_dict[uav_we_no]["remain_electricity"] == UAV_price_dict[UAV_we_dict[uav_we_no]['type']]["capacity"]:
                charged_unlifted_no.add(uav_we_no)
                if UAV_we_dict[uav_we_no]['z'] > 0 and up_down_flag != -1:
                    up_down_flag = 1
                remove_set.add(uav_we_no)
            elif up_down_flag != 1:
                need_charge_no.add(uav_we_no)
                if UAV_we_dict[uav_we_no]['z'] > 0:
                    up_down_flag = -1
                remove_set.add(uav_we_no)
    for uav_we_no in remove_set:
        uav_unassigned.remove(uav_we_no)

    return uav_unassigned, block_dict, charged_unlifted_no, need_charge_no, match_dict, up_down_flag


def clear_enemy_block(no_UAV_we_loading,uav_unassigned,goods_dict,UAV_price_dict,UAV_we_dict,UAV_enemy,UAV_enemy_dict,h_low):
    enemy_block_set = set()
    score_clear = dict()
    for no_uav_we,goods_no_flag in no_UAV_we_loading.items():
        goods_no = goods_no_flag[0]
        uav_we = UAV_we_dict[no_uav_we]
        for uav_enemy in UAV_enemy:
            if (uav_enemy['x'], uav_enemy['y']) == (goods_dict[goods_no]['end_x'], goods_dict[goods_no]['end_y']) and uav_enemy['z']<=h_low:
                if uav_we['x'] is goods_dict[goods_no]['end_x'] and uav_we['y'] is goods_dict[goods_no]['end_y'] and uav_we['z']<uav_enemy['z']:
                    continue
                else:
                    enemy_block_set.add((uav_enemy["no"],no_uav_we,goods_no,uav_enemy['x'],uav_enemy['y'],uav_enemy['z']))
    no_enemy_dict = dict() ##堵我们的敌机
    for enemy_block in enemy_block_set:
        no_uav_enemy,no_uav_we_blocked,goods_no,enemy_x,enemy_y,enemy_z = enemy_block
        no_enemy_dict[no_uav_enemy] = (enemy_x,enemy_y,enemy_z)
        type_enemy = UAV_enemy_dict[no_uav_enemy]['type']
        uav_we_blocked = UAV_we_dict[no_uav_we_blocked]
        type_we_blocked = uav_we_blocked['type'] ##被堵的己方型号

        ## 我方被堵的运货飞机到达目的地最少步数
        # min_step_need = min_step(uav_we_blocked['x'], uav_we_blocked['y'], uav_we_blocked['z'], enemy_x,enemy_y,0, h_low)
        ## 留给己方小飞机赶过来清理敌机的步数上限。
        step_max_unassigned = uav_we_blocked["remain_electricity"] / goods_dict[goods_no]["weight"] - enemy_z -2


        for no_uav_unassigned in uav_unassigned:
            we_unassigned = UAV_we_dict[no_uav_unassigned]
            type_we_unassigned = we_unassigned['type'] ##未指定的己方编号
            ## 我方小飞机赶过来清理敌机需要的最短步数
            min_step_clear = min_step(we_unassigned['x'], we_unassigned['y'], we_unassigned['z'], enemy_x,enemy_y,enemy_z, h_low)
            if min_step_clear < step_max_unassigned and UAV_price_dict[type_we_unassigned] <= UAV_price_dict[type_enemy]:
                score = (2.0-min_step_clear/step_max_unassigned)*UAV_price_dict[type_enemy]["value"]/UAV_price_dict[type_we_unassigned]["value"]
                score_clear[(no_uav_unassigned,no_uav_enemy,no_uav_we_blocked)] = score

    score_clear = sorted(score_clear,key=lambda x:-score_clear[x])
    max_num_clear = min(len(uav_unassigned),len(no_enemy_dict)) ##最多可匹配几个清道夫
    num_clear = 0 ##匹配清道夫个数
    if max_num_clear:
        # num_clear = max_num_clear/2+1  ##不要匹配所有的，分低的略过
        num_clear = max_num_clear
    clear_match_dict = dict() ##存储最终的匹配,己方飞机和对应要去的敌机位置，例： 4:(20,35,15)
    for we_enemy in score_clear:
        no_we,no_enemy,no_uav_we_blocked = we_enemy
        if no_we in uav_unassigned and no_enemy in no_enemy_dict:
            clear_match_dict[no_we] = no_enemy_dict[no_enemy]
            uav_unassigned.remove(no_we)
            del no_enemy_dict[no_enemy]
            no_UAV_we_loading[no_uav_we_blocked][1]=True
            num_clear -= 1
            if num_clear<=0:
                break

    return clear_match_dict,uav_unassigned,no_UAV_we_loading


def no_cross_border(x, y, z, range_x, range_y, h_high):
    if x < 0:
        x = 0
    if x >= range_x:
        x = range_x - 1
    if y < 0:
        y = 0
    if y >= range_y:
        y = range_y - 1
    if z < 0:
        z = 0
    if z > h_high:
        z = h_high
    return x, y, z