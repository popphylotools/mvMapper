import pandas as pd

from bokeh.layouts import row, widgetbox
from bokeh.models import Select, CustomJS, Button
from bokeh.palettes import plasma
from bokeh.plotting import curdoc, figure, ColumnDataSource
from bokeh.tile_providers import STAMEN_TERRAIN
from bokeh.models import Jitter
import copy

ter = copy.copy(STAMEN_TERRAIN)

df = pd.read_csv("../bcur_munged.csv")

df['grp'] = df['grp'].apply(str)
df['assign'] = df['assign'].apply(str)

SIZES = list(range(6, 22, 3))

columns = list(df.columns)
discrete = [x for x in columns if df[x].dtype == object]
discrete_colorable = [x for x in discrete if len(df[x].unique()) <= max(len(df["grp"].unique()),
                                                                        len(df[
                                                                                "assign"].unique()))]
continuous = [x for x in columns if x not in discrete]
quantileable = [x for x in continuous if len(df[x].unique()) > 20]

df.northing = df.northing.apply(lambda x: 15000000 if pd.isnull(x) else x)
df.easting = df.easting.apply(lambda x: 0 if pd.isnull(x) else x)
df = df.applymap(lambda x: "NaN" if pd.isnull(x) else x)

source = ColumnDataSource(
    data=dict(ns=[], es=[], xs=[], ys=[], northing=[], easting=[], color=[], size=[]))


def create_crossfilter():
    kw = dict()
    if x.value in discrete:
        values = df[x.value][pd.notnull(df[x.value])].unique()
        if all([val.isnumeric() for val in values]):
            kw["x_range"] = sorted(values, key=lambda x: float(x))
        else:
            kw["x_range"] = sorted(values)
    if y.value in discrete:
        values = df[y.value][pd.notnull(df[y.value])].unique()
        if all([val.isnumeric() for val in values]):
            kw["y_range"] = sorted(values, key=lambda x: float(x))
        else:
            kw["y_range"] = sorted(values)

    x_title = x.value.title()
    y_title = y.value.title()

    plot = figure(plot_height=600, plot_width=800, tools="wheel_zoom,reset,box_select", **kw,
               title="%s vs %s" % (x_title, y_title))

    if x.value in discrete:
        plot.xaxis.major_label_orientation = pd.np.pi / 4

    # plot data on crossfilter
        plot.circle(x="xs", y="ys", color="color", size="size", source=source, line_color="white",
             alpha=0.6)

    return plot


def update_data():
    # size
    df["size"] = 9
    if size.value != 'None':
        groups = pd.qcut(df[size.value].values, len(SIZES))
        df["size"] = [SIZES[xx] for xx in groups.codes]

    # color
        df["color"] = "#31AADE"
    if color.value != 'None' and color.value in quantileable:
        COLORS = plasma(11)
        groups = pd.qcut(df[color.value].values, len(COLORS))
        df["color"] = [COLORS[xx] for xx in groups.codes]

    elif color.value != 'None' and color.value in discrete_colorable:
        values = df[color.value][pd.notnull(df[color.value])].unique()
        COLORS = plasma(len(values))

        # if all([val.isnumeric() for val in values]):
        #     values = sorted(values, key=lambda x: float(x))

        codes = dict(zip(values, range(len(values))))
        groups = [codes[val] for val in df[color.value].values]
        df["color"] = [COLORS[xx] for xx in groups]

    df["xs"] = df[x.value]
    df["ys"] = df[y.value]
    df["ns"] = df["northing"]
    df["es"] = df["easting"]

    # create a ColumnDataSource from the  data set
    source.data = source.from_df(
        df[["ns", "es", "xs", "ys", "northing", "easting", "color", "size"]])


# widgets #############################################
def x_change(attr, old, new):
    update_data()
    d = layout.children[1]
    layout.children[1] = create_crossfilter()
    del d


x = Select(title='X-Axis', value='LD1', options=columns)
x.on_change('value', x_change)


def y_change(attr, old, new):
    update_data()
    d = layout.children[1]
    layout.children[1] = create_crossfilter()
    del d


y = Select(title='Y-Axis', value='LD2', options=columns)
y.on_change('value', y_change)


def size_change(attr, old, new):
    update_data()


size = Select(title='Size', value='posterior_assign', options=['None'] + quantileable)
size.on_change('value', size_change)


def color_change(attr, old, new):
    update_data()


color = Select(title='Color', value='assign', options=['None'] + quantileable + discrete_colorable)
color.on_change('value', color_change)

# figures ############################################

# create crossfilter
p = create_crossfilter()

# create map
bound = 20000000  # meters
m = figure(tools="wheel_zoom,reset,box_select", x_range=(-bound, bound), y_range=(-bound, bound))
m.axis.visible = False
m.add_tile(ter)
# plot data on world map
# m.circle(x={'field': "easting", 'transform': Jitter(width=150000)}, y={'field': "northing", 'transform': Jitter(width=150000)}, color="color", size="size", source=source, line_color="white", alpha=0.6,
#          hover_color='white', hover_alpha=0.5)
m.circle(x="es", y="ns", color="color", size="size", source=source, line_color="white", alpha=0.6,
         hover_color='white', hover_alpha=0.5)

map_jitter = Jitter(width=16093, distribution="uniform")

jitter_callback = CustomJS(args=dict(source=source, map_jitter=map_jitter), code="""
    var data = source.data;
    for (var i = 0; i < data['easting'].length; i++) {
        data['es'][i] = map_jitter.compute(data['easting'][i]);
    }
    for (var i = 0; i < data['northing'].length; i++) {
        data['ns'][i] = map_jitter.compute(data['northing'][i]);
    }
    source.trigger('change');
""")

reset_jitter_callback = CustomJS(args=dict(source=source, map_jitter=map_jitter), code="""
    var data = source.data;
    for (var i = 0; i < data['easting'].length; i++) {
        data['es'][i] = data['easting'][i];
    }
    for (var i = 0; i < data['northing'].length; i++) {
        data['ns'][i] = data['northing'][i];
    }
    source.trigger('change');
""")

map_jitter_button = Button(label='apply jitter to map', callback=jitter_callback)
reset_map_jitter_button = Button(label='remove jitter from map', callback=reset_jitter_callback)

# layout ###########################################
# initilize data
update_data()

crossfilter_controls = widgetbox([x, y, color, size], width=200)
map_controls = widgetbox([map_jitter_button, reset_map_jitter_button], width=200)
layout = row(crossfilter_controls, p, m, map_controls)

curdoc().add_root(layout)
curdoc().title = "Crossfilter"
