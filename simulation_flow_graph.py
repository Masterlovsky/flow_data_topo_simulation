#! /usr/bin/python3
# -*- encoding:utf-8 -*-
import os

from deprecated import deprecated
from tqdm import tqdm

from pyecharts import options as opts
from pyecharts.globals import ThemeType
from pyecharts.charts import Graph
from pyecharts.render import make_snapshot
import numpy as np
import json
import logging

# Logger object
logger = logging.getLogger("main")
# set default logging level to INFO
logger.setLevel(logging.INFO)
# set logging format
formatter = logging.Formatter("[%(asctime)s]-[%(name)s]-[%(levelname)s] : %(message)s")
# set logging handler
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)


def g_make(nodes, links, categories, layout, title) -> Graph:
    c = (
        Graph(
            opts.InitOpts(
                width="1600px", height="950px",
                page_title="FlowGraph",
                theme=ThemeType.WHITE,
                js_host="./js/",
                chart_id="1a53dbfa024e4c22b72f77a579c0c63b",
                animation_opts=opts.AnimationOpts()
            )
        )
        .add(
            "",
            nodes,
            links,
            categories=categories,
            repulsion=300,
            is_draggable=True,
            layout=layout,
            tooltip_opts=opts.TooltipOpts(formatter="ID:{b}, Load:{c}"),
            # itemstyle_opts=opts.ItemStyleOpts(color="rgb(230,73,74)", border_color="rgb(255,148,149)", border_width=3)
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(title=title, subtitle="Link unit: " + TRAFFIC_UNIT_PRINT),
            legend_opts=opts.LegendOpts(legend_icon="circle"),
            toolbox_opts=opts.ToolboxOpts(is_show=True, orient="vertical", pos_left="right",
                                          feature=opts.ToolBoxFeatureOpts(
                                              data_view=opts.ToolBoxFeatureDataViewOpts(),
                                              magic_type={"is_show": False},
                                              data_zoom=opts.ToolBoxFeatureDataZoomOpts(is_show=False))
                                          ),
        )
    )
    return c


def load_flow_data(file: str):
    logger.info("Loading flow data from file: {}".format(file))
    flow_arr = np.loadtxt(file, delimiter=" ").astype(np.float64)
    return flow_arr


def load_topology_data(file: str):
    logger.info("Loading topology data from file: {}".format(file))
    topo_arr = np.loadtxt(file, skiprows=1).astype(int)
    return topo_arr


def load_type_data(file: str) -> dict:
    logger.info("Loading node type data from file: {}".format(file))
    nodes_type_dict = {}
    with open(file, 'r') as f:
        lines_list = f.readlines()
    if len(lines_list) != 4:
        raise ValueError("wrong format in node_type.txt file!")
    else:
        for index, line in enumerate(lines_list):
            line = line.split(":")[1]
            nodes_list = line.strip("[ ]\n").split(", ")
            for node in nodes_list:
                nodes_type_dict[node] = index + 1
    return nodes_type_dict


def load_axis_to_dict(file: str) -> dict:
    logger.info("Loading node axis data from file: {}".format(file))
    node_axis_dict = {}
    _x = None
    _y = None
    with open(file, 'r') as f:
        lines_list = f.readlines()
    for index, line in enumerate(lines_list):
        nodes_list = line.strip().split(",")
        if len(nodes_list) not in (4, 5):
            if index == 0:
                print("Warning, wrong format in node_axis.txt file!")
            continue
        _x, _y, _ctrl = float(nodes_list[1]), float(nodes_list[2]), int(nodes_list[-1])
        node_axis_dict[nodes_list[0]] = (_x, _y, _ctrl)
    return node_axis_dict


def sieve_flow_data(flow_old_file, flow_new_file):
    res_list = []
    with open(flow_old_file, 'r') as f_old:
        data_set = set(f_old.read().splitlines())
    with open(flow_new_file, 'r') as f_new:
        for line in f_new.read().splitlines():
            if line in data_set:
                continue
            res_list.append([int(i) for i in line.split(" ")])
    return np.array(res_list)


def dataHandler(flow_arr: np.ndarray, flow_new_arr: np.ndarray, topo_arr: np.ndarray):
    """
    根据节点流数据和节点拓扑文件生成最终数据表
    数据表共8列数据，的格式为：
    [Node1 Node2 Community1 Category2 load_val1 load_val2 link_val flag]
    flag: {0: 普通记录, 1: flow_data记录, 2: flow_data_new记录}
    :param flow_new_arr:
    :param flow_arr: 节点的流数组
    :param topo_arr: 节点拓扑数组
    :return:  整合之后的数组
    """
    logger.info("Data handler start...")
    topo_arr = np.hstack((topo_arr, np.zeros((len(topo_arr), 4), dtype=int)))
    # 使用flow_arr中的每一行更新topo_arr
    for flow_line in tqdm(flow_arr, desc="update flow_arr: "):
        for topo_line in topo_arr:
            if flow_line[0] == topo_line[0]:
                topo_line[4] = flow_line[2]
            if flow_line[1] == topo_line[1]:
                topo_line[5] = flow_line[3]
            if flow_line[0] == topo_line[0] and flow_line[1] == topo_line[1]:
                topo_line[6] = flow_line[4]
                topo_line[7] = 1
            if flow_line[0] == topo_line[1]:
                topo_line[5] = flow_line[2]
            if flow_line[1] == topo_line[0]:
                topo_line[4] = flow_line[3]
            if flow_line[0] == topo_line[1] and flow_line[1] == topo_line[0]:
                topo_line[6] = flow_line[4]
                topo_line[7] = 1

    # 使用flow_new_arr中的每一行更新topo_arr
    for flow_line in tqdm(flow_new_arr, desc="update flow_new_arr: "):
        for topo_line in topo_arr:
            if flow_line[0] == topo_line[0]:
                topo_line[4] = flow_line[2]
            if flow_line[1] == topo_line[1]:
                topo_line[5] = flow_line[3]
            if flow_line[0] == topo_line[0] and flow_line[1] == topo_line[1]:
                topo_line[6] = flow_line[4]
                topo_line[7] = 2
            if flow_line[0] == topo_line[1]:
                topo_line[5] = flow_line[2]
            if flow_line[1] == topo_line[0]:
                topo_line[4] = flow_line[3]
            if flow_line[0] == topo_line[1] and flow_line[1] == topo_line[0]:
                topo_line[6] = flow_line[4]
                topo_line[7] = 2

    return topo_arr


@deprecated(reason="This method is deprecated.")
def manual_set_node(key: str) -> tuple:
    if str(key) == "0":
        _is_fixed = True
        _x = 450
        _y = 100
    elif str(key) == "1":
        _is_fixed = True
        _x = 500
        _y = 300
    elif str(key) == "3":
        _is_fixed = True
        _x = 650
        _y = 300
    elif str(key) == "4":
        _is_fixed = True
        _x = 680
        _y = 376
    elif str(key) == "6":
        _is_fixed = True
        _x = 600
        _y = 100
    elif str(key) == "7":
        _is_fixed = True
        _x = 800
        _y = 300
    elif str(key) == "38":
        _is_fixed = True
        _x = 1000
        _y = 276
    elif str(key) == "40":
        _is_fixed = True
        _x = 900
        _y = 376
    elif str(key) == "44":
        _is_fixed = True
        _x = 1070
        _y = 376
    elif str(key) == "20":
        _is_fixed = True
        _x = 450
        _y = 636
    elif str(key) == "27":
        _is_fixed = True
        _x = 450
        _y = 536
    elif str(key) == "26":
        _is_fixed = True
        _x = 520
        _y = 470
    elif str(key) == "24":
        _is_fixed = True
        _x = 650
        _y = 536
    elif str(key) == "25":
        _is_fixed = True
        _x = 547
        _y = 670
    elif str(key) == "11":
        _is_fixed = True
        _x = 650
        _y = 893
    elif str(key) == "8":
        _is_fixed = True
        _x = 900
        _y = 893
    elif str(key) == "17":
        _is_fixed = True
        _x = 1150
        _y = 893
    elif str(key) == "9":
        _is_fixed = True
        _x = 750
        _y = 806
    elif str(key) == "15":
        _is_fixed = True
        _x = 1050
        _y = 806
    elif str(key) == "16":
        _is_fixed = True
        _x = 900
        _y = 750
    elif str(key) == "76":
        _is_fixed = True
        _x = 900
        _y = 636
    elif str(key) == "66":
        _is_fixed = True
        _x = 1237
        _y = 614
    elif str(key) == "57":
        _is_fixed = True
        _x = 1220
        _y = 582
    else:
        _is_fixed = False
        _x = None
        _y = None
    return _is_fixed, _x, _y


def get_node_num(nodes: dict) -> None:
    """
    获取每个社区的节点数目并输出在console中
    :param nodes: 节点字典，格式为：{NodeID: (val, Category, type)}
    """
    num_dict = {}
    for node, item in nodes.items():
        category = int(item[1])
        num_dict[category] = num_dict.setdefault(category, 0) + 1
    print("{ 社区编号: 节点数 }")
    print(json.dumps(num_dict, sort_keys=True, indent=4))


def run(layout: str = "force", title="Simulation_Flow_Graph", showlabel=True) -> Graph:
    """
    主函数，按照需求生成所有节点和边，并渲染输出
    :param title: 生成html文件的标题
    :param layout: 共三种方式，"force","manual","file"
    :param showlabel: 是否显示节点标签
    :return: Graph 对象
    "force"   是力引导模型，用于调试，可以拖动;
    "manual"  可以初始化时确定部分点的坐标，坐标在 manual_set_node() 中确定;
    "file"    从layout文件中读取坐标"
    """
    # if flow_data file or flow_data_new file is not exist, create it
    if not os.path.exists(flow_data_file):
        with open(flow_data_file, "w") as f:
            f.write("")
    if not os.path.exists(flow_data_new_file):
        with open(flow_data_new_file, "w") as f:
            f.write("")

    flow_data = load_flow_data(flow_data_file)
    flow_data_n = sieve_flow_data(flow_data_file, flow_data_new_file)
    topo_data = load_topology_data(topo_file)
    type_data = load_type_data(node_type_file)
    layout_data = load_axis_to_dict(layout_file)
    all_data = dataHandler(flow_data, flow_data_n, topo_data)
    nodes_data = []
    links_data = []
    category_data = []
    nodes = {}  # 存放所有节点的集合
    symbol_list = ["circle", "roundRect", "rect", "triangle", "diamond"]  # 分别代表router, receiver，source，switch，bgn
    labels_tuple = ("RCV", "SRC", "SW", "BGN")
    # ! 创建节点 ======================================================================
    max_val = 0
    for line in all_data:
        startNode, endNode, s_cat, e_cat, s_val, e_val = line[:6]
        nodes[startNode] = (s_val, s_cat, type_data.get(str(startNode), 0))
        nodes[endNode] = (e_val, e_cat, type_data.get(str(endNode), 0))
        max_val = max(max_val, s_val, e_val)
    # print(nodes.keys())
    for key in tqdm(nodes.keys(), desc="Creating Nodes: "):
        _name = str(key)
        _ctrl = 0  # 标记属于哪个控制域
        # _symbol_size 控制在一倍的NODE_NORMAL_SIZE - 两倍的NODE_NORMAL_SIZE之间
        _symbol_size = NODE_NORMAL_SIZE + nodes[key][0] / max_val * NODE_NORMAL_SIZE * 0.8
        # 对特殊节点进行单独标识 -----------------------------------------------------
        if nodes[key][2] > 0:
            _symbol_size = _symbol_size * 1.2
            _label_formatter = labels_tuple[nodes[key][2] - 1] + ":{b}"
            _formatter = labels_tuple[nodes[key][2] - 1] + ":{b}, load,ctrl:{c} "
            # _item_style_opts = opts.ItemStyleOpts(border_width=2, border_color="red")
            _item_style_opts = None
            _label_opts = opts.LabelOpts(is_show=showlabel, position="bottom", font_size=14, font_weight="bold",
                                         formatter=_label_formatter)
            _tooltip_opts = opts.TooltipOpts(trigger="item", formatter=_formatter)
        # 普通节点标识 --------------------------------------------------------------
        else:
            _formatter = "ID:{b}, load, ctrl = {c}"
            _label_opts = opts.LabelOpts(is_show=showlabel, position="bottom", font_size=12, font_weight="normal")
            _item_style_opts = None
            _tooltip_opts = opts.TooltipOpts(formatter=_formatter)
        # 添加节点
        if layout == "file":
            _x, _y, _ctrl = layout_data[str(key)]
            _is_fixed = True
        elif layout == "manual":
            _is_fixed, _x, _y = manual_set_node(key)
        else:
            _x, _y, _ctrl = layout_data.get(str(key), (None, None, 0))
            _is_fixed = False
        nodes_data.append(
            opts.GraphNode(name=_name,
                           x=_x, y=_y, is_fixed=_is_fixed,
                           symbol=str(symbol_list[nodes[key][2]]),
                           # symbol="image://pics/acc-sw.svg",
                           symbol_size=_symbol_size,
                           value=[str(round(nodes[key][0] / TRAFFIC_UNIT, 2)), _ctrl],
                           category=int(nodes[key][1] - 1),
                           label_opts=_label_opts,
                           tooltip_opts=_tooltip_opts,
                           itemstyle_opts=_item_style_opts  # 如果没改源码需要把这行注释掉！
                           )
        )
    # ! 创建边 ========================================================================
    max_line_val = 0
    for line in tqdm(all_data, desc="Creating Links: "):
        startNode, endNode, s_cat, e_cat, s_val, e_val, link_val, flag = line
        max_line_val = max(max_line_val, link_val)
        # color_r = str(150 - link_val)
        # color = "rgb(" + color_r + "," + color_r + "," + color_r + ")"
        if flag == 0:
            links_data.append(
                opts.GraphLink(source=str(startNode), target=str(endNode), value=round(link_val / TRAFFIC_UNIT, 2),
                               linestyle_opts=opts.LineStyleOpts(width=1.0)
                               )
            )
        elif flag == 1:
            links_data.append(
                opts.GraphLink(source=str(startNode),
                               target=str(endNode),
                               value=round(link_val / TRAFFIC_UNIT, 2),
                               symbol=["none", "none"],
                               symbol_size=10 + int(link_val / TRAFFIC_UNIT),
                               linestyle_opts=opts.LineStyleOpts(width=2 + link_val / max_line_val * 6,
                                                                 type_="solid",
                                                                 color="#495057",
                                                                 opacity=0.8),
                               label_opts=opts.LabelOpts(is_show=True, position="middle",
                                                         formatter="{c}",
                                                         distance=1,
                                                         horizontal_align="center"),

                               )
            )
        elif flag == 2:
            links_data.append(
                opts.GraphLink(source=str(startNode),
                               target=str(endNode),
                               value=int(link_val),
                               symbol=["none", "none"],
                               symbol_size=10 + int(link_val / TRAFFIC_UNIT),
                               linestyle_opts=opts.LineStyleOpts(width=2 + link_val / max_line_val * 6, type_="solid",
                                                                 color="green"),
                               label_opts=opts.LabelOpts(is_show=True, position="middle",
                                                         formatter="{c}",
                                                         distance=1,
                                                         horizontal_align="center"
                                                         )
                               )
            )
    # ! 创建类别 ========================================================================
    category_set = set(list(all_data[:, 2]) + list(all_data[:, 3]))
    for cate in category_set:
        category_data.append(
            opts.GraphCategory(name="AS:" + str(cate))
        )
    # ! 生成关系图 =======================================================================
    graph_ = g_make(nodes_data, links_data, category_data, layout, title)
    logger.info("Graph Created!")

    # 增加鼠标拖动点固定位置的js代码
    graph_.add_js_funcs(
        '''
            chart_1a53dbfa024e4c22b72f77a579c0c63b.on('mouseup',
            function(params){
                var option=chart_1a53dbfa024e4c22b72f77a579c0c63b.getOption();
                option.series[0].data[params.dataIndex].x=params.event.offsetX;
                option.series[0].data[params.dataIndex].y=params.event.offsetY;
                option.series[0].data[params.dataIndex].fixed=true;
                chart_1a53dbfa024e4c22b72f77a579c0c63b.setOption(option);
            }
        )
        '''
    )
    graph_.render(title + ".html")
    # make_snapshot(snapshot, graph_.render(), title + ".pdf")
    get_node_num(nodes)  # 获取每个社区的节点数目
    return graph_


if __name__ == '__main__':
    data_source_dir = "data_source/"
    topo_file = data_source_dir + "community_small.txt"
    flow_data_file = data_source_dir + "flow_data.txt"
    flow_data_new_file = data_source_dir + "flow_data_new.txt"
    layout_file = data_source_dir + "layout.txt"
    node_type_file = data_source_dir + "node_type.txt"

    NODE_NORMAL_SIZE = 15  # Identifies the standard size of a common no-flow node
    TRAFFIC_UNIT = 10 ** 6  # * The magnitude of traffic data
    TRAFFIC_UNIT_PRINT = "1M"  # * The unit of traffic data for print, need to change with the TRAFFIC_UNIT

    # graph = run(layout="force", title="TISCALI_SEA Topology", showlabel=False)
    graph = run(layout="force", title="Test Topology", showlabel=False)
    print("done!")
