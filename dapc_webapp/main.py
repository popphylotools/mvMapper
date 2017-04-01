import copy
import pandas as pd
from bokeh.layouts import row, widgetbox, layout
from bokeh.models import Select, CustomJS, Jitter, DataTable, TableColumn, Slider, Button
# noinspection PyUnresolvedReferences
from bokeh.palettes import linear_palette
from bokeh.plotting import curdoc, figure, ColumnDataSource
from bokeh.tile_providers import STAMEN_TERRAIN
import colorcet as cc
import pyproj
import json

max_discrete_colors = 255
SIZES = list(range(6, 22, 3))

# wont
force_discrete_colorable = ["grp", "assign"]

# define available palettes
palettes = {k: v for k, v in cc.palette.items() if
            ("_" not in k and
             k not in ["bkr", "coolwarm", "bjy", "bky", "gwv"])}

# data path
dataPath = "data/webapp_input.csv"


##################
# data handling #
##################

def get_data(path):
    """Read data from csv and transform map coordinates.
    :param path:
    :return:
    """
    data = pd.read_csv(path)

    for col in data.columns:
        if col in force_discrete_colorable:
            data[col] = data[col].apply(str)

    data = data.applymap(lambda x: "NaN" if pd.isnull(x) else x)

    # transform coords to map projection
    wgs84 = pyproj.Proj(init="epsg:4326")
    web_mer = pyproj.Proj(init="epsg:3857")
    data["easting"] = "NaN"
    data["northing"] = "NaN"
    data["easting"] = data["easting"].astype("float64")
    data["northing"] = data["northing"].astype("float64")
    data.loc[pd.notnull(data["Lng"]), "easting"], data.loc[pd.notnull(data["Lat"]), "northing"] = zip(
        *data.loc[pd.notnull(data["Lng"]) & pd.notnull(data["Lat"])].apply(
            lambda x: pyproj.transform(wgs84, web_mer, x["Lng"], x["Lat"]), axis=1))

    # show unknown locations on map in antartic
    data.northing = data.northing.apply(lambda x: -15000000 if pd.isnull(x) else x)
    data.easting = data.easting.apply(lambda x: 0 if pd.isnull(x) else x)

    return data


def update_df(_df, _size, _color, _palette, _continuous, _discrete_sizeable, _discrete_colorable):
    """
    :param _df:
    :param _size:
    :param _color:
    :param _palette:
    :param _continuous:
    :param _discrete_sizeable:
    :param _discrete_colorable:
    """
    _df["size"] = 9
    if _size != 'None' and _size in _discrete_sizeable:
        values = _df[_size][pd.notnull(_df[_size])].unique()
        if all([val.isnumeric() for val in values]):
            values = sorted(values, key=lambda x: float(x))
        codes = dict(zip(values, range(len(values))))
        groups = [codes[val] for val in _df[_size].values]
        _df["size"] = [SIZES[xx] for xx in groups]
    elif _size != 'None' and _size in _continuous:
        try:
            groups = pd.qcut(_df[_size].values, len(SIZES))
        except ValueError:
            groups = pd.cut(_df[_size].values, len(SIZES))
        _df["size"] = [SIZES[xx] for xx in groups.codes]

    _df["color"] = "#31AADE"
    if _color != 'None' and _color in _discrete_colorable:
        values = _df[_color][pd.notnull(_df[_color])].unique()
        colors = linear_palette(palettes[_palette], len(values))
        if all([val.isnumeric() for val in values]):
            values = sorted(values, key=lambda x: float(x))
        codes = dict(zip(values, range(len(values))))
        groups = [codes[val] for val in _df[_color].values]
        _df["color"] = [colors[xx] for xx in groups]
    elif _color != 'None' and _color in _continuous:
        # colors = linear_palette(palettes[_palette], max_discrete_colors)
        # try:
        #     groups = pd.qcut(_df[_color].values, len(colors))
        # except ValueError:
        colors = palettes[_palette]
        groups = pd.cut(_df[_color].values, len(colors))
        _df["color"] = [colors[xx] for xx in groups.codes]


def create_source(_df, _size, _color, _palette, _continuous, _discrete_sizeable, _discrete_colorable):
    """Return new ColumnDataSource.
    :param _color:
    :param _palette:
    :param _continuous:
    :param _discrete_sizeable:
    :param _discrete_colorable:
    :param _size:
    :param _df:
    :return:
    """
    update_df(_df, _size, _color, _palette, _continuous, _discrete_sizeable, _discrete_colorable)

    _df["ns"] = _df["northing"]
    _df["es"] = _df["easting"]

    # create a ColumnDataSource from the  data set
    return ColumnDataSource(_df)


def update_source(_source, _df, _size, _color, _palette, _continuous, _discrete_sizeable, _discrete_colorable):
    """Update `size` and `color` columns of ColumnDataSource _source to reflect widget selections
    :param _size:
    :param _color:
    :param _palette:
    :param _continuous:
    :param _discrete_sizeable:
    :param _discrete_colorable:
    :param _source:
    :param _df:
    """
    update_df(_df, _size, _color, _palette, _continuous, _discrete_sizeable, _discrete_colorable)

    # create a ColumnDataSource from the  data set
    _source.data.update({"size": _df["size"], "color": _df["color"]})


#######################
# Data Visualizations #
#######################

def create_crossfilter(_df, _source, _discrete, _x, _y):
    """Return a crossfilter plot linked to ColumnDataSource _source
    :param _df:
    :param _source:
    :param _discrete:
    :param _x:
    :param _y:
    :return:
    """
    kw = dict()
    if _x in _discrete:
        values = _df[_x][pd.notnull(_df[_x])].unique()
        if all([val.isnumeric() for val in values]):
            kw["x_range"] = sorted(values, key=lambda x: float(x))
        else:
            kw["x_range"] = sorted(values)
    if _y in _discrete:
        values = _df[_y][pd.notnull(_df[_y])].unique()
        if all([val.isnumeric() for val in values]):
            kw["y_range"] = sorted(values, key=lambda x: float(x))
        else:
            kw["y_range"] = sorted(values)

    x_title = _x.title()
    y_title = _y.title()

    p = figure(plot_height=700, plot_width=700,  # responsive=True,
               tools="wheel_zoom, pan, save, reset, box_select, tap",
               active_drag="box_select", active_scroll="wheel_zoom",
               title="%s vs %s" % (y_title, x_title),
               **kw, )

    if _x in _discrete:
        p.xaxis.major_label_orientation = pd.np.pi / 4

    # plot data on crossfilter
    p.circle(x=_x, y=_y, color="color", size="size", source=_source, line_color="white",
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
             nonselection_line_alpha=0.6, )

    return p


def create_map(_source):
    """Return map linked to ColumnDataSource '_source'.
    :param _source:
    :return:
    """
    stamen = copy.copy(STAMEN_TERRAIN)
    # create map
    bound = 20000000  # meters
    m = figure(plot_height=700, plot_width=700,  # responsive=True,
               tools="wheel_zoom, pan, reset, box_select, tap",
               active_drag="box_select", active_scroll="wheel_zoom",
               x_range=(-bound, bound), y_range=(-bound, bound))
    m.axis.visible = False
    m.add_tile(stamen)

    # plot data on world map
    m.circle(x="es", y="ns", color="color", size="size", source=_source, line_color="white",
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
             nonselection_line_alpha=0.6, )

    return m


def create_table(_columns, _source):
    """Return table linked to ColumnDataSource '_source'.
    :param _columns:
    :param _source:
    :return:
    """
    table_cols = [TableColumn(field=col, title=col) for col in _columns]
    return DataTable(source=_source, columns=table_cols, width=1600, height=250, fit_columns=False, )


#############
# callbacks #
#############

def x_change(attr, old, new):
    """Replece crossfilter plot."""
    l.children[0].children[1] = create_crossfilter(df, source, discrete, x.value, y.value)


def y_change(attr, old, new):
    """Replece crossfilter plot."""
    l.children[0].children[1] = create_crossfilter(df, source, discrete, x.value, y.value)


def size_change(attr, old, new):
    """Update ColumnDataSource 'source'."""
    update_source(source, df, size.value, color.value, palette.value, continuous, discrete_sizeable, discrete_colorable)


def color_change(attr, old, new):
    """Update ColumnDataSource 'source'."""
    update_source(source, df, size.value, color.value, palette.value, continuous, discrete_sizeable, discrete_colorable)


def selection_change(attr, old, new):
    """Update ColumnDataSource 'table_source' with selection found in 'source'."""
    selected = source.selected['1d']['indices']
    table_source.data = table_source.from_df(df.iloc[selected, :])


def palette_change(attr, old, new):
    """Update ColumnDataSource 'source'."""
    update_source(source, df, size.value, color.value, palette.value, continuous, discrete_sizeable, discrete_colorable)


########
# Main #
########

# load data
df = get_data(dataPath)

# catigorize columns
columns = [c for c in df.columns if c not in {"easting", "northing"}]
discrete = [x for x in columns if df[x].dtype == object]
continuous = [x for x in columns if x not in discrete]
discrete_sizeable = [x for x in discrete if len(df[x].unique()) <= len(SIZES)]
discrete_colorable = [x for x in discrete if (len(df[x].unique()) <= max_discrete_colors) or
                      ((x in force_discrete_colorable) and (len(df[x].unique()) < 256))]

# create widgets
if 'LD1' in columns:
    x = Select(title='X-Axis', value='LD1', options=columns)
else:
    x = Select(title='X-Axis', value=columns[0], options=columns)
x.on_change('value', x_change)

if 'LD2' in columns:
    y = Select(title='Y-Axis', value='LD2', options=columns)
else:
    y = Select(title='Y-Axis', value=columns[1], options=columns)
y.on_change('value', y_change)

if 'posterior_assign' in columns:
    size = Select(title='Size', value='posterior_assign', options=['None'] + discrete_sizeable + continuous)
else:
    size = Select(title='Size', value='None', options=['None'] + discrete_sizeable + continuous)
size.on_change('value', size_change)

if 'assign' in columns:
    color = Select(title='Color', value='assign', options=['None'] + discrete_colorable + continuous)
else:
    color = Select(title='Color', value='None', options=['None'] + discrete_colorable + continuous)
color.on_change('value', color_change)

palette = Select(title='Palette', value="inferno", options=[k for k in palettes.keys()])
palette.on_change('value', palette_change)

#####################
# initialize sources #
#####################

source = create_source(df, size.value, color.value, palette.value, continuous, discrete_sizeable, discrete_colorable)
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
            link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = filename;
            link.target = "_blank";
            link.style.visibility = 'hidden';
            link.dispatchEvent(new MouseEvent('click'));
        }
    """ % json.dumps(columns))

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

download_button = Button(label="Download Selected", button_type="success", callback=download_callback)

jitter_selector = Select(title="Map Jitter Distribution:", value="uniform",
                         options=["uniform", "normal"], callback=jitter_callback)

jitter_slider = Slider(start=0, end=1000, value=0, step=10,
                       title="Map Jitter Width (Km):", callback=jitter_callback)

jitter_callback.args["dist"] = jitter_selector
jitter_callback.args["slider"] = jitter_slider

# initialize plots
crossfilter = create_crossfilter(source, source, discrete, x.value, y.value)
mapPlot = create_map(source)

# create layout
controls = widgetbox([x, y, color, palette, size, jitter_selector, jitter_slider, download_button], width=200)
table = widgetbox(create_table([col for col in columns if ("LD" not in col)], table_source))
l = layout([
    [controls, crossfilter, mapPlot],
    [row(table)]
])

# add layout to document
curdoc().add_root(l)
curdoc().title = "Crossfilter"
