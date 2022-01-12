###############################################################################
# imports
###############################################################################
import oemof.solph as solph
import oemof.outputlib as outputlib
import oemof.tools.economics as eco

import oemof.solph as solph
import oemof.outputlib as outputlib
import pickle
import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter, YearLocator, MonthLocator
import matplotlib
import oemof_visio as oev
matplotlib.rcParams['figure.figsize'] = [20.0, 7.0]


import os
import pandas as pd
import yaml



def display_results(config_path, team_number):

    ###########################################################################
    # Load configuration file and parameter data
    ###########################################################################
    with open(config_path, 'r') as ymlfile:
        cfg = yaml.load(ymlfile, Loader=yaml.CLoader)

    abs_path = os.path.dirname(os.path.abspath(os.path.join(__file__, '..')))

    # Get values of energy system parameters
    file_name_param_01 = cfg['design_parameters_file_name'][team_number]
    file_name_param_02 = cfg['parameters_file_name']
    file_path_param_01 = (abs_path + '/data/'
                          + file_name_param_01)
    file_path_param_02 = (abs_path + '/data/'
                          + file_name_param_02)
    param_df_01 = pd.read_csv(file_path_param_01, index_col=1)
    param_df_02 = pd.read_csv(file_path_param_02, index_col=1)  
    param_df = pd.concat([param_df_01, param_df_02], sort=True)
    param_value = param_df['value']

    ###########################################################################
    # Restore results from latest optimisation
    ###########################################################################
    energysystem = solph.EnergySystem()
    abs_path = os.path.dirname(os.path.abspath(os.path.join(__file__, '..')))
    energysystem.restore(
        dpath=abs_path + "/results/optimisation_results/dumps",
        filename="model_team_{0}.oemof".format(team_number+1))
    string_results = outputlib.views.convert_keys_to_strings(
        energysystem.results['main'])

    # Extract specific time series (sequences) from results data
    shortage_electricity = string_results[
        'shortage_bel', 'electricity']['sequences']
    shortage_heat = string_results[
        'shortage_bth', 'heat']['sequences']
    shortage_hydrogen = string_results[
        'shortage_bh2', 'hydrogen']['sequences']
    gas_consumption = string_results[
        'rgas', 'natural_gas']['sequences']
    h2_demand = string_results[
        'hydrogen', 'demand_h2']['sequences']
    heat_demand = string_results[
        'heat', 'demand_th']['sequences']
    el_demand = string_results[
        'electricity', 'demand_el']['sequences']

    print("")
    print("-- Results (Team", cfg['team_names'][team_number].upper(),
          ") --")

    ###########################################################################
    # CO2-Emissions
    ###########################################################################
    em_co2 = (gas_consumption.flow.sum()
              *param_value['emission_gas']
              + shortage_hydrogen.flow.sum()
              *param_value['emission_h2']
             + shortage_electricity.flow.sum()
              *param_value['emission_el']
             + shortage_heat.flow.sum()
              *param_value['emission_heat'])  # [(MWh/a)*(kg/MWh)]
    print("CO2-Emission: {:.2f}".format(em_co2/1e3), "t/a")

    ###########################################################################
    # Costs
    ###########################################################################
    capex_chp = (param_value['number_of_chps']
                 * param_value['invest_cost_chp'])
    capex_boiler = (param_value['number_of_boilers']
                    * param_value['invest_cost_boiler'])
    capex_wind = (param_value['number_of_windturbines']
                  * param_value['invest_cost_wind'])
    capex_hp = (param_value['number_of_heat_pumps']
                * param_value['invest_cost_heatpump'])
    capex_storage_el = (param_value['capacity_electr_storage']
                        * param_value['invest_cost_storage_el'])
    capex_storage_th = (param_value['capacity_thermal_storage']
                        * param_value['invest_cost_storage_th'])
    capex_storage_h2 = (param_value['capacity_hydrogen_storage']
                        * param_value['invest_cost_storage_h2'])
    capex_pv = param_value['area_PV'] * param_value['invest_cost_pv']
    capex_solarthermal = (param_value['area_solar_th']
                          * param_value['invest_cost_solarthermal'])
    capex_PV_pp = (param_value['number_of_PV_pp']
                   * param_value['invest_cost_PV_pp']
                   * param_value['PV_pp_surface_area'])
    capex_electrolyser = (param_value['number_of_electrolysers']
                * param_value['invest_cost_electrolyser'])
    capex_Hydrogen_SMR = (param_value['number_of_Hydrogen_SMR']
                * param_value['invest_cost_Hydrogen_SMR'])
                          

    # Calculate annuity of each technology
    annuity_chp = eco.annuity(
        capex_chp,
        param_value['lifetime'],
        param_value['wacc'])
    annuity_electrolyser = eco.annuity(
        capex_electrolyser,
        param_value['lifetime'],
        param_value['wacc'])
    annuity_boiler = eco.annuity(
        capex_boiler,
        param_value['lifetime'],
        param_value['wacc'])
    annuity_wind = eco.annuity(
        capex_wind,
        param_value['lifetime'],
        param_value['wacc'])
    annuity_hp = eco.annuity(
        capex_hp,
        param_value['lifetime'],
        param_value['wacc'])
    annuity_storage_h2 = eco.annuity(
        capex_storage_h2,
        param_value['lifetime'],
        param_value['wacc'])
    annuity_storage_el = eco.annuity(
        capex_storage_el,
        param_value['lifetime'],
        param_value['wacc'])
    annuity_storage_th = eco.annuity(
        capex_storage_th,
        param_value['lifetime'],
        param_value['wacc'])
    annuity_pv = eco.annuity(
        capex_pv,
        param_value['lifetime'],
        param_value['wacc'])
    annuity_solar_th = eco.annuity(
        capex_solarthermal,
        param_value['lifetime'],
        param_value['wacc'])
    annuity_PV_pp = eco.annuity(
        capex_PV_pp,
        param_value['lifetime'],
        param_value['wacc'])
    annuity_Hydrogen_SMR = eco.annuity(
        capex_Hydrogen_SMR,
        param_value['lifetime'],
        param_value['wacc'])
    

    # Variable costs
    var_costs_gas = gas_consumption.flow.sum()*param_value['var_costs_gas']
    var_costs_el_import = (shortage_electricity.flow.sum()
                           * param_value['var_costs_shortage_bel'])
    var_costs_heat_import = (shortage_heat.flow.sum()
                             * param_value['var_costs_shortage_bth'])
    var_costs_h2_import = (shortage_hydrogen.flow.sum()
                           * param_value['var_costs_shortage_bh2'])
    var_costs_es = var_costs_gas + var_costs_el_import + var_costs_heat_import + var_costs_h2_import

    total_annuity = (annuity_chp + annuity_boiler + annuity_wind
                     + annuity_hp + annuity_storage_el
                     + annuity_storage_th + annuity_pv
                     + annuity_solar_th + annuity_PV_pp + annuity_storage_h2 + annuity_electrolyser + annuity_Hydrogen_SMR)

    print("Total Costs of Energy System per Year: {:.2f}".format(
        (var_costs_es+total_annuity) / 1e6), "Mio. €/a")

    ###########################################################################
    # Self-Sufficiency
    ###########################################################################

    # Take electrical consumption of heat pump (hp) into account. Quantity of
    # 'el_demand' does not include electrical consumption of hp.
    if param_value['number_of_heat_pumps'] > 0:
        el_consumption_hp = string_results[
            'electricity', 'heat_pump']['sequences'].flow.sum()
        el_consumption_incl_heatpump = el_demand.flow.sum() + el_consumption_hp
        coverage_el = ((el_consumption_incl_heatpump
                        - shortage_electricity.flow.sum())
                       / el_consumption_incl_heatpump)
    else:
        coverage_el = ((el_demand.flow.sum() - shortage_electricity.flow.sum())
                       / el_demand.flow.sum())

    coverage_heat = ((heat_demand.flow.sum() - shortage_heat.flow.sum())
                     / heat_demand.flow.sum())
    
    coverage_h2 = ((h2_demand.flow.sum() - shortage_hydrogen.flow.sum())
                       / h2_demand.flow.sum())

    selfsufficiency = (coverage_el + coverage_heat + coverage_h2) / 3

    print("Self-Sufficiency: {:.2f} %".format(selfsufficiency*100))
    print("")


    ###########################################################################
    # Plots
    ###########################################################################
    
    print(string_results.keys())
    node_results_bh2 = outputlib.views.node(energysystem.results['main'], 'hydrogen')
  
    
    df = node_results_bh2['sequences']
    df.head(2)
    ax = df.plot(kind='line', drawstyle='steps-post')
    ax.set_xlabel('Time [h]')
    ax.set_ylabel('Energy [MWh]')
    ax.set_title('Flows into and out of bh2')
    ax.legend(loc='upper center', bbox_to_anchor=(1.0, 0.5)) # place legend outside of plot
    
    plt.show()
    fig = plt.figure(figsize=(13, 5))
    
    in_out_dictionary = oev.plot.divide_bus_columns('hydrogen', df.columns)
    in_cols = in_out_dictionary['in_cols']
    out_cols = in_out_dictionary['out_cols']
    bh2_to_demand_h2 = [(('hydrogen', 'demand_h2'), 'flow')] #  this is a list with one element
    df[bh2_to_demand_h2].head(2)
    
    ax = df[out_cols].plot(kind='line', drawstyle='steps-post')
    ax.set_xlabel('Time [h]')
    ax.set_ylabel('Energy [MWh]')
    ax.set_title('Flows into or out of bh2')
    ax.legend(loc='upper center', bbox_to_anchor=(1.0, 0.5)) # place legend outside of plot
    plt.show()
    fig = plt.figure(figsize=(13, 5))
    
    inorder = [(('wind_turbine', 'hydrogen'), 'flow'),
             (('PV_pp', 'hydrogen'), 'flow'),
             (('PV', 'hydrogen'), 'flow'),
             (('solar_thermal', 'hydrogen'), 'flow'),
             (('electrolyser', 'hydrogen'), 'flow'),
             (('Hydrogen_SMR', 'hydrogen'), 'flow'),
             (('chp', 'hydrogen'), 'flow'),
             (('boiler', 'hydrogen'), 'flow')]
            

    outorder = [(('hydrogen', 'demand_h2'), 'flow')]
                
           
    cdict = {(('wind_turbine', 'hydrogen'), 'flow'): '#eeac7e',
        (('PV_pp', 'hydrogen'), 'flow'): '#0f2e2e',
        (('PV', 'hydrogen'), 'flow'): '#c76c56',
        (('solar_thermal', 'hydrogen'), 'flow'): '#56201d',
        (('electrolyser', 'hydrogen'), 'flow'): '#ffde32',
        (('Hydrogen_SMR', 'hydrogen'), 'flow'): '#494a19',
        (('chp', 'hydrogen'), 'flow'): '#4ca7c3',
        (('hydrogen', 'demand_h2'), 'flow'): '#ce4aff',
        (('hydrogen', 'excess_h2'), 'flow'): '#42c77a',
        (('hydrogen', 'heat_pump'), 'flow'): '#555555'}


    fig = plt.figure(figsize=(13, 5))

    my_plot = oev.plot.io_plot('hydrogen', df,
                           inorder=inorder,
                           outorder=outorder,
                           cdict=cdict,
                           ax=fig.add_subplot(1, 1, 1),
                           smooth=False)
    ax = my_plot['ax']
    oev.plot.set_datetime_ticks(ax, df.index, tick_distance=32,
                            date_format='%Y', offset=12)

    my_plot['ax'].set_ylabel('Power in MW')
    my_plot['ax'].set_xlabel('2012')
    my_plot['ax'].set_title("hydrogen bus")
    legend = ax.legend(loc='center left', bbox_to_anchor=(1.0, 0.5)) # place legend outside of plot

    # save figure
    fig = ax.get_figure()
    fig.savefig('myplot.png', bbox_inches='tight')
    return

