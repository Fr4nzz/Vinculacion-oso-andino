#Antes de ejecutar este codigo, hay que instalar las librerias: Pandas, BeautifulSoup y requests; en Python.
import pandas as pd
from bs4 import BeautifulSoup
import requests
import time
start = time.time()
plants = pd.read_csv('AdvancedSearchResults.csv',error_bad_lines=False)
header=['NameID','Scientific Name','Habit', 'Status', 'Elevation', 'Region', 'Province', 'Special Notes', 'Standard Note', 'x7', 'Voucher Specimen', 'Reference','Flora of Ecuador Reference','Protected Areas']
sample = plants.head(10) # toma muestra de las 10 primeras especies para probar el algoritmo
def extractData(sppId,sciName):
    #el link de cada especie es el mismo, solo cambia el id de la especie
    url ='http://legacy.tropicos.org/Name/{}?projectid=2'.format(sppId) #se inserta el id en los corchetes
    tropicPage = requests.get(url).text #descarga el codigo fuente de la pagina de la especie
    soup = BeautifulSoup(tropicPage,'lxml') #libreria que facilita la busqueda de variables y valores de la pagina descargada
    line=[sppId,sciName] #las primeras 2 columnas van a ser el ID y el nombre cientifico de la especie
    for i in range(12): #cada especie tiene un maximo de 12 variables que estan nombradas en la lista header
        if i<10:
            info = soup.find('tr', id='ctl00_MainContentPlaceHolder_projectNameControl_projectDetailsControls_QuestionSetRepeater_ctl00_AnswerSetRepeater_ctl00_QuestionSubsetRepeater_ctl00_AnswerRepeater_ctl0{}_AnswerRow'.format(i))
        else:
            info = soup.find('tr', id='ctl00_MainContentPlaceHolder_projectNameControl_projectDetailsControls_QuestionSetRepeater_ctl00_AnswerSetRepeater_ctl00_QuestionSubsetRepeater_ctl00_AnswerRepeater_ctl{}_AnswerRow'.format(i))
        if info is not None:#si existe la info, se guarda el texto en val y se borran los espacios del texto (tabs, enters)
            var = info.find('span',class_='ItemTitle').text.replace('\t','').replace('\r','').replace('\n','')
            val = info.find('span',class_='ItemText').text.replace('\t','').replace('\r','').replace('\n','')
        else: # si no se encuentra la info, se escribe 'No info'
            val='No info'
        line.append(val) #cada resultado se añade en la lista line
    print(sppId) #se muestra en que especie va el programa
    return line
dfLines = [extractData(sppId,sciName) for sppId,sciName in zip(plants['NameID'],plants['Name'])]
df = pd.DataFrame(dfLines, columns=header) #las lineas se transforman a un objeto llamado dataframe que acelera el guardado del archivo
df.to_csv ('Imbabura.csv', index = False, header=True)
print(f'Time: {time.time() - start}')
