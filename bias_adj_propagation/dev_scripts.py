import pandas as pd
import geoglows
import requests
from io import StringIO


def get_ideam_flow(id):
    # get the gauged data
    url = f'https://www.hydroshare.org/resource/d222676fbd984a81911761ca1ba936bf/' \
          f'data/contents/Discharge_Data/{id}.csv'
    df = pd.read_csv(StringIO(requests.get(url).text), index_col=0)
    df.index = pd.to_datetime(df.index).tz_localize('UTC')
    return df


def find_downstream_ids(df: pd.DataFrame, target_id: int, same_order: bool = True):
    downstream_ids = []
    stream_row = df[df['COMID'] == target_id]
    stream_order = stream_row['order_'].values[0]

    if same_order:
        while stream_row['NextDownID'].values[0] != -1 and stream_row['order_'].values[0] == stream_order:
            downstream_ids.append(stream_row['NextDownID'].values[0])
            stream_row = df[df['COMID'] == stream_row['NextDownID'].values[0]]
    else:
        while stream_row['NextDownID'].values[0] != -1:
            downstream_ids.append(stream_row['NextDownID'].values[0])
            stream_row = df[df['COMID'] == stream_row['NextDownID'].values[0]]
    return tuple(downstream_ids)


def find_upstream_ids(df: pd.DataFrame, target_id: int, same_order: bool = True):
    # todo
    downstream_ids = []
    stream_row = df[df['COMID'] == target_id]
    stream_order = stream_row['order_'].values[0]

    if same_order:
        while stream_row['NextDownID'].values[0] != -1 and stream_row['order_'].values[0] == stream_order:
            downstream_ids.append(stream_row['NextDownID'].values[0])
            stream_row = df[df['COMID'] == stream_row['NextDownID'].values[0]]
    else:
        while stream_row['NextDownID'].values[0] != -1:
            downstream_ids.append(stream_row['NextDownID'].values[0])
            stream_row = df[df['COMID'] == stream_row['NextDownID'].values[0]]
    return tuple(downstream_ids)


# import geopandas as gpd
# a = pd.read_csv('/Users/riley/Downloads/south_america-geoglows-connections.csv')
# start_flow = geoglows.streamflow.historic_simulation(start_id)
# start_ideam_flow = get_ideam
# downstream_ids = find_downstream_ids(a, start_id, same_order=True)
# shp = gpd.read_file('/Users/riley/Downloads/south_america-geoglows-drainageline/south_america-geoglows-drainageline.shp')
# shp = shp[shp['COMID'].isin(downstream_ids)]
# shp.to_file('/Users/riley/Downloads/check.geojson', driver='GeoJSON')

# start_id = 9017261
# start_ideam_id = 32037030
#
# downstream_id = 9015333
# downstream_ideam_id = 32097010
#
# start_flow = geoglows.streamflow.historic_simulation(start_id)
# start_ideam_flow = get_ideam_flow(start_ideam_id)
# start_biascorr_flow = geoglows.bias.correct_historical(start_flow, start_ideam_flow)
#
# downstream_flow = geoglows.streamflow.historic_simulation(downstream_id)
# downstream_ideam_flow = get_ideam_flow(downstream_ideam_id)
# downstream_biascorr_flow = geoglows.bias.correct_historical(downstream_flow, downstream_ideam_flow)
#
# corrected_downstream_with_start = geoglows.bias.correct_historical(downstream_flow, start_ideam_flow)
#
# start_flow.to_csv('start_flow.csv')
# start_ideam_flow.to_csv('start_ideam_flow.csv')
# start_biascorr_flow.to_csv('start_biascorr_flow.csv')
# downstream_flow.to_csv('downstream_flow.csv')
# downstream_ideam_flow.to_csv('downstream_ideam_flow.csv')
# downstream_biascorr_flow.to_csv('downstream_biascorr_flow.csv')
# corrected_downstream_with_start.to_csv('corrected_downstream_with_start.csv')

# downstream_ideam_id = 32097010
# downstream_ideam_flow = get_ideam_flow(downstream_ideam_id)
# downstream_ideam_flow.to_csv('/Users/riley/Documents/downstream_observed.csv')

# geoglows.plots.forecast_records(geoglows.streamflow.forecast_records(9015333)).show()

df1 = geoglows.streamflow.historic_simulation(600003, forcing='era_5', return_format='csv')
print(df1)