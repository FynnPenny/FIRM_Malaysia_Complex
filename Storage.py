import numpy as np
import pandas as pd
from scipy.signal import welch
import matplotlib.pyplot as plt

def dft_analysis(df):

    # Apply a Hanning Window
    window = np.hanning(len(df['energy']))
    windowed_energy = df['energy'] * window

    # Perform the DFT
    fft_result = np.fft.rfft(windowed_energy)

    # Get the power spectral density
    frequencies, psd = welch(windowed_energy, fs=1.0)

    # Plot the absolute values of the FFT results
    plt.figure(figsize=(10,4))
    plt.plot(np.abs(fft_result))
    plt.title('FFT Results (Absolute Value)')
    plt.show()

    # Plot the Power Spectral Density
    plt.figure(figsize=(10,4))
    plt.semilogy(frequencies, psd)
    plt.title('Power Spectral Density')
    plt.grid(True)
    plt.show()

def timeshifting_analysis(node,scenario,percapita):
    LPGM_df = pd.read_csv('Results/LPGM_{}_{}_{}_Network.csv'.format(node,scenario,percapita))

    dft_analysis(LPGM_df)

if __name__ == '__main__':
    node = 'APG_Full'
    scenario = 'HVDC'
    percapita = 20