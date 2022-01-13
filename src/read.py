# -*- coding: utf-8 -*-
# version 2021.01.12
import sys
import json
import datetime
from GivTCP import GivTCP
from settings import GiV_Settings
from givenergy_modbus.client import GivEnergyClient
from givenergy_modbus.model.inverter import Inverter, Model
from givenergy_modbus.model.register_cache import RegisterCache

Print_Raw=False
if GiV_Settings.Print_Raw_Registers.lower()=="true":
    Print_Raw=True
    
def runAll():
    energy_total_output={}
    energy_today_output={}
    batt_fw={}
    power_output={}
    controlmode={}
    power_flow_output={}
    sum=0
    invertor={}
    emptycount=0
    multi_output={}
    allRegNum=300
    hasExtraReg=False
    temp={}
    GivTCP.debug("----------------------------Starting----------------------------")
    GivTCP.debug("Getting All Registers")
    
    #Connect to Invertor and load data
    try:
        client=GivEnergyClient(host=GiV_Settings.invertorIP)
        InvRegCache = RegisterCache()
        client.update_inverter_registers(InvRegCache)
        GEInv=Inverter.from_orm(InvRegCache)
        #BatRegCache = RegisterCache()
        #client.update_battery_registers(BatRegCache)
        #GEBat=Battery.from_orm(BatRegCache)
        GivTCP.debug("Invertor connection successful, registers retrieved")
    except:
        e = sys.exc_info()
        GivTCP.debug("Error collecting registers: " + str(e))
        temp['result']="Error collecting registers: " + str(e)
        return json.dumps(temp)

    if Print_Raw:
        multi_output['raw/invertor']=GEInv.dict()
        
    try:
    #Total Energy Figures
        GivTCP.debug("Getting Total Energy Data")
        energy_total_output['Export Energy Total kWh']=round(GEInv.e_grid_out_total,2)
        energy_total_output['Battery Throughput Total kWh']=round(GEInv.e_battery_discharge_total_2,2)
        energy_total_output['AC Charge Energy Total kWh']=round(GEInv.e_inverter_in_total,2)
        energy_total_output['Import Energy Total kWh']=round(GEInv.e_grid_in_total,2)
        energy_total_output['Invertor Energy Total kWh']=round(GEInv.e_inverter_out_total,2)
        energy_total_output['PV Energy Total kWh']=round(GEInv.p_inverter_out,2)    #CHECK-CHECK
        
        if  GEInv.inverter_model==Model.Hybrid:
            energy_total_output['Load Energy Total kWh']=round((energy_total_output['Invertor Energy Total kWh']-energy_total_output['AC Charge Energy Total kWh'])-(energy_total_output['Export Energy Total kWh']-energy_total_output['Import Energy Total kWh']),3)
            energy_total_output['Battery Charge Energy Total kWh']=GEInv.e_battery_charge_total
            energy_total_output['Battery Discharge Energy Total kWh']=round(GEInv.e_battery_discharge_total,2)
        else:
            energy_total_output['Load Energy Total kWh']=round((energy_total_output['Invertor Energy Total kWh']-energy_total_output['AC Charge Energy Total kWh'])-(energy_total_output['Export Energy Total kWh']-energy_total_output['Import Energy Total kWh'])+energy_total_output['PV Energy Total kWh'],3)

        if GEInv.inverter_model==Model.Hybrid: 
            energy_total_output['Battery Charge Energy Total kWh']=GEInv.e_battery_discharge_total_2
            energy_total_output['Battery Discharge Energy Total kWh']=GEInv.e_battery_discharge_total_2
        
        energy_total_output['Self Consumption Energy Total kWh']=round(energy_total_output['PV Energy Total kWh']-energy_total_output['Export Energy Total kWh'],2)

#Energy Today Figures
        GivTCP.debug("Getting Today Energy Data")
        energy_today_output['Battery Throughput Today kWh']=round(GEInv.e_battery_charge_day+GEInv.e_battery_discharge_day,2)
        energy_today_output['PV Energy Today kWh']=round(GEInv.e_pv1_day+GEInv.e_pv2_day,2)
        energy_today_output['Import Energy Today kWh']=round(GEInv.e_grid_in_day,2)
        energy_today_output['Export Energy Today kWh']=round(GEInv.e_grid_out_day,2)
        energy_today_output['AC Charge Energy Today kWh']=round(GEInv.e_inverter_in_day,2)
        energy_today_output['Invertor Energy Today kWh']=round(GEInv.e_inverter_out_total,2)
        energy_today_output['Battery Charge Energy Today kWh']=round(GEInv.e_battery_charge_day,2)
        energy_today_output['Battery Discharge Energy Today kWh']=round(GEInv.e_battery_discharge_day,2)
        energy_today_output['Import for Load Energy Today kWh']=round(GEInv.e_grid_in_day - GEInv.e_inverter_in_day,2)
        energy_today_output['Self Consumption Energy Today kWh']=round(energy_today_output['PV Energy Today kWh']-energy_today_output['Export Energy Today kWh'],2)
                
        if GEInv.inverter_model==Model.Hybrid: 
            energy_today_output['Load Energy Today kWh']=round((energy_today_output['Invertor Energy Today kWh']-energy_today_output['AC Charge Energy Today kWh'])-(energy_today_output['Export Energy Today kWh']-energy_today_output['Import Energy Today kWh']),3)
        else:
            energy_today_output['Load Energy Today kWh']=round((energy_today_output['Invertor Energy Today kWh']-energy_today_output['AC Charge Energy Today kWh'])-(energy_today_output['Export Energy Today kWh']-energy_today_output['Import Energy Today kWh'])+energy_today_output['PV Energy Today kWh'],3)

        
############  Core Power Stats    ############

    #PV Power
        GivTCP.debug("Getting PV Power")
        PV_power_1=GEInv.p_pv1
        PV_power_2=GEInv.p_pv2
        PV_power=PV_power_1+PV_power_2
        if PV_power<15000:
            power_output['PV Power String 1']= PV_power_1
            power_output['PV Power String 2']= PV_power_2
            power_output['PV Power']= PV_power

    #Grid Power
        GivTCP.debug("Getting Grid Power")
        grid_power= GEInv.p_grid_out
        if grid_power<0:
            import_power=abs(grid_power)
            export_power=0
        elif grid_power>0:
            import_power=0
            export_power=abs(grid_power)
        else:
            import_power=0
            export_power=0
        power_output['Grid Power']=grid_power
        power_output['Import Power']=import_power
        power_output['Export Power']=export_power

    #EPS Power
        GivTCP.debug("Getting EPS Power")
        power_output['EPS Power']= GEInv.p_eps_backup

    #Invertor Power
        GivTCP.debug("Getting PInv Power")
        Invertor_power=GEInv.p_inverter_out
        if -6000 <= Invertor_power <= 6000:
            power_output['Invertor Power']= Invertor_power
        if Invertor_power<0:
            power_output['AC Charge Power']= abs(Invertor_power)

    #Load Power
        GivTCP.debug("Getting Load Power")
        Load_power=GEInv.p_load_demand 
        if Load_power<15500:
            power_output['Load Power']=Load_power

    #Self Consumption
        GivTCP.debug("Getting Self Consumption Power")
        power_output['Self Consumption Power']=max(Load_power - import_power,0)

    #Battery Power
        Battery_power=GEInv.p_battery 
        if Battery_power>=0:
            discharge_power=abs(Battery_power)
            charge_power=0
        elif Battery_power<=0:
            discharge_power=0
            charge_power=abs(Battery_power)
        power_output['Battery Power']=Battery_power
        power_output['Charge Power']=charge_power
        power_output['Discharge Power']=discharge_power

    #SOC
        GivTCP.debug("Getting SOC")
        power_output['SOC']=GEInv.battery_percent

############  Power Flow Stats    ############

    #Solar to H/B/G
        GivTCP.debug("Getting Solar to H/B/G Power Flows")
        if PV_power>0:
            S2H=min(PV_power,Load_power)
            power_flow_output['Solar to House']=S2H
            S2B=max((PV_power-S2H)-export_power,0)
            power_flow_output['Solar to Battery']=S2B
            power_flow_output['Solar to Grid']=max(PV_power - S2H - S2B,0)

        else:
            power_flow_output['Solar to House']=0
            power_flow_output['Solar to Battery']=0
            power_flow_output['Solar to Grid']=0

    #Battery to House
        GivTCP.debug("Getting Battery to House Power Flow")
        B2H=max(discharge_power-export_power,0)
        power_flow_output['Battery to House']=B2H

    #Grid to Battery/House Power
        GivTCP.debug("Getting Grid to Battery/House Power Flow")
        if import_power>0:
            power_flow_output['Grid to Battery']=charge_power-max(PV_power-Load_power,0)
            power_flow_output['Grid to House']=max(import_power-charge_power,0)

        else:
            power_flow_output['Grid to Battery']=0
            power_flow_output['Grid to House']=0

    #Battery to Grid Power
        GivTCP.debug("Getting Battery to Grid Power Flow")
        if export_power>0:
            power_flow_output['Battery to Grid']=max(discharge_power-B2H,0)
        else:
            power_flow_output['Battery to Grid']=0

    #Get Invertor Temperature
        invertor['Invertor Temperature']=round(GEInv.temp_inverter_heatsink,2)

    #Combine all outputs
        multi_output["Energy/Total"]=energy_total_output
        multi_output["Energy/Today"]=energy_today_output
        multi_output["Power"]=power_output
        multi_output["Power/Flows"]=power_flow_output
        multi_output["Invertor Details"]=invertor

    ################ Run Holding Reg now ###################
        GivTCP.debug("Getting mode control figures")
        # Get Control Mode registers
        shallow_charge=GEInv.battery_soc_reserve
        self_consumption=GEInv.battery_power_mode 
        charge_enable=GEInv.enable_charge
        if charge_enable==True:
            charge_enable="Active"
        else:
            charge_enable="Paused"

        #Get Battery Stat registers
        battery_reserve=GEInv.battery_discharge_min_power_reserve
        target_soc=GEInv.charge_target_soc
        discharge_enable=GEInv.enable_discharge
        if discharge_enable==True:
            discharge_enable="Active"
        else:
            discharge_enable="Paused"
        GivTCP.debug("Shallow Charge= "+str(shallow_charge)+" Self Consumption= "+str(self_consumption)+" Discharge Enable= "+str(discharge_enable))

        #Get Charge/Discharge Active status
        discharge_state=GEInv.battery_discharge_limit
        discharge_rate=discharge_state*3
        if discharge_rate>100: discharge_rate=100
        if discharge_state==0:
            discharge_state="Paused"
        else:
            discharge_state="Active"
        charge_state=GEInv.battery_charge_limit
        charge_rate=charge_state*3
        if charge_rate>100: charge_rate=100
        if charge_state==0:
            charge_state="Paused"
        else:
            charge_state="Active"


        #Calculate Mode
        GivTCP.debug("Calculating Mode...")
        mode=GEInv.system_mode
        GivTCP.debug("Mode is: " + str(mode))

        controlmode['Mode']=mode
        controlmode['Battery Power Reserve']=battery_reserve
        controlmode['Target SOC']=target_soc
        controlmode['Charge Schedule State']=charge_enable
        controlmode['Discharge Schedule State']=discharge_enable
        controlmode['Battery Charge State']=charge_state
        controlmode['Battery Discharge State']=discharge_state
        controlmode['Battery Charge Rate']=charge_rate
        controlmode['Battery Discharge Rate']=discharge_rate

        #Grab Timeslots
        timeslots={}
        GivTCP.debug("Getting TimeSlot data")
        timeslots['Discharge start time slot 1']=GEInv.discharge_slot_1[0]
        timeslots['Discharge end time slot 1']=GEInv.discharge_slot_1[1]
        timeslots['Discharge start time slot 2']=GEInv.discharge_slot_2[0]
        timeslots['Discharge end time slot 2']=GEInv.discharge_slot_2[1]
        timeslots['Charge start time slot 1']=GEInv.charge_slot_1[0]
        timeslots['Charge end time slot 1']=GEInv.charge_slot_1[1]
        timeslots['Charge start time slot 2']=GEInv.charge_slot_2[0]
        timeslots['Charge end time slot 2']=GEInv.charge_slot_2[1]

        #Get Invertor Details
        invertor={}
        GivTCP.debug("Getting Invertor Details")
        if GEInv.battery_type==1: batterytype="Lithium" 
        if GEInv.battery_type==0: batterytype="Lead Acid" 
        invertor['Battery Type']=batterytype
        invertor['Battery Capacity kWh']=round(((GEInv.battery_nominal_capacity*51.2)/1000),2)
        invertor['Invertor Serial Number']=GEInv.inverter_serial_number
        invertor['Battery Serial Number']=GEInv.first_battery_serial_number
        invertor['Modbus Version']=round(GEInv.modbus_version,2)
        if GEInv.meter_type==1: metertype="EM115" 
        if GEInv.meter_type==0: metertype="EM418" 
        invertor['Meter Type']=metertype
        invertor['Invertor Type']= GEInv.inverter_model.name

        #Create multioutput and publish
        if len(timeslots)==8:
            multi_output["Timeslots"]=timeslots
        if len(controlmode)==9:
            multi_output["Control"]=controlmode
        if len(invertor)==7:
            multi_output["Invertor Details"]=invertor
            
        publishOutput(multi_output)
    except:
        e = sys.exc_info()
        GivTCP.debug("Error processing registers: " + str(e))
        temp['result']="Error processing registers: " + str(e)
        return json.dumps(temp)
    return json.dumps(multi_output, indent=4, sort_keys=True, default=str)

def publishOutput(output):
    if GiV_Settings.MQTT_Output.lower()=="true":
        from mqtt import GivMQTT
        GivTCP.debug("Publish all to MQTT")
        GivMQTT.multi_MQTT_publish(output)
    if GiV_Settings.JSON_Output.lower()=="true":
        from GivJson import GivJSON
        GivTCP.debug("Pushing JSON output")
        GivJSON.output_JSON(output)
    if GiV_Settings.Influx_Output.lower()=="true":
        from influx import GivInflux
        GivTCP.debug("Pushing output to Influx")
        GivInflux.publish(output)

if __name__ == '__main__':
    globals()[sys.argv[1]]()

