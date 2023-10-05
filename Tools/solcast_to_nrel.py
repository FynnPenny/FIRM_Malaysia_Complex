# Import necessary libraries
import pandas as pd

def convert_nrel(input_csv,latitude,longitude,output_dir):
    # Load the CSV data
    df = pd.read_csv(input_csv)

    # Rename the columns
    df.rename(columns={'AirTemp': 'Temperature',
                    'DewpointTemp': 'Dew Point',
                    'Dhi': 'DHI',
                    'Dni': 'DNI',
                    'Ghi': 'GHI',
                    'RelativeHumidity': 'Relative Humidity',
                    'SurfacePressure': 'Pressure',
                    'WindDirection10m': 'Wind Direction',
                    'WindSpeed10m': 'Wind Speed',
                    'AlbedoDaily': 'Surface Albedo'}, inplace=True)

    # Convert 'PeriodStart' to datetime, shift to UTC, then to UTC+8
    df['PeriodStart'] = pd.to_datetime(df['PeriodStart']).dt.tz_convert('UTC').dt.tz_convert('Asia/Singapore')

    # Change the datetime format to 'mm/dd/yyyy hh:mm'
    df['PeriodStart'] = df['PeriodStart'].dt.strftime('%m/%d/%Y %H:%M')

    # Add date column
    df['PeriodStart'] = pd.to_datetime(df['PeriodStart'])
    df['Year'] = df['PeriodStart'].dt.year
    df['Month'] = df['PeriodStart'].dt.month
    df['Day'] = df['PeriodStart'].dt.day
    df['Hour'] = df['PeriodStart'].dt.hour
    df['Minute'] = df['PeriodStart'].dt.minute

    # Remove rows for 29th February
    df = df[~((df['Month'] == 2) & (df['Day'] == 29))]

    # Define header rows
    header1 = ['Source','Location ID','City','State','Country','Latitude','Longitude','Time Zone','Elevation','Local Time Zone','Clearsky DHI Units','Clearsky DNI Units','Clearsky GHI Units','Dew Point Units','DHI Units','DNI Units','GHI Units','Solar Zenith Angle Units','Temperature Units','Pressure Units','Relative Humidity Units','Precipitable Water Units','Wind Direction Units','Wind Speed Units','Cloud Type -15','Cloud Type 0','Cloud Type 1','Cloud Type 2','Cloud Type 3','Cloud Type 4','Cloud Type 5','Cloud Type 6','Cloud Type 7','Cloud Type 8','Cloud Type 9','Cloud Type 10','Cloud Type 11','Cloud Type 12','Fill Flag 0','Fill Flag 1','Fill Flag 2','Fill Flag 3','Fill Flag 4','Fill Flag 5','Surface Albedo Units','Version']
    header2 = ['Solcast', '3816179', '-', '-', '-', latitude, longitude, 8, 25, 8, 'w/m2', 'w/m2', 'w/m2', 'c', 'w/m2', 'w/m2', 'w/m2', 'Degree', 'c', 'mbar', '%', 'cm', 'Degrees', 'm/s', 'N/A', 'Clear', 'Probably Clear', 'Fog', 'Water', 'Super-Cooled Water', 'Mixed', 'Opaque Ice', 'Cirrus', 'Overlapping', 'Overshooting', 'Unknown', 'Dust', 'Smoke', 'N/A', 'Missing Image', 'Low Irradiance', 'Exceeds Clearsky', 'Missing Cloud Properties', 'Rayleigh Violation', 'N/A', 'unknown']

    # Filter data by year and write to CSV
    for year in range(2007, 2023):
        df_year = df[df['Year'] == year][['Year', 'Month', 'Day', 'Hour', 'Minute', 'DNI', 'DHI', 'GHI', 'Dew Point', 'Temperature', 'Pressure', 'Relative Humidity', 'Wind Direction', 'Wind Speed', 'Surface Albedo']]
        
        # Write to CSV with header rows
        output_file = f'{output_dir}/NREL_{year}_{latitude}_{longitude}.csv'
        with open(output_file, 'w') as f:
            f.write(','.join(header1) + '\n')
            f.write(','.join(map(str, header2)) + '\n')
        df_year.to_csv(output_file, mode='a', index=False)

if __name__ == '__main__':
    input_dir = '/path/to/solcast_csv/dir'
    output_dir = '/path/to/output/dir'

    lats = [str(x) for x in [2.123,5.681,6.319,5.900,2.502,3.225,4.563,3.985,5.284,5.425,2.369,1.671,3.855,3.108,5.081]]
    longs = [str(x) for x in [103.262,100.414,100.283,102.208,102.134,102.465,100.955,101.090,118.284,115.598,111.857,111.257,113.883,101.618,103.104]]

    for i in range(0,len(lats)):
        latitude = lats[i]
        longitude = longs[i]

        combo_str = latitude+'_'+longitude

        solcast_file = input_dir+'/'+combo_str+'/'+combo_str+'_Solcast_PT60M.csv'

        print(f'Converting {solcast_file}...')

        convert_nrel(solcast_file,latitude,longitude,output_dir)
        print('Conversion complete!')


