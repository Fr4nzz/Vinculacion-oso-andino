'''El PDF leído por este codigo se encuentra disponible en:
https://www.researchgate.net/publication/318970039_Libro_Rojo_de_las_Plantas_Endemicas_del_Ecuador
Antes de ejecutar este código, se deben instalar las librerias: pdfplumber, pandas y openpyxl en python'''
import pdfplumber
import pandas as pd
import numpy as np
import re
import time
import os
import pickle
start = time.time()
'''Descomentar la siguiente linea si se quiere especificar la carpeta donde se encuentra el pdf
y donde se guardará el archivo de excel. Por defecto se utiliza la ubicacion del script'''
os.chdir('C:/Users/FranzCh/Documents/ProyectoOsos')
print('Cargando pdf con la libreria pdfplumber')
pdf = pdfplumber.open('librorojo2012pdf.pdf') if not ('pdf' in vars() or 'pdf' in globals()) else pdf
#Definicion de las expresiones regulares a buscar en el texto:
year_search = re.compile(r'd{4}')
anyNumber = re.compile(r'\d')
prov_search = re.compile(r'^\?*\(*(AZU|BOL|CAÑ|CAN|CAR|CHI|COT|ESM|GAL|GUA|IMB|LOJ|MAN|MOR|NAP|ORO|ORE|PAS|PIC|RIO|'+
                         r'SDT|SEL|SUC|TUN|ZAM|Localidad desconocida|Provincias* desconocida)')
herbarios_search = re.compile(r'^(Herbarios ecuatorianos*:* *|Nota:* *)')
ref_search = re.compile(r'^Refs\.*:* *')
desconocid_search = re.compile('desconocid')
lycophytas_search = re.compile('(lycoph)|(pteridoph)', re.IGNORECASE)
family_search = re.compile(r'^([a-z]+ceae)\s*$', re.IGNORECASE) #identifica a un nombre de familia porque termina en ceae
m_search = re.compile(r'\d\s*m(\s*|\?|$)')#Identifica si una linea contiene una altura sobre el nivel de mar
bold_search = re.compile('bold', re.IGNORECASE)
wordsOnly = re.compile(r'\b[^\d\W]+\b')
mmtopx = 612/215.36 # factor para convertir milimetros a pixeles
iucn_category_search = re.compile(r'(EX|EW|CR|EN|VU|NT|LC|DD|NE)') #identifica las categorias UICN fuera de parentesis
## las hojas de especies del PDF esta organizado en 2 columnas delimitadas por las coordenadas:
wrongNames = {'Sicyos villosa':'Sicyos villosus','Eucrosia do dsonii':'Eucrosia dodsonii'}
skipTitlesInDescr = {'Araceae':3,'Orchidaceae':11}
xleft,yup,xright,ydown,xmid = 45,137,567,735,314
leftSide = (xleft,yup,xmid,ydown)
rightSide = (xmid,yup,xright,ydown)
Groups = {'ANGIOSPERMAS':{'pages':(70,817),'text':'','ListadoDeSpp':''},
          'GIMNOSPERMAS':{'pages':(820,821),'text':''},
          'Licofitas y Helechos':{'pages':(825,863),'text':''},
          'BRYOPHYTAS':{'pages':(866,879),'text':''}}
def bbox(word):
    return (word['x0'], word['top'], word['x1'], word['bottom'])
currentFamily = ''
wordN = 0
IndxOfBoldWords, IndxOfGreyWords, IndxOfFamilies, prevYPos = [],[],[],0
check = []
class Word:
  def __init__(self, word, column):
    global wordN, prevYPos, IndxOfFamilies, IndxOfBoldWords, IndxOfGreyWords
    self.ypos = word['bottom']
    self.newLine = not bool(self.ypos - 2 < prevYPos and prevYPos < self.ypos + 2)
    self.text = word['text']
    prevYPos = self.ypos
    wordChars = column.crop(bbox(word)).chars
    firstCharInWord = wordChars[0] if wordChars[0]['text'] != ' ' else wordChars[1]
    font = firstCharInWord['fontname']
    color = firstCharInWord['non_stroking_color']
    self.fontSize = firstCharInWord['size']
    self.isFamily = False
    self.isFamilyAuthor = False
    if self.fontSize > 12:
        if family_search.search(self.text):
            self.isFamily = True
    elif self.fontSize > 8:
        self.isFamilyAuthor = True
    self.isGrey = False
    if len(color) == 4:
        if color[3] < 0.95:
            self.isGrey = True
    self.isBold = bool(bold_search.search(font))
    if self.isFamily:
        IndxOfFamilies.append(wordN)
    if self.isBold:
        IndxOfBoldWords.append(wordN)
    if self.isGrey:
        IndxOfGreyWords.append(wordN)
    wordN += 1
Groups['ANGIOSPERMAS']['Word'] = Word
def saveText(Groups):
    with open('LibroRojo.pickle', 'wb') as handle:
        pickle.dump(Groups, handle, protocol=pickle.HIGHEST_PROTOCOL)
def loadSavedText():
    global Groups, Word
    if os.path.isfile(f'LibroRojo.pickle'):
        with open('LibroRojo.pickle', 'rb') as handle:
            Groups = pickle.load(handle)
        Word = Groups['ANGIOSPERMAS']['Word']
    else:
        print('Nothing to load')
loadSavedText()
def getLine(words, startIndx):
    endIndx = startIndx+1
    while not words[endIndx].newLine:
        endIndx += 1
    return ' '.join([w.text for w in words[startIndx:endIndx]]), endIndx
def textWithFormat(column):
    listOfWords = []
    for word in column.extract_words(y_tolerance=0.5):
        listOfWords.append(Word(word,column))
    return listOfWords
def tuplesIndx(Index):
    startEndIndx = [Index[0]]
    for IndxPos, Indx in enumerate(Index[1:-1], 1):
        if not (Indx - Index[IndxPos - 1] < 3 and Index[IndxPos + 1] - Indx < 3):
            startEndIndx.append(Indx)
    startEndIndx = [(startEndIndx[i], startEndIndx[i + 1]) for i in range(0, len(startEndIndx)-1, 2)]
    return startEndIndx
for GroupName, currentGroup in Groups.items():
    print(f'Leyendo especies correspondientes al grupo {GroupName}')
    words = []
    if currentGroup['text'] == '':
        wordN = 0
        IndxOfBoldWords, IndxOfGreyWords, IndxOfFamilies, prevYPos = [],[],[],0
        for pageN in range(*currentGroup['pages']):
            print("reading page N: ", pageN+1) #se suma 1 porque la numeracion de las pags. por pdfplumber empieza en 0
            page = pdf.pages[pageN] #Lee y carga la pagina actual en la memoria
            lines = []
            #En el siguiente for loop se identifican los encabezados de las familias (ej: pag. 76 Actinidiaceae)
            for line in page.lines:
                duplicatedLine = False
                #El encabezado se reconoce porque siempre tiene una linea de longitud entre 114 y 170 pixels
                if (114 <= line['width'] <= 170) and line['stroking_color'] == [1]:
                    for savedline in lines:
                        # Si una linea esta a 2 pixeles cerca de otra, se considera ser la misma linea
                        # y no se agrega a la lista de lineas
                        if savedline-2 <= line['top'] <= savedline+2:
                            duplicatedLine = True
                    if duplicatedLine:
                        continue
                    lines.append(line['top'])
            lines.sort()# Se ordenan las lineas en orden de aparicion de arriba hacia abajo de la pagina
            #El encabezado tiene una altura de 114 pixeles con la linea ubicada en el medio:
            lines = [{"lineBoxUp":yline-57,"lineBoxDown":yline+57} for yline in lines]
            linesN = len(lines)
            # Cada encabezado divide a la pagina horizontalmente creando multiples columnas
            # que se leen de izquierda a derecha y de arriba a abajo:
            if linesN:
                for i,yline in enumerate(lines):
                    #Se lee el texto dentro del encabezado para saber a que familia pertenecen las especies que se leen
                    #despues del encabezado
                    headBox = page.crop((xleft,yline["lineBoxUp"],xright,yline["lineBoxDown"]))#.extract_text()
                    if yline["lineBoxUp"] > yup and i == 0:
                        upperBoxLeft = page.crop((xleft,yup,xmid,yline["lineBoxUp"]))#.extract_text()
                        upperBoxRight = page.crop((xmid,yup,xright,yline["lineBoxUp"]))#.extract_text()
                        words = words + textWithFormat(upperBoxLeft) + textWithFormat(upperBoxRight)
                    columnDown = lines[i + 1]["lineBoxUp"] if i+1 < linesN else ydown
                    lowerBoxLeft = page.crop((xleft,yline["lineBoxDown"],xmid,columnDown))#.extract_text()
                    lowerBoxRight = page.crop((xmid,yline["lineBoxDown"],xright,columnDown))#.extract_text()
                    words = words + textWithFormat(headBox) + textWithFormat(lowerBoxLeft) + textWithFormat(lowerBoxRight)
            else: #Si la pagina no tiene encabezados, simplemente se divide a la pagina en dos columnas
                leftColumn = page.crop(leftSide)#.extract_text()
                rightColumn = page.crop(rightSide)#.extract_text()
                words = words + textWithFormat(leftColumn) + textWithFormat(rightColumn)
            page.close()
        currentGroup['text'] = words  # el texto crudo se almacena en el diccionario
        IndxOfBoldWords, IndxOfGreyWords = tuplesIndx(IndxOfBoldWords), tuplesIndx(IndxOfGreyWords)
        IndxOfFamilies = [(IndxOfFamilies[i],IndxOfFamilies[i+1]) for i in range(len(IndxOfFamilies)-1)]
        currentGroup['Index'] = {'Bold Words': IndxOfBoldWords, 'Grey Words': IndxOfGreyWords,'Families': IndxOfFamilies}
    words = currentGroup['text']
    IndxOfBoldWords = currentGroup['Index']['Bold Words']
    IndxOfGreyWords = currentGroup['Index']['Grey Words']
    IndxOfFamilies = currentGroup['Index']['Families']
    Families = {}
    sppIndx = 0
    pubLocIndx = 0
    for Fam in IndxOfFamilies:
        famStart, famEnd = Fam[0], Fam[1]
        familyName = words[famStart].text
        skip = skipTitlesInDescr[familyName] if familyName in skipTitlesInDescr else 0
        sppIndx += skip
        famAuthorsIndx = famStart+1
        famAuthors = ''
        while words[famAuthorsIndx].isFamilyAuthor:
            famAuthor,famAuthorsIndx = getLine(words,famAuthorsIndx)
            famAuthors = famAuthors + famAuthor
        Families[familyName] = {'Index':Fam,'Authors':famAuthors,'Species':{}}
        breakCurrFam = False
        while sppIndx < len(IndxOfBoldWords)-1 and not breakCurrFam:
            sppStart, sppEnd = IndxOfBoldWords[sppIndx]
            nextSppStart = IndxOfBoldWords[sppIndx+1][0] if sppIndx<len(IndxOfBoldWords)-1 else famEnd
            nextSppStart = famEnd if nextSppStart>famEnd else nextSppStart
            if sppStart < famEnd:
                sppIndx += 1
                sppName = ' '.join([w.text for w in words[sppStart:sppEnd+1]])
                sppName = wrongNames[sppName] if sppName in wrongNames else sppName
                if sppName[0].islower():
                    continue
                publishLoc = []
                while True:
                    auxPubStart = IndxOfGreyWords[pubLocIndx][0]
                    if auxPubStart > nextSppStart:
                        break
                    if auxPubStart > sppStart:
                        pubStart, pubEnd = IndxOfGreyWords[pubLocIndx]
                        publishLoc.append(' '.join([w.text for w in words[pubStart:pubEnd + 1]]))
                    pubLocIndx += 1
                sppAuthors = ' '.join([w.text for w in words[sppEnd + 1:pubStart]])
                if len(publishLoc) == 0: # Lidia con lugares de publicacion cuyo texto no es gris
                    sppNameLine, pubStart = getLine(words,sppStart)
                    sppAuthors = sppNameLine[len(sppName):]
                    auxPublishLoc, pubEnd = getLine(words,pubStart)
                    publishLoc.append(auxPublishLoc)
                    pubEnd -= 1
                iucnStart = pubEnd + 1
                iucn, lifeFormStart = getLine(words, iucnStart)
                iucn = iucn_category_search.split(iucn)
                symbols = iucn[0].replace('U','*').replace('=','+').replace(' ','')
                fullIUCN = ''.join(iucn[1:])+' '+symbols
                iucn = iucn_category_search.search(fullIUCN)
                iucn = iucn.group(0) if iucn else ''
                lifeForm, habitatStart = getLine(words, lifeFormStart)
                habitat, provStart = getLine(words, habitatStart)
                descripcion = ''
                while provStart < nextSppStart:
                    provincias, descrStart = getLine(words, provStart)
                    if not prov_search.search(provincias):
                        habitat = habitat + ' ' + provincias  # si la linea no contiene provincias, esa linea se agrega al habitat
                        provStart = descrStart
                    else:  # si la linea si contiene provincias, se procede a buscar provincias en la siguiente linea
                        descripcion, herbStart = getLine(words,descrStart)  # puede ser la primera linea de descripcion u otra linea de provincias
                        if prov_search.search(
                                descripcion):  # si se encontro otra linea de provincias, se suman las 2 lineas
                            provincias = provincias + descripcion
                            descrStart = herbStart
                            descripcion, herbStart = getLine(words,descrStart)  # se obtiene la primera linea de descripcion
                        break
                if ':' in habitat:
                    aux = habitat.rsplit(':', 1)
                    altitude = aux[1] if len(aux) > 1 else 'desconocido'
                else:
                    altitude = habitat
                if len(altitude) > 1:
                    if altitude[0] == ' ':
                        altitude = altitude[1:]
                else:
                    altitude = ''
                descrLines = [descripcion]
                herbarios = ''
                refStart = nextSppStart
                while herbStart < nextSppStart:
                    herbarios, refStart = getLine(words, herbStart)
                    if not (herbarios_search.search(herbarios) or ref_search.search(herbarios)):
                        descrLines.append(herbarios)
                        herbStart = refStart
                    else:
                        for i in range(len(descrLines)):
                            if len(descrLines[i])>0:
                                if descrLines[i][-1] == '-':
                                    descrLines[i] = descrLines[i][:-1]
                        descripcion = ' '.join(descrLines)
                        break
                refs = ''
                while refStart < nextSppStart:
                    refs, auxRefStart = getLine(words, refStart)
                    if ref_search.search(refs):
                        break
                    else:
                        refStart = auxRefStart
                herbarios = ' '.join([w.text for w in words[herbStart:refStart]])
                herbarios = herbarios_search.split(herbarios)[-1]
                refs = ' '.join([w.text for w in words[refStart:nextSppStart]])
                refs = ref_search.split(refs)[-1]
                if len(publishLoc) > 1:
                    check.append(sppName)
                    print(f'Found two publishing locations in the same species. Check {sppName}')
                sppInfo = {'Especie':sppName, 'Autor(es) de la especie': sppAuthors,'Grupo':GroupName,'Familia':familyName,
                           'Autor(es) de la familia': famAuthors, 'IUCN': iucn,'IUCN completo':fullIUCN,
                           'Forma de vida': lifeForm,'Habitat': habitat, 'Altitud': altitude, 'Provincias': provincias,
                           'Descripcion': descripcion, 'Herbarios ecuatorianos': herbarios,
                           'Lugar de Publicacion': publishLoc[0], 'Referencias': refs}
                Families[familyName]['Species'][sppName] = sppInfo
            else:
                breakCurrFam = True
    currentGroup['Families'] = Families
    currentGroup['DataFrame'] = pd.DataFrame([sppDict for _, famDict in Families.items() for _,sppDict in famDict['Species'].items()])
    saveText(Groups)
#Se unen las especies de los cuatro grupos leídos:
LibroRojo = pd.concat([Groups[GroupName]['DataFrame'] for GroupName in Groups])
LibroRojo['Genero'] = LibroRojo['Especie'].str.split(' ').str[0]
LibroRojo.to_excel('LibroRojo a excel v4.xlsx', index = False, header=True)
#Se lee la lista de especies ubicada en las paginas 924:944 porque contiene especies que no estaban en el contenido del Libro Rojo
iucn_category_search = re.compile(r'\((EX|EW|CR|EN|VU|NT|LC|DD|NE)\)') #identifica las categorias UICN entre parentesis
def listadoDeEspecies():
    xleft,yup,xright,ydown,xmid = 45,230,567,721,306
    columns = []
    start = time.time()
    for pageN in range(924,944):
        print("reading page N: ", pageN+1)
        page = pdf.pages[pageN]
        yup = 230 if pageN == 924 else 50*mmtopx
        col1 = (0,yup,62*mmtopx,ydown)
        col2 = (62*mmtopx,yup,109*mmtopx,ydown)
        col3 = (109*mmtopx,yup,155*mmtopx,ydown)
        col4 = (155*mmtopx,yup,610,ydown)
        for col in [col1,col2,col3,col4]:
            coltext = page.crop(col).extract_text()
            columns.append(coltext)
        page.close()
    columns = list(filter(None, columns))
    text = '\n'.join(columns)
    text = text.split('\n')
    currentFamily = ''
    i=-1
    rows = []
    while i < len(text)-1:
        i += 1
        if family_search.search(text[i]):
            currentFamily = text[i]
            continue
        if iucn_category_search.search(text[i]):
            currIUCN = iucn_category_search.search(text[i]).group(1)
            continue
        if text[i].isupper():
            grupo = text[i]
            continue
        spp = text[i]
        if i < len(text)-1:
            if text[i+1][0].islower():#este if lidia con casos en que el nombre de la especie ocupa 2 lineas
                space = '' if spp[-1] == ' ' else ' '
                spp = spp + space + text[i+1]
                i += 1
        rows.append([spp,currentFamily,currIUCN,grupo])
    listaDeSpp = pd.DataFrame(rows,columns = ['Especie','Familia','IUCN','Grupo'])
    listaDeSpp['Genero'] = listaDeSpp['Especie'].str.split(' ').str[0]
    #Familias.to_excel('Familias.xlsx', index = False, header=True) #Descomentar esta linea si se quiere obtener un excel solo con la informacion de las paginas 924:944
    #LibroRojo = pd.read_excel('LibroRojo a excel.xlsx') #Descomentar esta linea si se quiere ejecutar el codigo desde esta seccion
    print(f'Nombres de especies a buscar encontrados en: {time.time() - start} segundos')
    return listaDeSpp
listadoDeSpp = Groups['ANGIOSPERMAS']['ListadoDeSpp']
if type(listadoDeSpp) != pd.core.frame.DataFrame:
    listadoDeSpp = listadoDeEspecies()
    Groups['ANGIOSPERMAS']['ListadoDeSpp'] = listadoDeSpp
    saveText(Groups)
LibroRojov4 = pd.read_excel(r'LibroRojo a excel v4.xlsx')
LibroRojoCompleto = pd.merge(listadoDeSpp, LibroRojo, on="Especie",how="outer")
LibroRojoCompleto['Familia_x'] = np.where(LibroRojoCompleto['Familia_x'].isnull(),LibroRojoCompleto['Familia_y'],LibroRojoCompleto['Familia_x'])
LibroRojoCompleto['Grupo_x'] = np.where(LibroRojoCompleto['Grupo_x'].isnull(),LibroRojoCompleto['Grupo_y'],LibroRojoCompleto['Grupo_x'])
LibroRojoCompleto['IUCN_x'] = np.where(LibroRojoCompleto['IUCN_x'].isnull(),LibroRojoCompleto['IUCN_y'],LibroRojoCompleto['IUCN_x'])
LibroRojoCompleto['Genero_x'] = np.where(LibroRojoCompleto['Genero_x'].isnull(),LibroRojoCompleto['Genero_y'],LibroRojoCompleto['Genero_x'])
LibroRojoCompleto.rename(columns={'Familia_x': 'Familia','Grupo_x': 'Grupo','IUCN_x': 'IUCN','Genero_x': 'Genero'}, inplace=True)
LibroRojoCompleto.to_excel('LibroRojo a excel Final.xlsx', index = False, header=True)
print(f'tiempo total de ejecución del algoritmo: {(time.time() - start)/60} minutos')
