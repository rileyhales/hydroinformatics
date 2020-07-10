from io import StringIO

import geoglows
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import requests
from scipy import interpolate
from scipy import stats
import hydrostats as hs
import hydrostats.data as hd


def collect_data(start_id, start_ideam_id, downstream_id, downstream_ideam_id):
    # Upstream simulated flow
    start = geoglows.streamflow.historic_simulation(start_id)
    # Upstream observed flow
    start_ideam = get_ideam_flow(start_ideam_id)
    start_ideam.dropna(inplace=True)

    # Downstream simulated flow
    downstream = geoglows.streamflow.historic_simulation(downstream_id)
    # Downstream observed flow
    downstream_ideam = get_ideam_flow(downstream_ideam_id)
    downstream_ideam.dropna(inplace=True)
    # Downstream bias corrected flow (for comparison to the propagation method
    downstream_bc = geoglows.bias.correct_historical(downstream, downstream_ideam)

    # Export all as csv
    start.to_csv('start_flow.csv')
    start_ideam.to_csv('start_ideam_flow.csv')
    downstream.to_csv('downstream_flow.csv')
    downstream_ideam.to_csv('downstream_ideam_flow.csv')
    downstream_bc.to_csv('downstream_bc_flow.csv')
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


def get_scalar_bias_fdc(first_series, seconds_series):
    first_fdc = compute_flow_duration_curve(first_series)
    second_fdc = compute_flow_duration_curve(seconds_series)
    ratios = np.divide(first_fdc['Flow'].values.flatten(), second_fdc['Flow'].values.flatten())
    columns = (first_fdc.columns[0], 'Scalars')
    scalars_df = pd.DataFrame(np.transpose([first_fdc.values[:, 0], ratios]), columns=columns)
    scalars_df.replace(np.inf, np.nan, inplace=True)
    scalars_df.dropna(inplace=True)

    return scalars_df


def propagate_correction(sim_data: pd.DataFrame, obs_data: pd.DataFrame, sim_data_to_correct,
                         drop_outliers: bool = False, outlier_threshold: int or float = 2.5,
                         filter_scalar_fdc: bool = True, fdc_range: tuple = (10, 90),
                         extrapolate_method: str = 'nearest') -> pd.DataFrame:
    # list of the unique months in the historical simulation. should always be 1->12 but just in case...
    unique_simulation_months = sorted(set(sim_data.index.strftime('%m')))
    dates = []
    values = []
    scales = []
    percents = []

    for month in unique_simulation_months:
        # filter data to only be current iteration's month
        monthly_sim = sim_data[sim_data.index.month == int(month)].dropna()
        monthly_obs = obs_data[obs_data.index.month == int(month)].dropna()
        monthly_cor = sim_data_to_correct[sim_data_to_correct.index.month == int(month)].dropna()

        # compute the fdc for paired sim/obs data and compute scalar fdc, either with or without outliers
        if drop_outliers:
            # drop outlier data
            # https://stackoverflow.com/questions/23199796/detect-and-exclude-outliers-in-pandas-data-frame
            mon_sim_fdc = compute_flow_duration_curve(
                monthly_sim[(np.abs(stats.zscore(monthly_sim)) < outlier_threshold).all(axis=1)])
            mon_obs_fdc = compute_flow_duration_curve(
                monthly_obs[(np.abs(stats.zscore(monthly_obs)) < outlier_threshold).all(axis=1)])
        else:
            mon_sim_fdc = compute_flow_duration_curve(monthly_sim)
            mon_obs_fdc = compute_flow_duration_curve(monthly_obs)

        scalar_fdc = get_scalar_bias_fdc(mon_obs_fdc['Flow'].values.flatten(), mon_sim_fdc['Flow'].values.flatten())

        if filter_scalar_fdc:
            scalar_fdc = scalar_fdc[scalar_fdc['Exceedence Probability'] >= fdc_range[0]]
            scalar_fdc = scalar_fdc[scalar_fdc['Exceedence Probability'] <= fdc_range[1]]

        # create the interpolator for the month
        if extrapolate_method == 'nearest':
            to_scalar = interpolate.interp1d(scalar_fdc.values[:, 0], scalar_fdc.values[:, 1],
                                             fill_value='extrapolate', kind='nearest')
        elif extrapolate_method == 'linear':
            to_scalar = interpolate.interp1d(scalar_fdc.values[:, 0], scalar_fdc.values[:, 1],
                                             fill_value='extrapolate')
        elif extrapolate_method == 'average':
            to_scalar = interpolate.interp1d(scalar_fdc.values[:, 0], scalar_fdc.values[:, 1],
                                             fill_value=np.mean(scalar_fdc.values[:, 1]), bounds_error=False)
        elif extrapolate_method == 'max' or extrapolate_method == 'maximum':
            to_scalar = interpolate.interp1d(scalar_fdc.values[:, 0], scalar_fdc.values[:, 1],
                                             fill_value=np.max(scalar_fdc.values[:, 1]), bounds_error=False)
        elif extrapolate_method == 'min' or extrapolate_method == 'minimum':
            to_scalar = interpolate.interp1d(scalar_fdc.values[:, 0], scalar_fdc.values[:, 1],
                                             fill_value=np.min(scalar_fdc.values[:, 1]), bounds_error=False)
        elif extrapolate_method == 'globalmin':
            total_scalar_fdc = get_scalar_bias_fdc(
                compute_flow_duration_curve(obs_data.values.flatten()),
                compute_flow_duration_curve(sim_data.values.flatten()))
            to_scalar = interpolate.interp1d(scalar_fdc.values[:, 0], scalar_fdc.values[:, 1],
                                             fill_value=np.min(total_scalar_fdc.values[:, 1]), bounds_error=False)
        elif extrapolate_method == 'globalaverage':
            total_scalar_fdc = get_scalar_bias_fdc(
                compute_flow_duration_curve(obs_data.values.flatten()),
                compute_flow_duration_curve(sim_data.values.flatten()))
            to_scalar = interpolate.interp1d(scalar_fdc.values[:, 0], scalar_fdc.values[:, 1],
                                             fill_value=np.mean(total_scalar_fdc.values[:, 1]), bounds_error=False)
        else:
            raise ValueError('Invalid extrapolation method provided')

        # determine the percentile of each uncorrected flow using the monthly fdc
        x = monthly_cor.values.flatten()
        percentiles = [stats.percentileofscore(x, a) for a in x]
        scalars = to_scalar(percentiles)

        dates += monthly_sim.index.to_list()
        # value = np.divide(monthly_cor.values.flatten(), scalars)
        value = monthly_cor.values.flatten() * scalars
        values += value.tolist()
        scales += scalars.tolist()
        percents += percentiles

    df_data = np.transpose([values, scales, percents])
    columns = ['Propagated Corrected Streamflow', 'Scalars', 'MonthlyPercentile']
    corrected = pd.DataFrame(data=df_data, index=dates, columns=columns)
    corrected.sort_index(inplace=True)
    return corrected


def plot_results(sim, obs, bc, bcp, title):
    sim_dates = sim.index.tolist()
    scatters = [
        go.Scatter(
            name='Propagated Corrected (Experimental)',
            x=bcp.index.tolist(),
            y=bcp['Propagated Corrected Streamflow'].values.flatten(),
        ),
        go.Scatter(
            name='Bias Corrected (Jorges Method)',
            x=sim_dates,
            y=bc.values.flatten(),
        ),
        go.Scatter(
            name='Simulated (ERA 5)',
            x=sim_dates,
            y=sim.values.flatten(),
        ),
        go.Scatter(
            name='Observed',
            x=obs.index.tolist(),
            y=obs.values.flatten(),
        ),
        go.Scatter(
            name='Percentile',
            x=sim_dates,
            y=bcp['MonthlyPercentile'].values.flatten(),
        ),
        go.Scatter(
            name='Scalar',
            x=sim_dates,
            y=bcp['Scalars'].values.flatten(),
        ),
    ]
    go.Figure(scatters, layout={'title': title}).show()
    return


def statistics_tables(corrected: pd.DataFrame, simulated: pd.DataFrame, observed: pd.DataFrame) -> pd.DataFrame:
    # merge the datasets together
    merged_sim_obs = hd.merge_data(sim_df=simulated, obs_df=observed)
    merged_cor_obs = hd.merge_data(sim_df=corrected, obs_df=observed)

    metrics = ['ME', 'RMSE', 'NRMSE (Mean)', 'MAPE', 'NSE', 'KGE (2009)', 'KGE (2012)']
    # Merge Data
    table1 = hs.make_table(merged_dataframe=merged_sim_obs, metrics=metrics)
    table2 = hs.make_table(merged_dataframe=merged_cor_obs, metrics=metrics)

    table2 = table2.rename(index={'Full Time Series': 'Corrected Full Time Series'})
    table1 = table1.rename(index={'Full Time Series': 'Original Full Time Series'})
    table1 = table1.transpose()
    table2 = table2.transpose()

    return pd.merge(table1, table2, right_index=True, left_index=True)


def make_stats_summary(df1, df2, df3, df4, df5, df6, labels):
    data = np.transpose((
        df1['Original Full Time Series'],
        df1['Corrected Full Time Series'],
        df2['Corrected Full Time Series'],
        df3['Corrected Full Time Series'],
        df4['Corrected Full Time Series'],
        df5['Corrected Full Time Series'],
        df6['Corrected Full Time Series'],
    ))
    columns = ['Sim v Obs'] + list(labels)
    return pd.DataFrame(data, columns=columns, index=df1.index)


# collect_data(9017261, 32037030, 9015333, 32097010)
collect_data(9012999, 22057070, 9012650, 22057010)

# Read all as csv
start_flow = pd.read_csv('start_flow.csv', index_col=0)
start_ideam_flow = pd.read_csv('start_ideam_flow.csv', index_col=0)
downstream_flow = pd.read_csv('downstream_flow.csv', index_col=0)
downstream_ideam_flow = pd.read_csv('downstream_ideam_flow.csv', index_col=0)
downstream_bc_flow = pd.read_csv('downstream_bc_flow.csv', index_col=0)
start_flow.index = pd.to_datetime(start_flow.index)
start_ideam_flow.index = pd.to_datetime(start_ideam_flow.index)
downstream_flow.index = pd.to_datetime(downstream_flow.index)
downstream_ideam_flow.index = pd.to_datetime(downstream_ideam_flow.index)
downstream_bc_flow.index = pd.to_datetime(downstream_bc_flow.index)


# downstream_prop_correct = propagate_correction(start_flow, start_ideam_flow, downstream_flow)
# plot_results(downstream_flow, downstream_ideam_flow, downstream_bc_flow, downstream_prop_correct, 'Correct Monthly')

methods = ('nearest', 'linear', 'min', 'globalmin', 'average', 'globalaverage')

stats_dfs = []
for extrap_met in methods:
    downstream_prop_correct = propagate_correction(start_flow, start_ideam_flow, downstream_flow,
                                                   drop_outliers=True, outlier_threshold=1,
                                                   extrapolate_method=extrap_met)
    # plot_results(downstream_flow, downstream_ideam_flow, downstream_bc_flow, downstream_prop_correct,
    #              f'Correct Monthly - Drop input outliers @ 1z, {extrap_met} extrapolation')
    del downstream_prop_correct['Scalars'], downstream_prop_correct['MonthlyPercentile']
    stats_dfs.append(statistics_tables(downstream_prop_correct, downstream_flow, downstream_ideam_flow))
make_stats_summary(stats_dfs[0], stats_dfs[1], stats_dfs[2], stats_dfs[3], stats_dfs[4], stats_dfs[5], methods).to_csv('stats_drop_outliers.csv')


stats_dfs = []
for extrap_met in methods:
    downstream_prop_correct = propagate_correction(start_flow, start_ideam_flow, downstream_flow,
                                                   drop_outliers=True, outlier_threshold=1,
                                                   extrapolate_method=extrap_met)
    plot_results(downstream_flow, downstream_ideam_flow, downstream_bc_flow, downstream_prop_correct,
                 f'Correct Monthly - Using the middle of the scalar fdc (10-90%), {extrap_met} extrapolation')
    del downstream_prop_correct['Scalars'], downstream_prop_correct['MonthlyPercentile']
    stats_dfs.append(statistics_tables(downstream_prop_correct, downstream_flow, downstream_ideam_flow))
make_stats_summary(stats_dfs[0], stats_dfs[1], stats_dfs[2], stats_dfs[3], stats_dfs[4], stats_dfs[5], methods).to_csv('stats_middle_1090_scalars.csv')


stats_dfs = []
for extrap_met in methods:
    downstream_prop_correct = propagate_correction(start_flow, start_ideam_flow, downstream_flow,
                                                   drop_outliers=True, outlier_threshold=1,
                                                   extrapolate_method=extrap_met)
    # plot_results(downstream_flow, downstream_ideam_flow, downstream_bc_flow, downstream_prop_correct,
    #              f'Correct Monthly - Using the middle of the scalar fdc (10-80%), {extrap_met} extrapolation')
    del downstream_prop_correct['Scalars'], downstream_prop_correct['MonthlyPercentile']
    stats_dfs.append(statistics_tables(downstream_prop_correct, downstream_flow, downstream_ideam_flow))
make_stats_summary(stats_dfs[0], stats_dfs[1], stats_dfs[2], stats_dfs[3], stats_dfs[4], stats_dfs[5], methods).to_csv('stats_middle_1080_scalars.csv')
