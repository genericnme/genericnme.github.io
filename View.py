import ipywidgets as widgets
import matplotlib.pyplot as plt
import matplotlib.patches as mplpatches
import cartopy.crs as ccrs
import Model as model
import Plotconfiguration as pconf
from metpy.units import units

dbg = widgets.Output()
plot_output = widgets.Output()
pointselection_out = widgets.Output()

start_end_cords = []
a = model.Model()
var_selection = widgets.Select(options=a.get_var_names(), layout=widgets.Layout(width='100px', height='225px'))
data_vars = widgets.Accordion([], layout=widgets.Layout(width='425px'))

@dbg.capture()
def on_open_dset_btn_click(b):
    a.open_dset()
    var_selection.options = a.get_var_names()
    show_pointselection()


def on_remove_btn_click(b):
    ind = data_vars.selected_index
    varname = data_vars.get_title(ind)
    a.remove_var(varname)
    update_data_vars()

def get_var_description(var):
    remove_btn = widgets.Button(description='Remove variable')
    remove_btn.on_click(on_remove_btn_click)
    descr = widgets.Textarea(value=a.get_desc(var), layout=widgets.Layout(width='425px', height='350px'))
    return widgets.VBox([descr, remove_btn])


def update_data_vars():
    data_vars.children = [get_var_description(var) for var in a.get_to_plot_vars()]
    [data_vars.set_title(i, title=name) for i, name in enumerate(a.get_to_plot_vars())]


def on_add_btn_click(b):
    conf = pconf.Plotconfiguration(sel_cmap.value, sel_grades.value, sel_fill.value)
    a.add_var_to_plot(var_selection.value, conf)
    update_data_vars()

def on_plot_btn_click(b):
    try:
        plevs = [float(i) for i in sel_levels.value.split(sep=',')] * units.hPa
    except Exception as e:
        with dbg:
            print(e)
        plevs = [1000., 800., 900., 700., 600., 500., 400., 300., 200., 100., 90., 80., 70., 60., 50., 40., 30., 20.,
                 10.] * units.hPa
    finally:
        plevs[::-1].sort()
    if plottype_sel.value=='Cross Section':
        start = start_end_cords[0]
        end = start_end_cords[1]
        #Cords to data range
        if start['lon'] < 0:
            start['lon'] += 360
        if end['lon'] < 0:
            end['lon'] += 360
        with plot_output:
            a.do_csec_plot(plevs, start, end)

    elif plottype_sel.value=='Horizontal':
        a.do_horizontal_plot(plevs)
    plt.show()
    a.reset_data_vars()


def area_on_map(left, bottom, width, height):
    plt.figure(1, figsize=(16, 9))
    ax = plt.axes(projection=ccrs.PlateCarree(), label='Areaselection')
    ax.stock_img()
    if left >= 180:
        left -= 360
    rect = mplpatches.Rectangle([left, bottom], width, height)
    ax.add_patch(rect)
    plt.show()


@dbg.capture()
def on_click_on_map(event):
    if len(start_end_cords) >= 2:
        start_end_cords.pop(0)  # Delete marker which is closer to the click
    start_end_cords.append({'lon': round(event.xdata), 'lat': round(event.ydata)})  # Check values?
    plt.figure(2)
    plt.cla()
    plt.axes(projection=ccrs.PlateCarree(), label='pointselection').stock_img()
    for mrk in start_end_cords:
        plt.plot(mrk['lon'], mrk['lat'], '+-r', transform=ccrs.PlateCarree(), ms=40)
    print('button=%d, x=%d, y=%d, xdata=%f, ydata=%f' %
         (event.button, event.x, event.y, event.xdata, event.ydata))


def show_pointselection():
    with pointselection_out:
        fig = plt.figure(2, figsize=(16, 9))
        plt.axes(projection=ccrs.PlateCarree(), label='pointselection').stock_img()
        plt.show()
        cid = fig.canvas.mpl_connect('button_press_event', on_click_on_map)

bottom_lat = widgets.BoundedIntText(min=-90,
                                    max=90,
                                    description='Bottom Lat:')
left_lon = widgets.BoundedIntText(min=0,
                                  max=360,
                                  description='Left Lon:')
height = widgets.BoundedIntText(min=10,
                                max=360,
                                description='Height:')  # Change width and height to top_lat and right_lon
width = widgets.BoundedIntText(min=10,
                               max=180,
                               description='Width:')

area_selection_input = widgets.VBox([left_lon, bottom_lat, height, width])
area_on_map_out = widgets.interactive_output(area_on_map,
                                             {'left': left_lon, 'bottom': bottom_lat, 'width': width, 'height': height})

area_vbox = widgets.VBox([area_selection_input, area_on_map_out])

# configurations specific for each variable:
sel_grades = widgets.BoundedIntText(value=15, min=5, max=100, description='Number of Colorgrades:')
sel_cmap = widgets.Dropdown(options=plt.colormaps(), description="Colormap:")
sel_fill = widgets.Checkbox(description='Filled Plot', value=True)

add_btn = widgets.Button(description="Add to Plot")

add_btn.on_click(on_add_btn_click)

plotconf_inp = widgets.VBox([sel_fill, sel_grades, sel_cmap, add_btn])

var_conf_sel = widgets.HBox([var_selection, plotconf_inp, data_vars])

plottype_sel = widgets.Dropdown(options=['Cross Section', 'Horizontal'], description='Type of plot')
sel_levels = widgets.Textarea(
    value="1000, 800, 900, 700, 600, 500, 400, 300, 200, 100, 90, 80, 70, 60, 50, 40, 30, 20, 10",
    placeholder="Type in desired Pressure levels (comma seperated)",
    description="Pressure levels:")

general_hbox = widgets.HBox([plottype_sel, sel_levels])#let user pick x-axis variable for csec and 'level' for horizontal plot

accordion = widgets.Accordion(children=[general_hbox, var_conf_sel, pointselection_out, area_vbox])
accordion.set_title(0, 'Type of plot')
accordion.set_title(1, 'Variables to plot')
accordion.set_title(2, 'Start-/Endpoint (Cross Section)')
accordion.set_title(3, 'Area (On Level)')

open_dset_btn = widgets.Button(description="Open Dataset")
plot_btn = widgets.Button(description="Plot")
plot_vbox = widgets.VBox([plot_btn, plot_output])

plot_btn.on_click(on_plot_btn_click)
open_dset_btn.on_click(on_open_dset_btn_click)


toolbox = widgets.Tab()
toolbox.children = [open_dset_btn, accordion, plot_vbox, dbg]
toolbox.set_title(0, 'Dataset Selection')
toolbox.set_title(1, 'Options')
toolbox.set_title(2, 'Plot')
toolbox.set_title(3, 'Debug Output')