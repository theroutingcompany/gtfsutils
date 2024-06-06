import numpy as np
import shapely

from . import load_shapes, load_stops


def spatial_filter_by_stops(df_dict, filter_geometry):
    if isinstance(filter_geometry, list) or \
       isinstance(filter_geometry, np.ndarray):
        if len(filter_geometry) != 4:
            raise ValueError("Wrong dimension of bounds")
        geom = shapely.geometry.box(*filter_geometry)  # type: ignore
    elif isinstance(filter_geometry, shapely.geometry.base.BaseGeometry):  # type: ignore
        geom = filter_geometry
    else:
        raise ValueError(
            f"filter_geometry type {type(filter_geometry)} not supported!")

    # Filter stops.
    gdf_stops = load_stops(df_dict)
    mask = gdf_stops.intersects(geom)

    gdf_stops = gdf_stops[mask]
    stop_ids = gdf_stops['stop_id'].values
    filter_by_stop_ids(df_dict, stop_ids)

    # Subset shapes.
    if 'shapes' in df_dict:
        gdf_shapes = load_shapes(df_dict, geom_type='point')
        mask = gdf_shapes.intersects(geom)
        df_dict['shapes'] = df_dict['shapes'][mask]


def filter_by_stop_ids(df_dict, stop_ids):
    if not isinstance(stop_ids, list) and \
       not isinstance(stop_ids, np.ndarray):
        stop_ids = [stop_ids]

    # Filter stops.txt
    mask = df_dict['stops']['stop_id'].isin(stop_ids)
    df_dict['stops'] = df_dict['stops'][mask]

    # Filter stop_times.txt
    mask = df_dict['stop_times']['stop_id'].isin(stop_ids)
    df_dict['stop_times'] = df_dict['stop_times'][mask]

    # Filter trips.txt
    trip_ids = df_dict['stop_times']['trip_id'].values
    mask = df_dict['trips']['trip_id'].isin(trip_ids)
    df_dict['trips'] = df_dict['trips'][mask]

    direction_col_name = 'direction_id'
    if 'trip_direction_name' in df_dict['trips']:
        direction_col_name = 'trip_direction_name'

    df_dict['trips'][direction_col_name].fillna(0, inplace=True)

    # Filter route.txt
    route_ids = df_dict['trips']['route_id'].values
    mask = df_dict['routes']['route_id'].isin(route_ids)
    df_dict['routes'] = df_dict['routes'][mask]

    # Filter agency.txt
    agency_ids = df_dict['routes']['agency_id'].values
    mask = df_dict['agency']['agency_id'].isin(agency_ids)
    df_dict['agency'] = df_dict['agency'][mask]

    # Filter shapes.txt
    if 'shapes' in df_dict:
        shape_ids = df_dict['trips']['shape_id'].values
        mask = df_dict['shapes']['shape_id'].isin(shape_ids)
        df_dict['shapes'] = df_dict['shapes'][mask]

    # Filter calendar.txt
    if 'calendar' in df_dict:
        service_ids = df_dict['trips']['service_id'].values
        mask = df_dict['calendar']['service_id'].isin(service_ids)
        df_dict['calendar'] = df_dict['calendar'][mask]

    # Filter calendar_dates.txt
    if 'calendar_dates' in df_dict:
        service_ids = df_dict['trips']['service_id'].values
        mask = df_dict['calendar_dates']['service_id'].isin(service_ids)
        df_dict['calendar_dates'] = df_dict['calendar_dates'][mask]

    # Filter frequencies.txt
    if 'frequencies' in df_dict:
        mask = df_dict['frequencies']['trip_id'].isin(trip_ids)
        df_dict['frequencies'] = df_dict['frequencies'][mask]

    # Filter transfers.txt
    if 'transfers' in df_dict:
        mask = df_dict['transfers']['from_stop_id'].isin(stop_ids) \
            & df_dict['transfers']['to_stop_id'].isin(stop_ids)
        df_dict['transfers'] = df_dict['transfers'][mask]

    # Filter fare_rules.txt
    if 'fare_rules' in df_dict:
        route_ids = df_dict['routes']['route_id'].values
        mask = df_dict['fare_rules']['route_id'].isin(route_ids)
        df_dict['fare_rules'] = df_dict['fare_rules'][mask]

        # Filter fare_attributes.txt if fare_rules.txt is provided
        if 'fare_attributes' in df_dict:
            fare_ids = df_dict['fare_rules']['fare_id'].values
            mask = df_dict['fare_attributes']['fare_id'].isin(fare_ids)
            df_dict['fare_attributes'] = df_dict['fare_attributes'][mask]

    # Filter pathways.txt
    if 'pathways' in df_dict:
        mask = df_dict['pathways']['from_stop_id'].isin(stop_ids) \
            & df_dict['pathways']['to_stop_id'].isin(stop_ids)
        df_dict['pathways'] = df_dict['pathways'][mask]

    # Filter calendar_attributes.txt
    if 'calendar_attributes' in df_dict:
        mask = df_dict['calendar_attributes']['service_id'].isin(service_ids)
        df_dict['calendar_attributes'] = df_dict['calendar_attributes'][mask]

    # Filter route_attributes.txt
    if 'route_attributes' in df_dict:
        mask = df_dict['route_attributes']['route_id'].isin(route_ids)
        df_dict['route_attributes'] = df_dict['route_attributes'][mask]

    # Filter stop_areas.txt
    if 'stop_areas' in df_dict:
        mask = df_dict['stop_areas']['stop_id'].isin(stop_ids)
        df_dict['stop_areas'] = df_dict['stop_areas'][mask]


def spatial_filter_by_shapes(df_dict, filter_geometry, operation='within'):
    if isinstance(filter_geometry, list) or \
       isinstance(filter_geometry, np.ndarray):
        if len(filter_geometry) != 4:
            raise ValueError("Wrong dimension of bounds")
        geom = shapely.geometry.box(*filter_geometry)  # type: ignore
    elif isinstance(filter_geometry, shapely.geometry.base.BaseGeometry):  # type: ignore
        geom = filter_geometry
    else:
        raise ValueError(
            f"filter_geometry type {type(filter_geometry)} not supported!")

    # Filter shapes
    gdf_shapes = load_shapes(df_dict)
    if operation == 'within':
        mask = gdf_shapes.within(geom)
    elif operation == 'intersects':
        mask = gdf_shapes.intersects(geom)
    else:
        raise ValueError(
            f"Operation {operation} not supported!")

    gdf_shapes = gdf_shapes[mask]
    shape_ids = gdf_shapes['shape_id'].values
    filter_by_shape_ids(df_dict, shape_ids)


def filter_by_shape_ids(df_dict, shape_ids):
    if not isinstance(shape_ids, list) and \
       not isinstance(shape_ids, np.ndarray):
        shape_ids = [shape_ids]

    # Filter shapes.txt
    mask = df_dict['shapes']['shape_id'].isin(shape_ids)
    df_dict['shapes'] = df_dict['shapes'][mask]

    # Filter trips.txt
    mask = df_dict['trips']['shape_id'].isin(shape_ids)
    df_dict['trips'] = df_dict['trips'][mask]

    # Filter route.txt
    route_ids = df_dict['trips']['route_id'].values
    mask = df_dict['routes']['route_id'].isin(route_ids)
    df_dict['routes'] = df_dict['routes'][mask]
    df_dict['routes']['route_short_name'] = df_dict['routes']['route_short_name'] \
        .astype(str)
    df_dict['routes']['route_long_name'] = df_dict['routes']['route_long_name'] \
        .astype(str)

    # Filter agency.txt
    agency_ids = df_dict['routes']['agency_id'].values
    mask = df_dict['agency']['agency_id'].isin(agency_ids)
    df_dict['agency'] = df_dict['agency'][mask]

    # Filter stop_times.txt
    trip_ids = df_dict['trips']['trip_id'].values
    mask = df_dict['stop_times']['trip_id'].isin(trip_ids)
    df_dict['stop_times'] = df_dict['stop_times'][mask]

    # Filter stops.txt
    stop_ids = df_dict['stop_times']['stop_id'].values
    mask = df_dict['stops']['stop_id'].isin(stop_ids)
    df_dict['stops'] = df_dict['stops'][mask]

    # Filter calendar.txt
    if 'calendar' in df_dict:
        service_ids = df_dict['trips']['service_id'].values
        mask = df_dict['calendar']['service_id'].isin(service_ids)
        df_dict['calendar'] = df_dict['calendar'][mask]

    # Filter calendar_dates.txt
    if 'calendar_dates' in df_dict:
        service_ids = df_dict['trips']['service_id'].values
        mask = df_dict['calendar_dates']['service_id'].isin(service_ids)
        df_dict['calendar_dates'] = df_dict['calendar_dates'][mask]

    # Filter frequencies.txt
    if 'frequencies' in df_dict:
        mask = df_dict['frequencies']['trip_id'].isin(trip_ids)
        df_dict['frequencies'] = df_dict['frequencies'][mask]

    # Filter transfers.txt
    if 'transfers' in df_dict:
        mask = df_dict['transfers']['from_stop_id'].isin(stop_ids) \
            & df_dict['transfers']['to_stop_id'].isin(stop_ids)
        df_dict['transfers'] = df_dict['transfers'][mask]


def filter_by_agency_ids(df_dict, agency_ids):
    if not isinstance(agency_ids, list) and \
       not isinstance(agency_ids, np.ndarray):
        agency_ids = [agency_ids]

    # Filter agency.txt
    mask = df_dict['agency']['agency_id'].isin(agency_ids)
    df_dict['agency'] = df_dict['agency'][mask]

    # Filter routes.txt
    mask = df_dict['routes']['agency_id'].isin(agency_ids)
    df_dict['routes'] = df_dict['routes'][mask]

    # Filter trips.txt
    routes_ids = df_dict['routes']['route_id']
    mask = df_dict['trips']['route_id'].isin(routes_ids)
    df_dict['trips'] = df_dict['trips'][mask]

    # Filter stop_times.txt
    trips_ids = df_dict['trips']['trip_id']
    mask = df_dict['stop_times']['trip_id'].isin(trips_ids)
    df_dict['stop_times'] = df_dict['stop_times'][mask]

    # Filter stops.txt
    stops_ids = df_dict['stop_times']['stop_id'].values
    mask = df_dict['stops']['stop_id'].isin(stops_ids)
    df_dict['stops'] = df_dict['stops'][mask]

    # Filter shapes.txt
    if 'shapes' in df_dict:
        shapes_ids = df_dict['trips']['shape_id'].values
        mask = df_dict['shapes']['shape_id'].isin(shapes_ids)
        df_dict['shapes'] = df_dict['shapes'][mask]

    # Filter calendar.txt
    if 'calendar' in df_dict:
        service_ids = df_dict['trips']['service_id'].values
        mask = df_dict['calendar']['service_id'].isin(service_ids)
        df_dict['calendar'] = df_dict['calendar'][mask]

    # Filter calendar_dates.txt
    if 'calendar_dates' in df_dict:
        service_ids = df_dict['trips']['service_id'].values
        mask = df_dict['calendar_dates']['service_id'].isin(service_ids)
        df_dict['calendar_dates'] = df_dict['calendar_dates'][mask]

    # Filter frequencies.txt
    if 'frequencies' in df_dict:
        # BUG: (ajw, 2024-06-06): trip_ids doesn't look like it's defined but this func isn't used so 🤷‍♂️.
        mask = df_dict['frequencies']['trip_id'].isin(trip_ids)
        df_dict['frequencies'] = df_dict['frequencies'][mask]

    # Filter transfers.txt
    if 'transfers' in df_dict:
        mask = df_dict['transfers']['from_stop_id'].isin(stops_ids) \
            & df_dict['transfers']['to_stop_id'].isin(stops_ids)
        df_dict['transfers'] = df_dict['transfers'][mask]
