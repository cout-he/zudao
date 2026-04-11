import copy
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import itertools
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.patches as patches
import matplotlib.font_manager as fm
from openpyxl import load_workbook

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT_DIR / "data" / "产品数据.xlsx"
RESULT_FIGURE = ROOT_DIR / "outputs" / "result.png"
# 图片显示中文
plt.rcParams['font.sans-serif'] = ['SimHei']  # 字体设置
plt.rcParams['axes.unicode_minus'] = False  # 减号unicode编码

class Node(object):
#子节点类型，构造树#
    def __init__(self,value = None):
        self.layer_num=None
        self.combination=value
        self.child_list=[]
        self.brother_combinations=[]
        self.parent=None
        self.demand_information=[]
        self.used_L=0
    def add_parent(self,node):
        self.parent=node
class item(object):
    def __init__(self,demand):
        self.panel_width=1250
        self.panel_weight=7970
        self.plan_good=[]
        self.length_good=np.inf
        self.l_good_vec=[]
        self.plan_tmp=[]
        self.length_tmp=[]
        self.combination_tmp=[]
        self.combination_good=[]
##————————————##
        self.demand_information = demand
        '''ok1
        {
            'Width': [130, 500, 547],
            'Length': [445, 833,291],
            'num': [1000, 1000, 1000],
            'Weight': [544.947,3923.43,1500]
                    }
        '''
        '''
        #ok2
        self.demand_information = {
            'Width': [130, 500, 547],
            'Length': [445, 833, 582],
            'num': [1000, 1000, 500],
            'Weight': [544.947, 3923.43, 1500]
        }
        '''
        self.demand_information=pd.DataFrame(self.demand_information)
        self.demand_information=copy.deepcopy(self.demand_information)
    def rules_generation(self,demand_information):
        item_num = len(demand_information)
        max_num = (np.floor(self.panel_width / np.array(demand_information['Width'])).astype(np.int_) *
                   ~(demand_information['num'].eq(0)))  # 对应的每个type最多能放的数量
        max_num = np.array(max_num)
        # item_num = (max_num!=0).sum()
        # 定义每个位置的可能选择
        choices_for_position = []
        for i in range(item_num):
            choices_for_position.append(range(max_num[i] + 1))
        # 使用 itertools.product 生成所有可能的组合
        combinations = list(itertools.product(*choices_for_position))
        return combinations

    def cut_rules(self,demand_information,combination):
        cut_plan = list()
        # 排长度
        length_num=np.ceil(np.array(demand_information['num'])/np.array(combination))##每一种板按该组合需要排满的个数
        length=np.array(demand_information['Length'])*length_num##对应的长度
        #length = np.array(demand_information['Length'] * demand_information['num']) / np.array(combination)
        # 取最小的长度横切
        cut_length = np.min(length[~np.isnan(length)])
        cut_index = list(length).index(cut_length)
        cut_finished = np.array(np.floor(cut_length / demand_information['Length']).astype(np.int_) * np.array(
            combination))  # 相当于完成了最短的订单，计算没完成的订单剩余需求
        cut_finished[cut_index]=demand_information['num'][cut_index]
        # 记录切割方式和损耗
        cut_plan.extend(cut_finished)
        # 更新demand
        for index in range(len(cut_finished)):
            demand_information.loc[index, 'num'] -= cut_finished[index]
        return demand_information, cut_plan,cut_length
def result_plot(item):
    width = item.panel_width
    Length = sum(item.l_good_vec)  # 四个参数控制矩形
    # 设置画布大小为10x6英寸
    plt.figure(figsize=(10, 6))

    figure_x=200
    figure_y=100

    scaler_x=figure_x/Length
    scaler_y = figure_y/width

    result_x=[]
    result_y=[]
    result_id=[]
    result_num = []
    values=[]#面积
    sizes=np.array((item.demand_information['Width']*scaler_x)*(item.demand_information['Length']*scaler_y))
    h = []
    for step in range(len(item.plan_good)):
        plan=item.plan_good[step]
        length=np.array((item.demand_information['Length']*scaler_x)*plan)
        w1=[]
        h1=[]
        id=[]
        num=[]
        for i in range(len(item.combination_good[step])):
            depart=item.combination_good[step][i]
            for j in range(depart):
                w1.append(length[i] / depart)
                h1.append(item.demand_information['Width'][i] * scaler_y)#宽不变
                id.append(i)
                num.append(int(plan[i] /depart))
        h.append(h1)
        result_x.append(w1)
        result_y.append([0]+list(itertools.accumulate(h[step])))
        result_id.append(id)
        result_num.append(num)
        values.append(sizes * np.array(plan))

    rects=[]
    xlim=0
    ylim=0
    for i in range(len(result_x)):
        for num in range(len(result_x[i])):
            loc = {}
            loc['id']=result_id[i][num]
            loc['num'] = result_num[i][num]
            loc['x'] = 0+sum(max(sublist) for sublist in result_x[:i])
            loc['y'] = result_y[i][num]
            loc['dx'] =result_x[i][num]
            loc['dy'] =h[i][num]
            rects.append(loc)
            if loc['x']+loc['dx']>xlim:
                xlim=loc['x']+loc['dx']
            if loc['y']+loc['dy']>ylim:
                ylim = loc['y']+loc['dy']

    labels=range(len(rects))
    colors = [plt.cm.Spectral(i / float(len(labels))) for i in range(len(labels))]

    # 用来正常显示中文标签
    plt.rcParams['font.sans-serif'] = ['SimHei']

    sheet = plt.Rectangle((0, 0), figure_x, figure_y*Length/width, fc='lightgray', ec="black")
    plt.gca().add_patch(sheet)
    for rect in rects:
        rectangle = plt.Rectangle((rect['x'], rect['y']), (rect['dx']), (rect['dy']), fc='royalblue', ec="red")
        plt.gca().add_patch(rectangle)
        plt.text(
                    rect['x'] +rect['dx'] / 2,  # rect的水平中心
                    rect['y'] + rect['dy'] / 2,  # rect的垂直中心
                    s='item:{}\n num:{}'.format(rect['id']+1,rect['num']),
                    ha="center",  # 居中
                    va="center",  # 居中
                    multialignment="center",  # 居中
                    color='white',
                    fontsize=10,
                )
        # 显示宽度的文本标签在矩形的底部中间位置
        plt.text(
            rect['x'] + rect['dx'] / 2,  # 矩形底部的水平中心
            rect['y'] ,  # 矩形底部往上5个像素的位置
            s='长度: {}'.format(int(rect['dx']/scaler_x)),  # 格式化显示宽度
            ha="center",  # 水平居中
            va="top",  # 垂直顶部对齐
            color='black',  # 文本颜色
            fontsize=8,
            rotation=0  # 旋转文本45度，使其竖直显示
        )

        # 显示长度的文本标签在矩形的左侧中间位置
        plt.text(
            rect['x'],  # 矩形左侧向右5个像素的位置
            rect['y'] + rect['dy'] / 2,  # 矩形的垂直中心
            s='宽度: {}'.format(int(rect['dy']/scaler_y)),  # 格式化显示长度
            ha="right",  # 水平右对齐
            va="center",  # 垂直居中对齐
            color='black',  # 文本颜色
            rotation='vertical',
            fontsize=8
        )
    # 设置坐标轴范围
    plt.xlim(0, xlim+1 )  # 设置x轴范围为[2, 8]
    plt.ylim(0, ylim+1)  # 设置y轴范围为[-1, 1]

    plt.title('面积利用率:{:.2f}%'.format(eff), fontsize=12)
    plt.axis('off')  # 不显示坐标框
    plt.savefig(RESULT_FIGURE)
    plt.show()

def get_para():
    wb = load_workbook(DATA_FILE, data_only=True)
    # 选择活动的工作表
    sheetname = int(input("请输入产品数据表: "))
    ws = wb['Sheet%d'%sheetname]
    item_num = ws['B1'].value
    if item_num <= 0:
        sys.exit("产品种类数量输入不正确")
    width_list = list()
    length_list = list()
    num_list = list()
    weight_list = list()
    for i in range(item_num):
        width = ws['A%d'%(i+3)].value
        if width <= 0:
            sys.exit("产品宽度输入不正确")
        length = ws['B%d'%(i+3)].value
        if length <= 0:
            sys.exit("产品长度输入不正确")
        num = ws['C%d'%(i+3)].value
        if num <= 0:
            sys.exit("产品数量输入不正确")
        weight = ws['D%d'%(i+3)].value
        if weight <= 0:
            sys.exit("产品重量输入不正确")
        width_list.append(width)
        length_list.append(length)
        num_list.append(num)
        weight_list.append(weight)
    demand_information = {
        'Width': width_list,
        'Length': length_list,
        'num': num_list,
        'Weight': weight_list
    }
    return demand_information


    '''
    item_num = int(input("请输入产品种类个数: "))
    if item_num<=0:
        sys.exit("产品种类数量输入不正确")
    width_list=list()
    length_list=list()
    num_list=list()
    weight_list=list()
    for i in range(item_num):

        width=float(input("请输入第%d种产品的宽度: "%(i+1)))
        if width<=0:
            sys.exit("产品宽度输入不正确")
        length=float(input("请输入第%d种产品的长度: "%(i+1)))
        if length<=0:
            sys.exit("产品长度输入不正确")
        num=int(input("请输入第%d种产品的数量: "%(i+1)))
        if num<=0:
            sys.exit("产品数量输入不正确")
        weight=float(input("请输入第%d种产品的重量: "%(i+1)))
        if weight<=0:
            sys.exit("产品重量输入不正确")
        width_list.append(width)
        length_list.append(length)
        num_list.append(num)
        weight_list.append(weight)
    demand_information = {
        'Width': width_list,
        'Length': length_list,
        'num': num_list,
        'Weight': weight_list
    }
    return demand_information
    '''
if __name__ == '__main__':

    #初始信息
    demand=get_para()
    #初始化#
    item=item(demand)
    root=Node()
    root.demand_information=item.demand_information
    root.layer_num=0
    combinations=item.rules_generation(item.demand_information)
    for i in range(len(combinations)):
        c = combinations[i]
        total_width = (item.demand_information['Width'] * list(c)).sum()
        # 判断是否满足宽度需求 以及 防止浪费过多限制
        if ((total_width < item.panel_width and item.panel_width - total_width < item.demand_information['Width'].min())):
            root.child_list.append(c)
    node_now=root

    while (node_now.parent!=None or len(node_now.child_list)!=0):
        if len(node_now.child_list)==0:
            node_now=node_now.parent
            node_now.child_list.pop(0)
            item.plan_tmp.pop()
            item.length_tmp.pop()
            item.combination_tmp.pop()
            continue
        ##计算下一层方案并更新##
        combination=node_now.child_list[0]
        node_nxt=Node(combination)#孩子结点
        node_nxt.layer_num=node_now.layer_num+1
        node_nxt.parent=node_now
        ##update_demand_information为下一层切割需求，cut_plan为当前层切割方案，cut_length为当前层切割长度##
        demand_information_nxt, cut_plan, cut_length = item.cut_rules(copy.deepcopy(node_now.demand_information),combination)
        node_nxt.used_L=node_now.used_L+cut_length
        node_nxt.demand_information=demand_information_nxt
        item.plan_tmp.append(cut_plan)
        item.combination_tmp.append(combination)
        item.length_tmp.append(node_nxt.used_L)
        ##——————————————————##
        ##判断下一层是否为叶子节点##
        if node_nxt.demand_information['num'].sum() != 0:
            #不是叶子结点#
            ##获取该节点的所有可行组合##
            combinations = item.rules_generation(node_nxt.demand_information)
            for i in range(len(combinations)):
                c = combinations[i]
                total_width = (node_nxt.demand_information['Width'] * list(c)).sum()
                # 判断是否满足宽度需求 以及 防止浪费过多限制
                index_ok=node_nxt.demand_information['num'][node_nxt.demand_information['num']>0].index
                if ((total_width < item.panel_width and item.panel_width - total_width < node_nxt.demand_information[
                    'Width'][index_ok].min())):
                    node_nxt.child_list.append(c)
            ##------------------##
            node_now=node_nxt#更新node，进入下一层
        else:
            #是叶子结点#
            if item.length_tmp[-1]<item.length_good:
                item.length_good=item.length_tmp[-1]
                item.l_good_vec=copy.deepcopy(item.length_tmp)
                item.plan_good=copy.deepcopy(item.plan_tmp)
                item.combination_good=copy.deepcopy(item.combination_tmp)
            item.length_tmp.pop()
            item.plan_tmp.pop()
            item.combination_tmp.pop()
            node_now.child_list.pop(0)
        ##———————————————————##
    global eff
    eff=100*(item.demand_information['Width']*item.demand_information['Length']*item.demand_information['num']).sum()/(item.panel_width*item.length_good)
    print('已切割长度')
    print(item.l_good_vec)
    print('切割组合')
    print(item.plan_good)
    print('切割效率为%f %%'%eff)
    print("ok")
    result_plot(item)





























'''
        for i in range(1,len(combinations[-1])):

            c = combinations[i]
            total_width = (item.demand_information['Width'] * list(c)).sum()
            max_num = np.sum(np.ones(3) * ~item.demand_information['num'].eq(0))
            # 判断是否满足宽度需求 以及 防止浪费过多限制
            if ((total_width < panel_width and panel_width - total_width <item.demand_information['Width'].min() and max_num > 1)
                    or (total_width < panel_width and max_num == 1)):
##更新当前层combinations，并引入item下一层##
                item
                item.combinations[-1]=combinations[i+1:]
                item.current=Node(c)
                root=item.upper
                root.add_child(item.current)
##——————————————————————————————————##

                # if item.upper!=None:
                #     item.All_plan[item.upper] = item.current
                # else:
                #     item.All_plan[item.current] = {}
##update_demand_information为下一层切割需求，cut_plan为当前层切割方案，cut_length为当前层切割长度##
                update_demand_information,cut_plan,cut_length=item.cut_rules(item.demand_information)
                plan_tmp.append[cut_plan]
                if update_demand_information['num'].sum() != 0:#未完成,二叉树继续向下
                    item.upper=item.current
                    item.current = None
##更新下一层combinations##
                    combinations[-1].append(item.rules_generation(update_demand_information))
##———————————————————##
                    break
                else:#完成，向右
                    item.upper = Node(c)
                    item.current = None
                    combinations = item.rules_generation(update_demand_information)








    # 使用字典创建DataFrame
    item_infomation = pd.DataFrame(data)
    demand_infomation=copy.deepcopy(item_infomation)

    # #信息补全
    # indices_with_none = list(item_infomation[item_infomation.isnull().any(axis=1)].index)
    # columns_with_none = item_infomation.isna().any(axis=0)
    # columns_with_none_names = list(item_infomation.columns[columns_with_none])
    # for index in indices_with_none:
    #     weight=item_infomation['Width'][index]/panel_width*panel_weight
    #     length=item_infomation['Weight'][index]/weight


    combinations=rules_generation(demand_infomation)
    # max_num = np.sum(np.ones(3) * ~demand_infomation['num'].eq(0))
    All_plan=[]
    i=1
    j=1
    while i<len(combinations):
        c = combinations[i]
        total_width = (demand_infomation['Width'] * list(c)).sum()
        max_num = np.sum(np.ones(3) * ~demand_infomation['num'].eq(0))
        # 判断是否满足宽度需求 以及 防止浪费过多限制
        if (total_width < panel_width and panel_width - total_width < demand_infomation[
            'Width'].min() and max_num > 1) or (total_width < panel_width and max_num == 1):
            plans=[]
            if demand_infomation['num'].sum() != 0:#还存在订单未完成
                demand_infomation,plan=cut_rules(demand_infomation)
                plans.append(plan)
                combinations = rules_generation(demand_infomation)
                i=j
                All_plan.append(plans)
                if len(combinations)==1:
                    demand_infomation = copy.deepcopy(item_infomation)
                    combinations = rules_generation(demand_infomation)
                    i+=1
                print(1)
        else:
            i+=1
'''
#1、combinations出错，item只有一个对象，只能存储一个combinations，而下一层的新的combinations将上一层的combinations覆盖掉了
#解决方法：combinations保存到结点上去，并为节点增加父亲节点
#2、没有保存方案的比较解，没有对方案进行取舍
#解决方案：使用plan_good存当前最优的排刀方案，length_good存当前最优方案的使用长度
#3、demand_information与1类似，将demand_information保存到节点上
