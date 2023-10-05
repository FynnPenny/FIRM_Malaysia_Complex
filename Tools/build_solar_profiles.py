import pandas as pd

def create_profiles(lats, longs, years, output_file):
    # Initialize an empty DataFrame
    final_df = pd.DataFrame()

    for i in range(0,len(lats)):
        latitude = lats[i]
        longitude = longs[i]

        combo_str = latitude+'_'+longitude

        site_files = []
        for year in years:
            site_files.append(input_dir+'/PVWatts_' + str(year)+'_'+combo_str+'.csv')

        location_df = pd.DataFrame()

        # Loop through all files and append them to the DataFrame
        for file in site_files:
            temp_df = pd.read_csv(file)
            location_df = location_df.append(temp_df, ignore_index=True)

        # Divide all the values by 4000
        location_df['ac'] = location_df['ac'] / 4000

        # Add this location's data as a new column in the final DataFrame
        final_df[str(i)] = location_df['ac']

    # Write the resulting DataFrame to a new CSV file
    final_df.to_csv(output_file, index=False)  

if __name__ == '__main__':
    input_dir = '/path/to/SAM Outputs/dir'
    output_dir = '/path/to/output/dir'

    lats = [str(x) for x in [2.123,5.681,6.319,5.900,2.502,3.225,4.563,3.985,5.284,5.425,2.369,1.671,3.855,3.108,5.081]]
    longs = [str(x) for x in [103.262,100.414,100.283,102.208,102.134,102.465,100.955,101.090,118.284,115.598,111.857,111.257,113.883,101.618,103.104]]
    years = list(range(2007,2023))

    output_file = output_dir + '/pv.csv'

    create_profiles(lats, longs, years, output_file)

    
        
        