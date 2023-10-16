import os
import logging
import datetime
import pandas as pd
import shapely.geometry
import geopandas as gpd
import re
import io
from zipfile import ZipFile

__version__ = "0.0.5"

logger = logging.getLogger(__name__)


REQUIRED_GTFS_FILES = [
    'agency',
    'stops',
    'routes',
    'trips',
    'calendar',
    'stop_times',
    # 'shapes',
    # 'frequencies',
    # 'feedinfo'
]

# https://developers.google.com/transit/gtfs/reference
AVAILABLE_GTFS_FILES = [
    "agency",
    "stops",
    "routes",
    "trips",
    "stop_times",
    "calendar",
    "calendar_dates",
    "fare_attributes",
    "fare_rules",
    "shapes",
    "frequencies",
    "transfers",
    "pathways",
    "levels",
    "feed_info",
    "translations",
    "attributions"
]

ROUTE_TYPE_MAP = {
    0: 'tram, light_rail',
    1: 'subway',
    2: 'rail, railway, train',
    3: 'bus, ex-bus',
    4: 'ferry',
    5: 'cableCar',
    6: 'gondola',
    7: 'funicular'
}

COLUMNS_DEPENDENCY_DICT = {
    'agency':   ('agency_id',  ['routes']),
    'routes':   ('route_id',   ['trips']),
    'trips':    ('trip_id',    ['stop_times']),
    'stops':    ('stop_id',    ['stop_times']),
    'calendar': ('service_id', ['calendar_dates']),
    'shapes':   ('shape_id',   ['trips'])
}


def replace_line_breaks_in_quotes(text: str) -> io.StringIO:
    def fix(match): return re.sub(r'\r?\n', " ", match[0])
    return io.StringIO(re.sub(r'"([^"]+)"', fix, text))


def load_gtfs(filepath, subset=None):
    df_dict = {}
    buffer: io.StringIO

    if os.path.isdir(filepath):
        for filename in os.listdir(filepath):
            filekey = filename.split('.txt')[0]
            if (subset is None) or (filekey in subset):
                try:
                    fname = os.path.join(filepath, filename)

                    with open(fname, 'r') as f:
                        buffer = replace_line_breaks_in_quotes(f.read())

                    df_dict[filekey] = pd.read_csv(buffer, low_memory=False)
                except Exception as e:
                    logger.error(
                        f"[{e.__class__.__name__}] {e} for {filename}")
    else:
        with ZipFile(filepath) as z:
            for filename in z.namelist():
                filekey = filename.split('.txt')[0]
                if (subset is None) or (filekey in subset):
                    try:
                        # with z.open(filename) as f:
                        #     buffer = replace_line_breaks_in_quotes(
                        #         f.read().decode())

                        df_dict[filekey] = pd.read_csv(
                            z.open(filename), low_memory=False)
                    except Exception as e:
                        logger.error(
                            f"[{e.__class__.__name__}] {e} for {filename}")

    return df_dict


def load_stops(src):
    if isinstance(src, str):
        df_dict = load_gtfs(src, subset=['stops'])
    elif isinstance(src, dict):
        df_dict = src
    else:
        raise ValueError(
            f"Data type not supported: {type(src)}")

    stops = df_dict['stops'].copy()
    geoms = gpd.points_from_xy(stops.stop_lon, stops.stop_lat)

    return gpd.GeoDataFrame(
        stops, geometry=geoms, crs="EPSG:4326")


def load_shapes(src, geom_type='linestring'):
    if isinstance(src, str):
        df_dict = load_gtfs(src, subset=['shapes'])
    elif isinstance(src, dict):
        df_dict = src
    else:
        raise ValueError(
            f"Data type not supported: {type(src)}")

    if 'shapes' not in df_dict:
        raise ValueError("shapes.txt not found in GTFS")

    if geom_type == 'linestring':
        items = []
        for shape_id, g in df_dict['shapes'].groupby('shape_id'):
            g = g.sort_values('shape_pt_sequence')
            coords = g[['shape_pt_lon', 'shape_pt_lat']].values

            if len(coords) > 1:
                items.append({
                    'shape_id': shape_id,
                    'geom': shapely.geometry.LineString(coords)
                })

        gdf = gpd.GeoDataFrame(items, geometry='geom', crs="EPSG:4326")

    elif geom_type == 'point':
        shapes = df_dict['shapes'].copy()
        geoms = gpd.points_from_xy(shapes.shape_pt_lon, shapes.shape_pt_lat)

        gdf = gpd.GeoDataFrame(shapes, geometry=geoms, crs="EPSG:4326")

    else:
        raise ValueError(
            f"Geometry type {geom_type} not supported!")

    return gdf


def save_gtfs(df_dict, filepath, ignore_required=False, overwrite=False):
    if not ignore_required and not all(key in df_dict.keys()
                                       for key in REQUIRED_GTFS_FILES):
        raise ValueError("Not all required GTFS files in dictionary")

    if overwrite or not os.path.exists(filepath):
        with ZipFile(filepath, "w") as zf:
            for filekey, df in df_dict.items():
                buffer = df.to_csv(index=False)
                zf.writestr(filekey + ".txt", buffer)


def get_bounding_box(src):
    if isinstance(src, str):
        df_dict = load_gtfs(src, subset=['stops'])
    elif isinstance(src, dict):
        df_dict = src
    else:
        raise ValueError(
            f"Data type not supported: {type(src)}")

    return [
        df_dict['stops']['stop_lon'].min(),
        df_dict['stops']['stop_lat'].min(),
        df_dict['stops']['stop_lon'].max(),
        df_dict['stops']['stop_lat'].max()
    ]


def get_calendar_date_range(src):
    if isinstance(src, str):
        df_dict = load_gtfs(src, subset=['calendar'])
    elif isinstance(src, dict):
        df_dict = src
    else:
        raise ValueError(
            f"Data type not supported: {type(src)}")

    if "calendar" in df_dict:
        min_date = min(
            df_dict['calendar']['start_date'].min(),
            df_dict['calendar']['end_date'].min())
        max_date = max(
            df_dict['calendar']['start_date'].max(),
            df_dict['calendar']['end_date'].max())
        min_date = datetime.datetime.strptime(str(min_date), "%Y%m%d")
        max_date = datetime.datetime.strptime(str(max_date), "%Y%m%d")
    else:
        raise ValueError("calendar.txt missing")

    return min_date, max_date


def print_info(src):
    if isinstance(src, str):
        df_dict = load_gtfs(src)
    elif isinstance(src, dict):
        df_dict = src
    else:
        raise ValueError(
            f"Data type not supported: {type(src)}")

    print("\nGTFS files:")
    for key in sorted(df_dict.keys()):
        print(f"  {key + '.txt':<20s} {len(df_dict[key]):12,d} rows")

    min_date, max_date = get_calendar_date_range(df_dict)
    print("\nCalender date range:\n  "
          f"{min_date.strftime('%d.%m.%Y')} - "
          f"{max_date.strftime('%d.%m.%Y')}")

    bounds = get_bounding_box(df_dict)
    print(f"\nBounding box:\n  {bounds}\n")
