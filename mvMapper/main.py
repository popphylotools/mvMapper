from jinja2 import Environment, FileSystemLoader
import yaml

from tornado.ioloop import IOLoop
from tornado.web import RequestHandler

from bokeh.application import Application
from bokeh.application.handlers import FunctionHandler
from bokeh.embed import autoload_server
from bokeh.server.server import Server
from bokeh.themes import Theme


import copy
import json
import pytoml

import colorcet as cc
import pandas as pd
import pyproj
from bokeh.layouts import row, widgetbox, layout
from bokeh.models import Select, CustomJS, Jitter, DataTable, TableColumn, Slider, Button
# noinspection PyUnresolvedReferences
from bokeh.palettes import linear_palette
from bokeh.plotting import figure, ColumnDataSource
from bokeh.tile_providers import STAMEN_TERRAIN


env = Environment(loader=FileSystemLoader('templates'))

class IndexHandler(RequestHandler):
    def get(self):
        template = env.get_template('embed.html')
        script = autoload_server(model=None, url='http://localhost:5006/bkapp')
        self.write(template.render(script=script, template="Tornado"))

def modify_doc(doc):
    SIZES = list(range(6, 22, 3))

    # define available palettes
    palettes = {k: v for k, v in cc.palette.items() if
                ("_" not in k and
                 k not in ["bkr", "coolwarm", "bjy", "bky", "gwv"])}

    # config file
    configPath = "config/config.toml"

    ##################
    # data handling #
    ##################

    def get_data(path, force_discrete_colorable):
        """Read data from csv and transform map coordinates."""
        data = pd.read_csv(path)

        # data from columns in force_discrete_colorable will be treated as discrete even if numeric
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
        data.loc[pd.notnull(data["lon"]), "easting"], data.loc[pd.notnull(data["lat"]), "northing"] = zip(
            *data.loc[pd.notnull(data["lon"]) & pd.notnull(data["lat"])].apply(
                lambda x: pyproj.transform(wgs84, web_mer, x["lon"], x["lat"]), axis=1))

        # show unknown locations on map in antarctic
        default_coords = config.get('default_coords') or {'lon': 0, 'lat': -80}

        data.northing = data.northing.apply(lambda x: pyproj.transform(wgs84, web_mer, ) if pd.isnull(x) else x)
        data.easting = data.easting.apply(lambda x: 0 if pd.isnull(x) else x)

        return data

    def update_df(_df, _size, _color, _palette, _continuous, _discrete_sizeable, _discrete_colorable):
        """update the size and color columns of the given df based on widget selections and column classifications"""
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
            colors = palettes[_palette]
            groups = pd.cut(_df[_color].values, len(colors))
            _df["color"] = [colors[xx] for xx in groups.codes]

    def create_source(_df, _size, _color, _palette, _continuous, _discrete_sizeable, _discrete_colorable):
        """Update df and return new ColumnDataSource."""
        update_df(_df, _size, _color, _palette, _continuous, _discrete_sizeable, _discrete_colorable)

        _df["ns"] = _df["northing"]
        _df["es"] = _df["easting"]

        # create a ColumnDataSource from the  data set
        return ColumnDataSource(_df)

    def update_source(_source, _df, _size, _color, _palette, _continuous, _discrete_sizeable, _discrete_colorable):
        """update df and and propagate changes to source"""
        update_df(_df, _size, _color, _palette, _continuous, _discrete_sizeable, _discrete_colorable)

        # create a ColumnDataSource from the  data set
        _source.data.update({"size": _df["size"], "color": _df["color"]})

    #######################
    # Data Visualizations #
    #######################

    def create_crossfilter(_df, _source, _discrete, _x, _y):
        """Return a crossfilter plot linked to ColumnDataSource '_source'."""
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
        """Return map linked to ColumnDataSource '_source'."""
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
        """Return table linked to ColumnDataSource '_source'."""
        table_cols = [TableColumn(field=col, title=col) for col in _columns]
        return DataTable(source=_source, columns=table_cols, width=1600, height=250, fit_columns=False, )

    #############
    # callbacks #
    #############

    # noinspection PyUnusedLocal
    def x_change(attr, old, new):
        """Replece crossfilter plot."""
        l.children[0].children[1] = create_crossfilter(df, source, discrete, x.value, y.value)

    # noinspection PyUnusedLocal
    def y_change(attr, old, new):
        """Replece crossfilter plot."""
        l.children[0].children[1] = create_crossfilter(df, source, discrete, x.value, y.value)

    # noinspection PyUnusedLocal
    def size_change(attr, old, new):
        """Update ColumnDataSource 'source'."""
        update_source(source, df, size.value, color.value, palette.value, continuous, discrete_sizeable,
                      discrete_colorable)

    # noinspection PyUnusedLocal
    def color_change(attr, old, new):
        """Update ColumnDataSource 'source'."""
        update_source(source, df, size.value, color.value, palette.value, continuous, discrete_sizeable,
                      discrete_colorable)

    # noinspection PyUnusedLocal
    def selection_change(attr, old, new):
        """Update ColumnDataSource 'table_source' with selection found in 'source'."""
        selected = source.selected['1d']['indices']
        table_source.data = table_source.from_df(df.iloc[selected, :])

    # noinspection PyUnusedLocal
    def palette_change(attr, old, new):
        """Update ColumnDataSource 'source'."""
        update_source(source, df, size.value, color.value, palette.value, continuous, discrete_sizeable,
                      discrete_colorable)

    ########
    # Main #
    ########

    # load config file
    with open(configPath) as toml_data:
        config = pytoml.load(toml_data)

    # load data
    df = get_data(config["dataPath"], config["force_discrete_colorable"])

    # catigorize columns
    columns = [c for c in df.columns if c not in {"easting", "northing"}]
    discrete = [x for x in columns if df[x].dtype == object]
    continuous = [x for x in columns if x not in discrete]
    discrete_sizeable = [x for x in discrete if len(df[x].unique()) <= len(SIZES)]
    discrete_colorable = [x for x in discrete if (len(df[x].unique()) <= config["max_discrete_colors"]) or
                          ((x in config["force_discrete_colorable"]) and (len(df[x].unique()) < 256))]

    # create widgets
    x = Select(title='X-Axis',
               value=(config.get("default_xAxis") if config.get("default_yAxis") in columns else columns[1]),
               options=columns)
    x.on_change('value', x_change)

    y = Select(title='Y-Axis',
               value=(config.get("default_yAxis") if config.get("default_yAxis") in columns else columns[2]),
               options=columns)
    y.on_change('value', y_change)

    sizeOptions = ['None'] + discrete_sizeable + continuous
    size = Select(title='Size',
                  value=(config.get("default_sizeBy") if config.get("default_yAxis") in sizeOptions else 'None'),
                  options=sizeOptions)
    size.on_change('value', size_change)

    colorOptions = ['None'] + discrete_colorable + continuous
    color = Select(title='Color',
                   value=(config.get("default_colorBy") if config.get("default_yAxis") in colorOptions else 'None'),
                   options=colorOptions)
    color.on_change('value', color_change)

    palleteOptions = [k for k in palettes.keys()]
    palette = Select(title='Palette',
                     value=(
                     config.get("default_palette") if config.get("default_yAxis") in palleteOptions else "inferno"),
                     options=palleteOptions)
    palette.on_change('value', palette_change)

    #####################
    # initialize sources #
    #####################

    source = create_source(df, size.value, color.value, palette.value, continuous, discrete_sizeable,
                           discrete_colorable)
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
    crossfilter = create_crossfilter(df, source, discrete, x.value, y.value)
    mapPlot = create_map(source)

    # create layout
    controls = widgetbox([x, y, color, palette, size, jitter_selector, jitter_slider, download_button], width=200)
    table = widgetbox(create_table(columns, table_source))
    l = layout([
        [controls, crossfilter, mapPlot],
        [row(table)]
    ])

    # add layout to document
    doc.add_root(l)
    doc.title = "Crossfilter"

    doc.theme = Theme(json=yaml.load("""
        attrs:
            Figure:
                background_fill_color: '#2F2F2F'
                border_fill_color: '#2F2F2F'
                outline_line_color: '#444444'
            Axis:
                axis_line_color: "white"
                axis_label_text_color: "white"
                major_label_text_color: "white"
                major_tick_line_color: "white"
                minor_tick_line_color: "white"
                minor_tick_line_color: "white"
            Grid:
                grid_line_dash: [6, 4]
                grid_line_alpha: .3
            Title:
                text_color: "white"
    """))

bokeh_app = Application(FunctionHandler(modify_doc))

io_loop = IOLoop.current()

server = Server({'/bkapp': bokeh_app}, io_loop=io_loop, extra_patterns=[('/', IndexHandler)])
server.start()

if __name__ == '__main__':
    from bokeh.util.browser import view

    print('Opening Tornado app with embedded Bokeh application on http://localhost:5006/')

    io_loop.add_callback(view, "http://localhost:5006/")
    io_loop.start()
