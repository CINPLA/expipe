import matplotlib.pyplot as plt


def set_grid(ax, bgcolor="#EAEAF2", linecolor="w", linestyle="-", linewidth=1.3):
    """
    Set background color and grid line options

    Parameters
    ----------
    ax : matplotlib.axis
        axis object

    bgcolor : str
        background color

    linecolor : str
        linecolor color

    linestyle : str
        linestyle

    linewidth : float
        linewidth
    """
    ax.set_facecolor(bgcolor)
    ax.set_axisbelow("True")
    ax.grid(True, color=linecolor, linestyle=linestyle, linewidth=linewidth, zorder=0)


def spines_edge_color(ax, edges={"top": "none", "bottom": "w",
                                 "right": "none", "left": "w"}):
    """
    Set spines edge color

    Parameters
    ----------
    ax : matplotlib.axis
        axis object

    edges : dictionary
        edges as keys with colors as key values
    """
    
    if edges is None:
        edges = {"top": "none", "bottom": "none",
                 "right": "none", "left": "none"}
    for edge, color in edges.iteritems():
        ax.spines[edge].set_edgecolor(color)
        
        
def remove_ticklabels(ax, x_axis=True, y_axis=True):
    """
    Remove ticklabels
    Parameters
    ----------
    Required arguments
    ax : matplotlib.axis
        axis object
    x_axis : bool
        remove xticklabels
    y_axis : bool
        remove yticklabels
    """

    if x_axis:
        labels = [item.get_text() for item in ax.get_xticklabels()]
        empty_string_labels = ['']*len(labels)
        ax.set_xticklabels(empty_string_labels)
    if y_axis:
        labels = [item.get_text() for item in ax.get_yticklabels()]
        empty_string_labels = ['']*len(labels)
        ax.set_yticklabels(empty_string_labels)


def move_spines(ax, edges={"bottom": 0, "left": 0}):
    """
    Move spines
    Parameters
    ----------
    Required arguments
    ax : matplotlib.axis
        axis object
    edges : dictionary
        edges as keys with value as key values
    """

    for edge, value in edges.iteritems():
        ax.spines[edge].set_position(('data', value))


def remove_ticks(ax):
    """
    Removes ticks

    Parameters
    ----------
    ax : matplotlib.axis
        axis object
    """
    ax.xaxis.set_ticks_position('none')
    ax.yaxis.set_ticks_position('none')


def set_font():
    """
    font options
    """
    params = {
        'font.family': [u'sans-serif'],
        'font.sans-serif':
        [u'Arial',
         u'Liberation Sans',
         u'Bitstream Vera Sans',
         u'sans-serif'],
        'font.size': 14,
        'axes.titlesize': 18,
        'axes.labelsize': 16,
        'lines.linewidth': 2,
    }
    plt.rcParams.update(params)


def set_legend():
    """
    legend options
    """
    params = {
        'legend.fontsize': 'medium',
        'legend.handlelength': 2.2,
        'legend.frameon': False,
        'legend.numpoints': 1,
        'legend.scatterpoints': 1,
        'legend.fontsize': 14,
        'legend.handlelength': 2.2,
        'legend.borderpad': 0.0,
        'legend.framealpha': 2,
    }
    plt.rcParams.update(params)


def colormap(color=0):
    """
    colormap

    Parameters
    ----------
    color : int
        color index

    Returns
    -------
    color array in a format which is accepted by matplotlib
    """
    # These are the "Tableau 20" colors as RGB.
    tableau20 = [(31, 119, 180), (14, 199, 232), (255, 127, 14), (255, 187, 120),
                 (44, 160, 44), (152, 223, 138), (214, 39, 40), (255, 152, 150),
                 (148, 103, 189), (197, 176, 213), (140, 86, 75), (196, 156, 148),
                 (227, 119, 194), (247, 182, 210), (127, 127, 127), (199, 199, 199),
                 (188, 189, 34), (219, 219, 141), (23, 190, 207), (158, 218, 229)]

    color = color % len(tableau20)
    # Scale the RGB values to the [0, 1] range, which is the format matplotlib accepts.
    for i in range(len(tableau20)):
        r, g, b = tableau20[i]
        tableau20[i] = (r / 255., g / 255., b / 255.)

    return tableau20[color]

#########################################################################################
if __name__ == "__main__":
    import numpy as np 
    
    t = np.linspace(0, 100, 1000)
    fig = plt.figure()
    ax = fig.add_subplot(111)

    spines_edge_color(ax)
    remove_ticks(ax)
    set_grid(ax)

    set_font()
    set_legend()

    ax.plot(np.sin(0.1*t), color=colormap(0), label="test A")
    ax.plot(np.cos(0.1*t), color=colormap(2), label="test B")
    ax.set_xlabel("time")
    ax.set_title("Test")

    plt.legend(loc=1)
    plt.show()
