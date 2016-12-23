import copy
import pandas as pd
from bokeh.layouts import row, widgetbox
from bokeh.models import Jitter
from bokeh.models import Select, CustomJS, Button
from bokeh.palettes import plasma
from bokeh.plotting import curdoc, figure, ColumnDataSource
from bokeh.tile_providers import STAMEN_TERRAIN




def get_data():
    data = pd.read_csv("../bcur_munged.csv")

    data['grp'] = data['grp'].apply(str)
    data['assign'] = data['assign'].apply(str)

    data.northing = data.northing.apply(lambda x: 15000000 if pd.isnull(x) else x)
    data.easting = data.easting.apply(lambda x: 0 if pd.isnull(x) else x)
    data = data.applymap(lambda x: "NaN" if pd.isnull(x) else x)

    return data

def create_source(df):
    df["size"] = 9
    if size.value != 'None':
        groups = pd.qcut(df[size.value].values, len(SIZES))
        df["size"] = [SIZES[xx] for xx in groups.codes]

    df["color"] = "#31AADE"
    if color.value != 'None' and color.value in quantileable:
        colors = plasma(11)
        groups = pd.qcut(df[color.value].values, len(colors))
        df["color"] = [colors[xx] for xx in groups.codes]
    # elif color.value != 'None' and color.value in discrete_colorable:
    #     values = df[color.value][pd.notnull(df[color.value])].unique()
    #     colors = plasma(len(values))
    #     if all([val.isnumeric() for val in values]):
    #         values = sorted(values, key=lambda x: float(x))
    #     codes = dict(zip(values, range(len(values))))
    #     groups = [codes[val] for val in df[color.value].values]
    #     df["color"] = [colors[xx] for xx in groups]

    df["xs"] = df[x.value]
    df["ys"] = df[y.value]
    df["ns"] = df["northing"]
    df["es"] = df["easting"]

    # create a ColumnDataSource from the  data set
    return ColumnDataSource(df[["ns", "es", "xs", "ys", "northing", "easting", "color", "size"]])

def update_source(s, df):
    df["size"] = 9
    if size.value != 'None':
        groups = pd.qcut(df[size.value].values, len(SIZES))
        df["size"] = [SIZES[xx] for xx in groups.codes]

    df["color"] = "#31AADE"
    if color.value != 'None' and color.value in quantileable:
        colors = plasma(11)
        groups = pd.qcut(df[color.value].values, len(colors))
        df["color"] = [colors[xx] for xx in groups.codes]
    # elif color.value != 'None' and color.value in discrete_colorable:
    #     values = df[color.value][pd.notnull(df[color.value])].unique()
    #     colors = plasma(len(values))
    #     if all([val.isnumeric() for val in values]):
    #         values = sorted(values, key=lambda x: float(x))
    #     codes = dict(zip(values, range(len(values))))
    #     groups = [codes[val] for val in df[color.value].values]
    #     df["color"] = [colors[xx] for xx in groups]

    df["xs"] = df[x.value]
    df["ys"] = df[y.value]
    df["ns"] = df["northing"]
    df["es"] = df["easting"]

    # create a ColumnDataSource from the  data set
    s.data = s.from_df(df[["ns", "es", "xs", "ys", "northing", "easting", "color", "size"]])

def create_crossfilter(s, df):
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

    p = figure(plot_height=600, plot_width=800, tools="wheel_zoom,reset,box_select", **kw,
               title="%s vs %s" % (x_title, y_title))

    if x.value in discrete:
        p.xaxis.major_label_orientation = pd.np.pi / 4

    # plot data on crossfilter
    p.circle(x="xs", y="ys", color="color", size="size", source=source, line_color="white",
             alpha=0.6)

    return p

def create_map(s):
    # stamen = copy.copy(STAMEN_TERRAIN)
    # create map
    bound = 20000000  # meters
    m = figure(tools="wheel_zoom,reset,box_select", x_range=(-bound, bound),
               y_range=(-bound, bound))
    m.axis.visible = False
    # m.add_tile(stamen)

    # plot data on world map
    m.circle(x="es", y="ns", color="color", size="size", source=source, line_color="white",
             alpha=0.6,
             hover_color='white', hover_alpha=0.5)

    return m


def update(attr, old, new):
    update_source(source, data)
    layout.children[1] = create_crossfilter(source, data)
    layout.children[2] = create_map(source)


SIZES = list(range(6, 22, 3))

data = get_data()

columns = list(data.columns)
discrete = [x for x in columns if data[x].dtype == object]
continuous = [x for x in columns if x not in discrete]
quantileable = [x for x in continuous if len(data[x].unique()) > 20]

x = Select(title='X-Axis', value='LD1', options=columns)
x.on_change('value', update)

y = Select(title='Y-Axis', value='LD2', options=columns)
y.on_change('value', update)

size = Select(title='Size', value='None', options=['None'] + quantileable)
size.on_change('value', update)

color = Select(title='Color', value='None', options=['None'] + quantileable)
color.on_change('value', update)

source = ColumnDataSource(
    data=dict(ns=[], es=[], xs=[], ys=[], northing=[], easting=[], color=[], size=[]))

controls = widgetbox([x, y, color, size], width=200)
layout = row(controls, create_crossfilter(source, data), create_map(source))

curdoc().add_root(layout)
curdoc().title = "Crossfilter"
