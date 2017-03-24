import copy
import pandas as pd
from bokeh.layouts import row, widgetbox, layout
from bokeh.models import Select, CustomJS, Jitter, DataTable, TableColumn, Slider, Button
from bokeh.palettes import plasma
from bokeh.plotting import curdoc, figure, ColumnDataSource
from bokeh.tile_providers import STAMEN_TERRAIN
import pyproj
import os
import json

default_color_count = 11
SIZES = list(range(6, 22, 3))


##################
# data handeling #
##################

def get_data():
    """Read data from csv and transform map coordinates. """
    data = pd.read_csv("data/webapp_data.csv")

    data['grp'] = data['grp'].apply(str)
    data['assign'] = data['assign'].apply(str)


    data = data.applymap(lambda x: "NaN" if pd.isnull(x) else x)

    # transform coords to map projection
    wgs84 = pyproj.Proj(init="epsg:4326")
    webMer = pyproj.Proj(init="epsg:3857")
    data["easting"] = "NaN"
    data["northing"] = "NaN"
    data["easting"] = data["easting"].astype("float64")
    data["northing"] = data["northing"].astype("float64")
    data.loc[pd.notnull(data["Lng"]), "easting"], data.loc[pd.notnull(data["Lat"]), "northing"] = zip(
        *data.loc[pd.notnull(data["Lng"]) & pd.notnull(data["Lat"])].apply(
            lambda x: pyproj.transform(wgs84, webMer, x["Lng"], x["Lat"]), axis=1))

    # show unknown locations on map in antartic
    data.northing = data.northing.apply(lambda x: -15000000 if pd.isnull(x) else x)
    data.easting = data.easting.apply(lambda x: 0 if pd.isnull(x) else x)

    return data


def create_source():
    """Return new ColumnDataSource."""
    df["size"] = 9
    if size.value != 'None':
        try:
            groups = pd.qcut(df[size.value].values, len(SIZES))
        except ValueError:
            groups = pd.cut(df[size.value].values, len(SIZES))
        df["size"] = [SIZES[xx] for xx in groups.codes]

    df["color"] = "#31AADE"
    if color.value != 'None' and color.value in quantileable:
        colors = plasma(default_color_count)
        try:
            groups = pd.qcut(df[color.value].values, len(colors))
        except ValueError:
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
    """Update `size` and `color` columns of ColumnDataSource 's' to reflect """
    df["size"] = 9
    if size.value != 'None':
        try:
            groups = pd.qcut(df[size.value].values, len(SIZES))
        except ValueError:
            groups = pd.cut(df[size.value].values, len(SIZES))
        df["size"] = [SIZES[xx] for xx in groups.codes]

    df["color"] = "#31AADE"
    if color.value != 'None' and color.value in quantileable:
        colors = plasma(default_color_count)
        try:
            groups = pd.qcut(df[color.value].values, len(colors))
        except ValueError:
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
    s.data.update({"size":df["size"], "color":df["color"]})

#######################
# Data Visualizations #
#######################

def create_crossfilter(s):
    """Return a crossfilter plot linked to ColumnDataSource s"""
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

    p = figure(plot_height=700, plot_width=700, #responsive=True,
               tools="wheel_zoom, pan, save, reset, box_select, tap",
               active_drag="box_select", active_scroll="wheel_zoom",
               title="%s vs %s" % (y_title, x_title),
               **kw,)

    if x.value in discrete:
        p.xaxis.major_label_orientation = pd.np.pi / 4

    # plot data on crossfilter
    p.circle(x=x.value, y=y.value, color="color", size="size", source=s, line_color="white",
                    alpha=0.6,
                    # set visual properties for selected glyphs
                    selection_fill_color="color",
                    selection_fill_alpha=0.6,
                    selection_line_color="white",
                    selection_line_alpha=0.6,

                    # set visual properties for non-selected glyphs
                    nonselection_fill_color="white",
                    nonselection_fill_alpha=0.1,
                    nonselection_line_color="color",
                    nonselection_line_alpha=0.6,)

    return p


def create_map(s):
    """Return map linked to ColumnDataSource 's'."""
    stamen = copy.copy(STAMEN_TERRAIN)
    # create map
    bound = 20000000  # meters
    m = figure(plot_height=700, plot_width=700, #responsive=True,
               tools="wheel_zoom, pan, reset, box_select, tap",
               active_drag="box_select", active_scroll="wheel_zoom",
               x_range=(-bound, bound), y_range=(-bound, bound))
    m.axis.visible = False
    m.add_tile(stamen)

    # plot data on world map
    m.circle(x="es", y="ns", color="color", size="size", source=s, line_color="white",
                    alpha=0.6,
                    # set visual properties for selected glyphs
                    selection_fill_color="color",
                    selection_fill_alpha=0.6,
                    selection_line_color="white",
                    selection_line_alpha=0.6,

                    # set visual properties for non-selected glyphs
                    nonselection_fill_color="black",
                    nonselection_fill_alpha=0.01,
                    nonselection_line_color="color",
                    nonselection_line_alpha=0.6,)

    return m


def create_table(cols, s):
    """Return table linked to ColumnDataSource 's'."""
    table_cols = [TableColumn(field=col, title=col) for col in cols]
    return DataTable(source=s, columns=table_cols, width=1600, height=250, fit_columns=False, )

#############
# callbacks #
#############

def x_change(attr, old, new):
    """Replece crossfilter plot."""
    l.children[0].children[1] = create_crossfilter(source)

def y_change(attr, old, new):
    """Replece crossfilter plot."""
    l.children[0].children[1] = create_crossfilter(source)

def size_change(attr, old, new):
    """Update ColumnDataSource 'source'."""
    update_source(source)

def color_change(attr, old, new):
    """Update ColumnDataSource 'source'."""
    update_source(source)

def selection_change(attrname, old, new):
    """Update ColumnDataSource 'table_source' with selection found in 'source'."""
    selected = source.selected['1d']['indices']
    table_source.data = table_source.from_df(df.iloc[selected, :])

########
# Main #
########

# load data
df = get_data()

# catigorize columns
columns = [c for c in df.columns]
discrete = [x for x in columns if df[x].dtype == object]
discrete_colorable = [x for x in discrete if len(df[x].unique()) <= max(len(df["grp"].unique()),
                                                                        len(df["assign"].unique()))]
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

#####################
# initialize sources #
#####################

source = create_source()
source.on_change('selected', selection_change)
table_source = ColumnDataSource(df)

########################
# javascript callbacks #
########################

download_callback = CustomJS(args=dict(table_source=table_source), code=r"""
        var data = table_source.data;
        var columns = %s;
        var n = columns.length;
        var m = data[columns[0]].length;

        var csvLines = [];

        var currRow = [];
        for (j=0; j<n; j++) {
            currRow.push("\"" + columns[j].toString() + "\"");
        }

        csvLines.push(currRow.join(","));

        for (i=0; i < m; i++) {
            var currRow = [];
            for (j=0; j<n; j++) {
                if (typeof(data[columns[j]][i]) == 'string') {
                    currRow.push("\"" + data[columns[j]][i].toString() + "\"");
                } else {
                    currRow.push(data[columns[j]][i].toString());
                }
            }
            csvLines.push(currRow.join(","));
        }

        var filetext = csvLines.join("\n");

        var filename = 'data_result.csv';
        var blob = new Blob([filetext], { type: 'text/csv;charset=utf-8;' });

        //addresses IE
        if (navigator.msSaveBlob) {
            navigator.msSaveBlob(blob, filename);
        }

        else {
            var link = document.createElement("a");
            link = document.createElement('a')
            link.href = URL.createObjectURL(blob);
            link.download = filename
            link.target = "_blank";
            link.style.visibility = 'hidden';
            link.dispatchEvent(new MouseEvent('click'))
        }
    """ % json.dumps([x for x in columns if x not in {"easting", "northing"}]))

jitter_callback = CustomJS(args=dict(source=source, map_jitter=Jitter()), code=r"""
        var data = source.data;
        if (slider.value == 0) {
            for (var i = 0; i < data['easting'].length; i++) {
                data['es'][i] = data['easting'][i];
            }
            for (var i = 0; i < data['northing'].length; i++) {
                data['ns'][i] = data['northing'][i];
            }
        }

        else {
            map_jitter.distribution = dist.value
            map_jitter.width = slider.value * 1000
            for (var i = 0; i < data['easting'].length; i++) {
                data['es'][i] = map_jitter.compute(data['easting'][i]);
            }
            for (var i = 0; i < data['northing'].length; i++) {
                data['ns'][i] = map_jitter.compute(data['northing'][i]);
            }
        }
        source.trigger('change');
    """)

download_button = Button(label="Download", button_type="success", callback=download_callback)

jitter_selector = Select(title="Map Jitter Distribution:", value="uniform",
                      options=["uniform", "normal"], callback=jitter_callback)

jitter_slider = Slider(start=0, end=1000, value=0, step=10,
                           title="Map Jitter Width (Km):", callback=jitter_callback)

jitter_callback.args["dist"] = jitter_selector
jitter_callback.args["slider"] = jitter_slider

# initialize plots
crossfilter = create_crossfilter(source)
map = create_map(source)

# create layout
controls = widgetbox([x, y, color, size, jitter_selector, jitter_slider, download_button], width=200)
table = widgetbox(create_table([col for col in columns if ("LD" not in col) and (col not in ["northing", "easting"])], table_source))
l = layout([
    [controls, crossfilter, map],
    [row(table)]
])

# add layout to document
curdoc().add_root(l)
curdoc().title = "Crossfilter"
