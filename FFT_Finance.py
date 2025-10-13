# -*- coding: utf-8 -*-
"""
Created on Wed Oct 16 15:08:55 2024

@author: Francesco
"""

"""
in questo script ci sono degli.: 'N.B.:' che spiegano alcuni passaggi cruciali
di alcune logiche.
è importante notare come i parametri di fondamentale interesse per la corretta 
implementazione del codice sono i seguenti.: 
* variabile 'ticker', da scegliere dalla lista di yfinance, permette di scegliere 
il titolo su cui effettuare l'analisi
* coefficiente moltiplicatore della deviazione standard della PSD, è lui che effettua 
il filtraggio delle frequenze, variarlo permette la decisione del filtro.
"""

#importazione librerie
from matplotlib import pyplot as plt
import yfinance as yf
import pandas as pd
import numpy as np
from scipy.fft import rfft, rfftfreq, irfft


#ticker di interesse
ticker = 'NQ=F'
yf_ticker = yf.Ticker(ticker)

ticker_data = yf_ticker.history(start="2020-01-01",
                                end="2024-12-31",
                                interval="1d") #uso 1 giorno come frequenza di campionamento

#N.B.: la FT, funziona meglio sui segnali stazionari, ovvero segnali che tendono 
#ad avere media e varianza costante nel tempo, per questo diamo come input 
#alla FT le variazioni percentuali e non direttamente i prezzi
stock_prices =  ticker_data['Close'].pct_change().dropna()

stock_prices_np = stock_prices.values


# Parametri per la FFT
N = len(stock_prices_np)  # Numero di campioni
T = 1  # Supponiamo che sia un campione al giorno

# Eseguiamo la FFT
yf = rfft(stock_prices_np)
xf = rfftfreq(N, 1/T)

#con np.abs calcoliamo il modulo del numero complesso
plt.plot(xf, np.abs(yf))
plt.xlabel('Frequency [1/days]')
plt.ylabel('PSD')
plt.title(f"{ticker} Fourier Transform")
plt.grid()
plt.show()


#FILTRAGGIO
# Creiamo un DataFrame per lavorare con le psd, frequenze e output della fft
df = pd.DataFrame({
    'freq': xf,
    'power_spectral_density': np.abs(yf),
    'raw_fourier_output': yf,
})

# Estraiamo i dati dominanti
meanAmp = df['power_spectral_density'].mean() #psd media
stdAmp = df['power_spectral_density'].std() #standard deviazione della psd
#N.B.: in base al coefficiente con cui moltiplichiamo la std decidiamo quali frequenze filtrare
dominantAmpCheck = df['power_spectral_density'] > (3 * stdAmp + meanAmp)  # Ampiezza dominante 
#(Regola statistica: 68-95-99,7), possiamo applicarla perchè abbiamo come input 
#della FFT le variazioni percentuali dei prezzi anzichè i prezzi puri
#quindi assumiamo il dataset delle variazioni percentuali come nornalmente distribuito

# Filtriamo le ampiezze, le frequenze e gli output della fft dominanti 
dominantAmp = df[dominantAmpCheck]['power_spectral_density']
dominantFreq = df[dominantAmpCheck]['freq']
dominantRawFourierOutput = df[dominantAmpCheck]['raw_fourier_output']

# Grafico delle frequenze dominanti
plt.plot(dominantFreq, dominantAmp, 'o')
plt.xlabel('Frequency [1/days]')
plt.ylabel('PSD')
plt.title('Dominant frequencies')
plt.grid()
plt.show()

#Eliminiamo ciò che non è di interesse
condition = df['freq'].isin(dominantFreq) #array di True o False per le frequenze che si filtrano
df.loc[~condition, 'raw_fourier_output'] = 0 #poniamo a 0 tutti gli output della fft che restano fuori dalla condizione
new_sig = irfft(df['raw_fourier_output'].values, n=len(stock_prices)) #Img dell'antitrasformata, poniamo un 
#limite sulla lunghezza per scrupolo, perchè la lunghezza deve combaciare con la lunghezza del dominio

# Grafico delle variazioni percentuali del prezzo con il filtraggio
plt.figure(figsize=(12, 6))

plt.plot(stock_prices.index,
         stock_prices,
         label='Original stock prices variation %',
         color='blue',
         lw=1.2
         )

plt.plot(stock_prices.index,
         new_sig,
         label='Filtered stock prices variation %',
         color='red',
         lw=1.2
         )

plt.xlabel('Dates [days]')
plt.ylabel('% variation')
plt.title(f"{ticker} Price percentage variation")

#N.B.: per ogni run assicurati che le date dei quarti fiscali coincidano con i
#quarti del ticker selezionato!!!
#poniamo delle linee verticali che coincidono con la metà di ogni quarto fiscale
#per il mercato americano in generale
for i in range(stock_prices.index[0].year, stock_prices.index[-1].year+1):
    plt.axvline(x = pd.Timestamp(f'{i}-01-01'), linestyle='--', color = 'yellow', label = '1Q' if i == stock_prices.index[0].year else "")
    plt.axvline(x = pd.Timestamp(f'{i}-04-01'), linestyle='--', color = 'orange', label = '2Q' if i == stock_prices.index[0].year else "")
    plt.axvline(x = pd.Timestamp(f'{i}-07-01'), linestyle='--', color = 'black', label = '3Q' if i == stock_prices.index[0].year else "")
    plt.axvline(x = pd.Timestamp(f'{i}-10-01'), linestyle='--', color = 'green', label = '4Q' if i == stock_prices.index[0].year else "")

plt.legend()
plt.grid(True)
plt.show()


first_absolute_price = ticker_data['Close'][0]
second_absolute_price = ticker_data['Close'][0]   
                                                                 #prodotto cumulativo
original_absolute_prices = (first_absolute_price * (1 + stock_prices).cumprod())
original_absolute_prices = pd.concat([pd.Series([first_absolute_price]), original_absolute_prices])

filtered_absolute_prices = (second_absolute_price * (1 + new_sig).cumprod())
filtered_absolute_prices = pd.concat([pd.Series([second_absolute_price]), pd.Series(filtered_absolute_prices)])


# Grafico del prezzo assoluto e del prezzo filtrato
plt.figure(figsize=(12, 6))

plt.plot(ticker_data.index,
         ticker_data['Close'],
         label='Original stock prices',
         color='blue',
         lw=1.2
         )
plt.plot(ticker_data.index,
         filtered_absolute_prices,
         label='Filtered stock prices',
         color='red',
         lw=1.2
         )
plt.xlabel('Dates [days]')
plt.ylabel('Prices [$]')
plt.title(f"{ticker} Market prices")
plt.legend()
plt.grid(True)
plt.show()


































