import PySAM
import PySAM.Pvwattsv8 as pvwatts
import pandas as pd

# Define a function to run PVWatts simulation with SAM
def run_pvwatts_simulation(solar_resource_file, output_file):
    # Create a Pvwattsv8 instance
    model = pvwatts.default("PVWattsNone")

    # Set parameters
    model.SolarResource.solar_resource_file = solar_resource_file
    model.SolarResource.use_wf_albedo = 1 # Use albedo from weather file

    model.SystemDesign.system_capacity = 4
    model.SystemDesign.dc_ac_ratio = 1.2
    model.SystemDesign.tilt = 0
    model.SystemDesign.azimuth = 180
    model.SystemDesign.inv_eff = 96
    model.Lifetime.system_use_lifetime_output = 0
    model.SystemDesign.losses = 14.08
    model.SystemDesign.module_type = 1 # Premium
    model.SystemDesign.array_type = 2 # Single-axis tracking
    model.SystemDesign.gcr = 0.4

    # Execute
    model.execute()

    # Get results
    ac = model.Outputs.ac

    # Convert to DataFrame and save to CSV
    pd.DataFrame(ac, columns=['ac']).to_csv(output_file, index=False)

if __name__ == '__main__':
    input_dir = '/home/tim/Documents/Projects/Malaysia FIRM/FIRM Data_1S1N/Solar/NREL Data'
    output_dir = '/home/tim/Documents/Projects/Malaysia FIRM/FIRM Data_1S1N/Solar/SAM Outputs'

    lats = [str(x) for x in [2.123,5.681,6.319,5.900,2.502,3.225,4.563,3.985,5.284,5.425,2.369,1.671,3.855,3.108,5.081]]
    longs = [str(x) for x in [103.262,100.414,100.283,102.208,102.134,102.465,100.955,101.090,118.284,115.598,111.857,111.257,113.883,101.618,103.104]]
    years = list(range(2007,2023))

    #lats = ['2.123']
    #longs = ['103.262']

    for i in range(0,len(lats)):
        print(f'Simulating {lats[i]}, {longs[i]}...')
        for j in years:
            latitude = lats[i]
            longitude = longs[i]

            combo_str = latitude+'_'+longitude

            nrel_file = input_dir+'/NREL_'+str(j)+'_'+combo_str+'.csv'
            output_file = output_dir + '/PVWatts_' + str(j)+'_'+combo_str+'.csv'
            
            run_pvwatts_simulation(nrel_file,output_file)
        print('Simulations complete!')