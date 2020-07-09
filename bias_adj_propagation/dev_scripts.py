from io import StringIO

import geoglows
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import requests
from scipy import interpolate
from scipy import stats


def collect_data(start_id, start_ideam_id, downstream_id, downstream_ideam_id):
    # Upstream simulated flow
    start_flow = geoglows.streamflow.historic_simulation(start_id)
    start_fdc = compute_flow_duration_curve(start_flow.values.flatten())
    # Upstream observed flow
    start_ideam_flow = get_ideam_flow(start_ideam_id)
    start_ideam_flow.dropna(inplace=True)
    start_ideam_fdc = compute_flow_duration_curve(start_ideam_flow.values.flatten())
    # upstream bias corrected flow
    start_bc_flow = geoglows.bias.correct_historical(start_flow, start_ideam_flow)
    start_bc_fdc = compute_flow_duration_curve(start_bc_flow.values.flatten())

    # Downstream simulated flow
    downstream_flow = geoglows.streamflow.historic_simulation(downstream_id)
    # downstream_fdc = compute_flow_duration_curve(downstream_flow.values.flatten())
    # Downstream observed flow
    downstream_ideam_flow = get_ideam_flow(downstream_ideam_id)
    downstream_ideam_flow.dropna(inplace=True)
    # Downstream bias corrected flow (for comparison to the propagation method
    downstream_bc_flow = geoglows.bias.correct_historical(downstream_flow, downstream_ideam_flow)

    # Export all as csv
    start_flow.to_csv('start_flow.csv')
    start_fdc.to_csv('start_fdc.csv')
    start_ideam_flow.to_csv('start_ideam_flow.csv')
    start_ideam_fdc.to_csv('start_ideam_fdc.csv')
    start_bc_flow.to_csv('start_bc_flow.csv')
    start_bc_fdc.to_csv('start_bc_fdc.csv')
    downstream_flow.to_csv('downstream_flow.csv')
    downstream_ideam_flow.to_csv('downstream_ideam_flow.csv')
    downstream_bc_flow.to_csv('downstream_bc_flow.csv')
    return


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


def compute_flow_duration_curve(hydro: list or np.array, prob_steps: int = 500, exceedence: bool = True):
    percentiles = [round((1 / prob_steps) * i * 100, 5) for i in range(prob_steps + 1)]
    flows = np.nanpercentile(hydro, percentiles)
    if exceedence:
        percentiles.reverse()
        columns = ['Exceedence Probability', 'Flow']
    else:
        columns = ['Non-Exceedence Probability', 'Flow']
    return pd.DataFrame(np.transpose([percentiles, flows]), columns=columns)


def compute_scalar_bias_fdc(first_series, seconds_series):
    first_fdc = compute_flow_duration_curve(first_series)
    second_fdc = compute_flow_duration_curve(seconds_series)
    ratios = np.divide(first_fdc['Flow'].values.flatten(), second_fdc['Flow'].values.flatten())
    scalars_df = pd.DataFrame(np.transpose([first_fdc.values[:, 0], ratios]))
    scalars_df.replace(np.inf, np.nan, inplace=True)
    scalars_df.dropna(inplace=True)

    return scalars_df


# collect_data(9017261, 32037030, 9015333, 32097010)
# collect_data(9012999, 22057070, 9012650, 22057010)

# Read all as csv
start_flow = pd.read_csv('start_flow.csv', index_col=0)
start_fdc = pd.read_csv('start_fdc.csv', index_col=0)
start_ideam_flow = pd.read_csv('start_ideam_flow.csv', index_col=0)
start_ideam_fdc = pd.read_csv('start_ideam_fdc.csv', index_col=0)
start_bc_flow = pd.read_csv('start_bc_flow.csv', index_col=0)
start_bc_fdc = pd.read_csv('start_bc_fdc.csv', index_col=0)
downstream_flow = pd.read_csv('downstream_flow.csv', index_col=0)
downstream_ideam_flow = pd.read_csv('downstream_ideam_flow.csv', index_col=0)
downstream_bc_flow = pd.read_csv('downstream_bc_flow.csv', index_col=0)

scalars_df = compute_scalar_bias_fdc(start_ideam_fdc['Flow'].values.flatten(), start_fdc['Flow'].values.flatten())
to_scalar = interpolate.interp1d(scalars_df.values[:, 0], scalars_df.values[:, 1],
                                 fill_value='extrapolate', kind='nearest')

x = downstream_flow.values.flatten()
percentiles = [stats.percentileofscore(x, a) for a in x]

pd.DataFrame(
    np.transpose(
        [downstream_flow.values.flatten(), downstream_bc_flow.values.flatten(), percentiles, to_scalar(percentiles)]),
    index=downstream_flow.index,
    columns=['Simulated (ERA5)', 'Corrected (Jorge)', 'Percentiles', 'Scalars']
).to_csv('downstream_sim_data.csv')

sim_dates = downstream_flow.index.tolist()
scatters = [
    go.Scatter(
        name='Propagated Corrected (Experimental)',
        x=sim_dates,
        y=np.divide(downstream_flow.values.flatten(), to_scalar(percentiles)),
        # y=downstream_flow.values.flatten() * to_scalar(percentiles),
    ),
    go.Scatter(
        name='Bias Corrected (Jorges Method)',
        x=sim_dates,
        y=downstream_bc_flow.values.flatten(),
    ),
    go.Scatter(
        name='Simulated (ERA 5)',
        x=sim_dates,
        y=downstream_flow.values.flatten(),
    ),
    go.Scatter(
        name='Observed',
        x=downstream_ideam_flow.index.tolist(),
        y=downstream_ideam_flow.values.flatten(),
    ),
    go.Scatter(
        name='Percentile',
        x=sim_dates,
        y=percentiles,
    ),
    go.Scatter(
        name='Scalar',
        x=sim_dates,
        y=to_scalar(percentiles),
    ),
]
go.Figure(scatters).show()

# downstream_flow.to_csv('downstream_flow.csv')
# downstream_ideam_flow.to_csv('downstream_observed_flow.csv')
# downstream_bc_flow.to_csv('downstream_bs_flow.csv')


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

# import geopandas as gpd
# a = pd.read_csv('/Users/riley/Downloads/south_america-geoglows-connections.csv')
# start_flow = geoglows.streamflow.historic_simulation(start_id)
# start_ideam_flow = get_ideam
# downstream_ids = find_downstream_ids(a, start_id, same_order=True)
# shp = gpd.read_file('/Users/riley/Downloads/south_america-geoglows-drainageline/south_america-geoglows-drainageline.shp')
# shp = shp[shp['COMID'].isin(downstream_ids)]
# shp.to_file('/Users/riley/Downloads/check.geojson', driver='GeoJSON')
