from matplotlib import pyplot as plt
from matplotlib.pyplot import MultipleLocator


def draw(x_input, y_input=None, size=(18, 12), x_locator=600, y_locator=10000, title='inventory allot'):
    if y_input is None:
        y_input = dict()
    plt.figure(figsize=size)
    # plt.rcParams['figure.dpi'] = 500  # 分辨率 1800*1200
    # 把x轴的刻度间隔设置为1，并存在变量里
    x_major_locator = MultipleLocator(x_locator)
    # 把y轴的刻度间隔设置为10，并存在变量里
    y_major_locator = MultipleLocator(y_locator)
    ax = plt.gca()
    # ax为两条坐标轴的实例
    ax.xaxis.set_major_locator(x_major_locator)
    # 把x轴的主刻度设置为1的倍数
    ax.yaxis.set_major_locator(y_major_locator)
    # 不显示科学计数
    ax.get_yaxis().get_major_formatter().set_scientific(False)

    plt.title(title)
    plt.xlabel("x-time(s)")
    plt.ylabel("y-num")
    for k, v in y_input.items():
        plt.plot(x_input, v)
    plt.text(0, y_locator * 1, 'start numbers:{}'.format(0))
    plt.text(364, 101000, '100000 / 364 * 60 * 60 = 989010.9890')
    plt.text(568, 60000, '59034 / 568 * 60 * 60 = 367891.3495')
    plt.show()
