import numpy as np
import matplotlib.colors as colors
import matplotlib.pyplot as plt
import quantities as pq


def polar_tuning_curve(orients, rates, params={}):
    """
    Direction polar tuning curve 
    """
    import numpy as np    
    import math
    from expipe.analysis.misc import pretty_plotting
    
    assert len(orients) == len(rates)
    
    fig, ax = plt.subplots()  
    ax = plt.subplot(111, projection='polar')
    ax.plot(orients, rates, '-o', **params)

    return fig, ax
    

def _gauss_function(x, y, A=1, a=0.63):
    r2 = x**2 + y**2
    return A / a**2 / np.pi * np.exp(-r2 / a**2)

    
def _dog_function(x, y, A=1.0, a=0.63, B=0.85, b=1.23):
    center = _gauss_function(x, y, A, a)
    surround = _gauss_function(x, y, B, b)
    return center - surround

    
def _doe_function(t, a=1, b=2):
    return np.exp(-t / a) / a**2 - np.exp(-t / b) / b**2


def _field(x, y, t, A=1.0, a=0.63, B=0.85, b=1.23, c=1, d=2):
    return _dog_function(x, y, A, a, B, b) * _doe_function(t, c, d)
    

class MidpointNormalize(colors.Normalize):
    def __init__(self, vmin=None, vmax=None, midpoint=None, clip=False):
        self.midpoint = midpoint
        colors.Normalize.__init__(self, vmin, vmax, clip)

    def __call__(self, value, clip=None):
        x, y = [self.vmin, self.midpoint, self.vmax], [0, 0.5, 1]
        return np.ma.masked_array(np.interp(value, x, y))


def rectangular_scalebar(ax, params={}): 
        '''
        Adds scalebar (rectangle) to an axes object with text
        
        Parameters
        ----------
        field : matplotlib.axes
            axes object
        
        Returns
        -------
        matplotlib.axes
            axes object

        '''
        # TODO: need to fix for non square grid
        import matplotlib.patches as patches
        scalebar_origin_x = ax.get_xticks()[-3]
        scalebar_origin_y = ax.get_yticks()[1]
        scalebar_width = ax.get_xticks()[1] - ax.get_xticks()[0] 
        scalebar_height = ax.get_yticks()[1] - ax.get_yticks()[0]
        ax.add_patch(
            patches.Rectangle(
                xy=(scalebar_origin_x, scalebar_origin_y),
                width=scalebar_width,
                height=scalebar_height,
                fill = False,
                edgecolor= "y",
                linewidth = 2.0
                )
        )    
        ax.text(scalebar_origin_x+scalebar_width/5., 
                scalebar_origin_y+scalebar_height+scalebar_height*0.1, 
                str(scalebar_width)+" deg", 
                **params)
        
        return ax

    
def plot_2d_receptive_field(field, 
                            ax=None,
                            mask=True,
                            mask_color="w",
                            norm=None,
                            params={}):
    '''
    Plots spatial (x vs y) or spatiotemporal (x/y vs t) 
    receptive field function in 2d    
    
    Parameters
    ----------
    field : 2d array
        receptive field function
    
    Returns
    -------

    '''
    import matplotlib.pyplot as plt
    if ax is None:
        fig, ax = plt.subplots()  
    if(mask):
        cmap = plt.cm.get_cmap(params["cmap"])
        cmap.set_bad(mask_color, alpha=1)
    
    im = ax.imshow(field, norm=norm, **params)
    return im, ax

    

def plot_1d_receptive_field(field,
                            x_axis=None,
                            ax=None,
                            params={}):
    
    
    
    if ax is None:
        fig, ax = plt.subplots()  
    
    if x_axis is None:    
        x_axis = range(len(field))
    
    line = ax.plot(x_axis, field, **params)
    
    fill = True
    if fill:
        ax.fill_between(x_axis, 0, field, where=field < 0, facecolor='#5B9FCF', alpha=0.7)
        ax.fill_between(x_axis, 0, field, where=field >= 0, facecolor='#E65D6D', alpha=0.7)

    return line, ax
    
    
def plot_advance_receptive_field(field):
    
    
    from expipe.analysis.misc import pretty_plotting
        
    params = {}
    params["cmap"] = "bwr"
    params["origin"] = "lower"
    params["aspect"] = None
    params["interpolation"] = "None"
    params["extent"] = [min(x), max(x), min(y), max(y)]
    
    scalebar_params = {}
    scalebar_params["color"] = "y"
    scalebar_params["fontsize"] = 18
    
    masked_field = np.ma.masked_inside (field, -0.01, 0.05)
    # norm = MidpointNormalize(midpoint=0.)
    norm = None
            
    fig, (ax_im, ax_line) = plt.subplots(2, 1, figsize=(5,10), sharex=True)
    pretty_plotting.set_font()
    pretty_plotting.set_grid(ax_im, linecolor="w")
    pretty_plotting.spines_edge_color(ax_im, edges=None)
    pretty_plotting.remove_ticks(ax_im)
    pretty_plotting.remove_ticklabels(ax_im)
    
    im, ax_im = plot_2d_receptive_field(field=masked_field, 
                                        ax=ax_im,
                                        mask=True,
                                        mask_color="k",
                                        norm=norm,
                                        params=params)
    rectangular_scalebar(ax=ax_im, params=scalebar_params)
    ax_im.set_xlabel("x")
    ax_im.set_ylabel("y")
    ax_im.set_xlim(x.min(), x.max())
    ax_im.set_ylim(y.min(), y.max())
    
    
    line, ax_line = plot_1d_receptive_field(field=field[50,:],
                                            x_axis=x,
                                            ax=ax_line)
    ax_line.set_xlim([x.min(),x.max()])
    pretty_plotting.remove_ticks(ax_line)
    pretty_plotting.move_spines(ax_line)
    pretty_plotting.remove_ticklabels(ax_line)


    # fig.tight_layout()
    # fig.colorbar(im)
    
    return fig, (ax_im, ax_line)




    

if __name__ == "__main__":
    from neo.core import SpikeTrain
    import quantities as pq

    trails = [
            SpikeTrain(np.arange(0, 10, 1)*pq.s, t_stop=10.0, annotations="0"),
            SpikeTrain(np.arange(0, 10, 1)*pq.s, t_stop=10.0, annotations="30"),
            SpikeTrain(np.arange(0, 10, 0.5)*pq.s, t_stop=10.0, annotations="45"),
            SpikeTrain(np.arange(0, 10, 1)*pq.s, t_stop=10.0, annotations="60"),
            SpikeTrain(np.arange(0, 10, 1)*pq.s, t_stop=10.0, annotations="90"),
            SpikeTrain(np.arange(0, 10, 1)*pq.s, t_stop=10.0, annotations="120"),
            SpikeTrain(np.arange(0, 10, 0.5)*pq.s, t_stop=10.0, annotations="180"),
            SpikeTrain(np.arange(0, 10, 1)*pq.s, t_stop=10.0, annotations="270"),
            SpikeTrain(np.arange(0, 10, 1)*pq.s, t_stop=10.0, annotations="315")
            ]
            
    polar_tuning_curve(trails=trails, params={})

    
    x = np.linspace(-4, 4, 100)
    y = np.linspace(-4, 4, 100)
    t = np.linspace(0, 10, 100)
    xx, tt, yy = np.meshgrid(x, t, y, sparse=True)
    field = _field(xx, yy, tt)
    fig, axarr = plot_advance_receptive_field(field=field[0,:,:])
    

    plt.show()
    
    
