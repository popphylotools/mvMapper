import copy
import pandas as pd
from bokeh.layouts import row, widgetbox
from bokeh.models import Jitter
from bokeh.models import Select, CustomJS, Button
from bokeh.palettes import plasma
from bokeh.plotting import curdoc, figure, ColumnDataSource
from bokeh.tile_providers import STAMEN_TERRAIN

default_color_count = 11
SIZES = list(range(6, 22, 3))



def get_data():
    data = pd.read_csv("../bcur_munged.csv")

    data['grp'] = data['grp'].apply(str)
    data['assign'] = data['assign'].apply(str)

    data.northing = data.northing.apply(lambda x: 15000000 if pd.isnull(x) else x)
    data.easting = data.easting.apply(lambda x: 0 if pd.isnull(x) else x)

    data = data.applymap(lambda x: "NaN" if pd.isnull(x) else x)

    return data


def create_source():
    df["size"] = 9
    if size.value != 'None':
        groups = pd.cut(df[size.value].values, len(SIZES))
        df["size"] = [SIZES[xx] for xx in groups.codes]

    df["color"] = "#31AADE"
    if color.value != 'None' and color.value in quantileable:
        colors = plasma(default_color_count)
        groups = pd.cut(df[color.value].values, len(colors))
        df["color"] = [colors[xx] for xx in groups.codes]
    elif color.value != 'None' and color.value in discrete_colorable:
        values = df[color.value][pd.notnull(df[color.value])].unique()
        colors = plasma(len(values))
        if all([val.isnumeric() for val in values]):
            values = sorted(values, key=lambda x: float(x))
        codes = dict(zip(values, range(len(values))))
        groups = [codes[val] for val in df[color.value].values]
        df["color"] = [colors[xx] for xx in groups]

    df["ns"] = df["northing"]
    df["es"] = df["easting"]

    # create a ColumnDataSource from the  data set
    return ColumnDataSource(df)


def update_source(s):
    df["size"] = 9
    if size.value != 'None':
        groups = pd.cut(df[size.value].values, len(SIZES))
        df["size"] = [SIZES[xx] for xx in groups.codes]

    df["color"] = "#31AADE"
    if color.value != 'None' and color.value in quantileable:
        colors = plasma(default_color_count)
        groups = pd.cut(df[color.value].values, len(colors))
        df["color"] = [colors[xx] for xx in groups.codes]
    elif color.value != 'None' and color.value in discrete_colorable:
        values = df[color.value][pd.notnull(df[color.value])].unique()
        colors = plasma(len(values))
        if all([val.isnumeric() for val in values]):
            values = sorted(values, key=lambda x: float(x))
        codes = dict(zip(values, range(len(values))))
        groups = [codes[val] for val in df[color.value].values]
        df["color"] = [colors[xx] for xx in groups]

    # create a ColumnDataSource from the  data set
    s.data["size"] = df["size"]
    s.data["color"] = df["color"]


def create_crossfilter(s):
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

    p = figure(plot_height=600, plot_width=800, tools="wheel_zoom, reset, box_select", **kw,
               title="%s vs %s" % (x_title, y_title))

    if x.value in discrete:
        p.xaxis.major_label_orientation = pd.np.pi / 4

    # plot data on crossfilter
    p.circle(x=x.value, y=y.value, color="color", size="size", source=s, line_color="white",
             alpha=0.6)

    return p


def create_map(s):
    stamen = copy.copy(STAMEN_TERRAIN)
    # create map
    bound = 20000000  # meters
    m = figure(tools="wheel_zoom, reset, box_select", x_range=(-bound, bound),
               y_range=(-bound, bound))
    m.axis.visible = False
    m.add_tile(stamen)

    # plot data on world map
    m.circle(x="es", y="ns", color="color", size="size", source=s, line_color="white",
             alpha=0.6,
             hover_color='white', hover_alpha=0.5)

    return m


def create_jitter_buttons(s):
    map_jitter = Jitter(width=16093, distribution="uniform")

    jitter_callback = CustomJS(args=dict(source=s, map_jitter=map_jitter), code="""
        var data = source.data;
        for (var i = 0; i < data['easting'].length; i++) {
            data['es'][i] = map_jitter.compute(data['easting'][i]);
        }
        for (var i = 0; i < data['northing'].length; i++) {
            data['ns'][i] = map_jitter.compute(data['northing'][i]);
        }
        source.trigger('change');
    """)

    reset_jitter_callback = CustomJS(args=dict(source=s, map_jitter=map_jitter), code="""
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

    reset_map_jitter_button = Button(label='remove jitter from map',
                                     callback=reset_jitter_callback)

    return map_jitter_button, reset_map_jitter_button


# callbacks
def x_change(attr, old, new):
    layout.children[1] = create_crossfilter(source)


def y_change(attr, old, new):
    layout.children[1] = create_crossfilter(source)


def size_change(attr, old, new):
    update_source(source)


def color_change(attr, old, new):
    update_source(source)


# load data
df = get_data()

# catigorize columns
columns = [c for c in df.columns if c not in ["Decimal Latitude", "Decimal Longitude"]]
discrete = [x for x in columns if df[x].dtype == object]
discrete_colorable = [x for x in discrete if len(df[x].unique()) <= max(len(df["grp"].unique()),
                                                                        len(df[
                                                                                "assign"].unique()))]
continuous = [x for x in columns if x not in discrete]
quantileable = [x for x in continuous if len(df[x].unique()) > 20]

# create widgets
x = Select(title='X-Axis', value='LD1', options=columns)
x.on_change('value', x_change)

y = Select(title='Y-Axis', value='LD2', options=columns)
y.on_change('value', y_change)

size = Select(title='Size', value='posterior_assign', options=['None'] + quantileable)
size.on_change('value', size_change)

color = Select(title='Color', value='assign', options=['None'] + quantileable + discrete_colorable)
color.on_change('value', color_change)

# initilize source
source = create_source()

# initialize plots
crossfilter = create_crossfilter(source)
map = create_map(source)

# create layout
crossfilter_controls = widgetbox([x, y, color, size], width=200)
map_controls = widgetbox([*create_jitter_buttons(source)], width=200)
layout = row(crossfilter_controls, crossfilter, map, map_controls)

curdoc().add_root(layout)
curdoc().title = "Crossfilter"
