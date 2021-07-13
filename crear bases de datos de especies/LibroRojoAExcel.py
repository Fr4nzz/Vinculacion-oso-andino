'''El PDF leído por este codigo se encuentra disponible en:
https://www.researchgate.net/publication/318970039_Libro_Rojo_de_las_Plantas_Endemicas_del_Ecuador
Antes de ejecutar este código, se deben instalar las librerias: pdfplumber, pandas y openpyxl en python'''
import pdfplumber
import pandas as pd
import re
import time
import os
start = time.time()
'''Descomentar la siguiente linea si se quiere especificar la carpeta donde se encuentra el pdf
y donde se guardará el archivo de excel. Por defecto se utiliza la ubicacion del script'''
#os.chdir('C:/Users/FranzCh/Documents/VincProject')
print('Cargando pdf con la libreria pdfplumber')
pdf = pdfplumber.open('librorojo2012pdf.pdf')
#Definicion de las expresiones regulares a buscar en el texto:
year_search = re.compile(r'd{4}')
anyNumber = re.compile(r'\d')
prov_search = re.compile(r'^\?*\(*(AZU|BOL|CAÑ|CAN|CAR|CHI|COT|ESM|GAL|GUA|IMB|LOJ|MAN|MOR|NAP|ORO|ORE|PAS|PIC|RIO|'+
                         r'SDT|SEL|SUC|TUN|ZAM|Localidad desconocida|Provincias* desconocida)')
herbarios_search = re.compile(r'^(Herbarios ecuatorianos:* *|Nota:* *)')
ref_search = re.compile(r'^Refs')
desconocid_search = re.compile('desconocid')
lycophytas_search = re.compile('(lycoph)|(pteridoph)', re.IGNORECASE)
family_search = re.compile('^([a-z]+ceae)\s*$', re.IGNORECASE) #identifica a un nombre de familia porque termina en ceae
iucn_category_search = re.compile(r'\((EX|EW|CR|EN|VU|NT|LC|DD|NE)\)') #identifica las categorias UICN entre parentesis
m_search = re.compile('\d\s*m(\s*|\?|$)')#Identifica si una linea contiene una altura sobre el nivel de mar

'''La tabla informativa de cada especie empieza con su nombre. Para identificar donde empieza una tabla informativa,
se deben saber de antemano los nombres de las especies. Los nombres de las especies se encuentran organizados por
familias y grupos en las paginas 924:944, que son leidos en esta sección del código'''

def listadoDeEspecies():
    xleft,yup,xright,ydown,xmid = 45,230,567,721,306
    mmtopx = 612/215.36
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
    Familias = pd.DataFrame(rows,columns = ['Especie','Familia','IUCN','Grupo'])
    Familias['Genero'] = Familias['Especie'].str.split(' ').str[0]
    #Familias.to_excel('Familias.xlsx', index = False, header=True) #Descomentar esta linea si se quiere obtener un excel solo con la informacion de las paginas 924:944
    #LibroRojo = pd.read_excel('LibroRojo a excel.xlsx') #Descomentar esta linea si se quiere ejecutar el codigo desde esta seccion
    print(f'Nombres de especies a buscar encontrados en: {time.time() - start} segundos')
    return Familias
sppNames = listadoDeEspecies()

'''Una vez obtenido el listado de especies que se esperan encontrar en el Libro Rojo, se procede a buscar cada especie
en el contenido del libro. Las especies estan ordenadas por: 1. Grupos (angiospermas, gimnospermas, ...),
2. Familias (en orden alfabético), 3. Especies (en orden alfabético). Como se sabe en qué orden va apareciendo cada
tabla informativa de especie, se realiza una iteracion, linea por linea, hasta hacer un match con el nombre de la especie
esperada y se lee las siguientes lineas de texto donde se encuentra la información de la especie de forma estructurada.
La información de la especie termina con una lista de herbarios o con una lista de referencias.
Una vez llegado al final de la tabla, se procede a buscar la siguiente tabla de especie.'''
iucn_category_search = re.compile(r'(EX|EW|CR|EN|VU|NT|LC|DD|NE)') #identifica las categorias UICN fuera de parentesis
## las hojas de especies del PDF esta organizado en 2 columnas delimitadas por las coordenadas:
xleft,yup,xright,ydown,xmid = 45,137,567,735,314
leftSide = (xleft,yup,xmid,ydown)
rightSide = (xmid,yup,xright,ydown)
Groups = {'ANGIOSPERMAS':{'pages':(70,817),'expectedSpp':sppNames[sppNames.Grupo.str.contains('ANGIOSP')],'text':''},
          'GIMNOSPERMAS':{'pages':(820,821),'expectedSpp':sppNames[sppNames.Grupo.str.contains('GIMNOSP')],'text':''},
          'Licofitas y Helechos':{'pages':(825,863),'expectedSpp':sppNames[sppNames.Grupo.str.contains('LYCOPH|PTERIDOPH')],'text':''},
          'BRYOPHYTAS':{'pages':(866,879),'expectedSpp':sppNames[sppNames.Grupo.str.contains('BRYOPH')],'text':''}}
#Nombres para las columnas de excel:
cols = ['Especie','Autor','Familia','Grupo','Lugar de publicacion','Categoria de la IUCN (raw)','codigo IUCN',
        'Forma de Vida','Habitat','Altitud','Provincias','Descripcion','Herbarios ecuatorianos','Referencias']
for GroupName, currentGroup in Groups.items():
    currentGroup['Familias'] = {}
    sppNamesDF = currentGroup['expectedSpp']
    for familia in sppNamesDF['Familia'].unique():
        FamDF = sppNamesDF[sppNamesDF['Familia'].str.contains(familia)]
        genera = FamDF['Genero'].unique()
        currentGroup['Familias'][familia] = {'genusRegex':re.compile('^'+'('+'|'.join(genera)+')')}
        for genus in genera:
            sppNamesInGenus = FamDF['Especie'][FamDF['Genero'].str.contains(genus)].str[:41]
            currentGroup['Familias'][familia][genus] = {
                'sppRegex':re.compile('^('+'|'.join(sppNamesInGenus).replace('(',r'\(').replace(')',r'\)')+'*)')}
    print(f'Leyendo especies correspondientes al grupo {GroupName}')
    species = []
    columns = []
    currentFamily = ''
    if currentGroup['text'] == '':
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
                    headBox = page.crop((xleft,yline["lineBoxUp"],xright,yline["lineBoxDown"])).extract_text()
                    if yline["lineBoxUp"] > yup and i == 0:
                        upperBoxLeft = page.crop((xleft,yup,xmid,yline["lineBoxUp"])).extract_text()
                        upperBoxRight = page.crop((xmid,yup,xright,yline["lineBoxUp"])).extract_text()
                        columns.extend([upperBoxLeft,upperBoxRight])
                    columnDown = lines[i + 1]["lineBoxUp"] if i+1 < linesN else ydown
                    lowerBoxLeft = page.crop((xleft,yline["lineBoxDown"],xmid,columnDown)).extract_text()
                    lowerBoxRight = page.crop((xmid,yline["lineBoxDown"],xright,columnDown)).extract_text()
                    columns.extend([headBox,lowerBoxLeft,lowerBoxRight])
            else: #Si la pagina no tiene encabezados, simplemente se divide a la pagina en dos columnas
                leftColumn = page.crop(leftSide).extract_text()
                rightColumn = page.crop(rightSide).extract_text()
                columns.extend([leftColumn,rightColumn])
            page.close() #Se libera de la memoria toda la información de la página extraída por pdfplumber
        columns = list(filter(None, columns)) #Se eliminan las columnas sin texto
        text = '\n'.join(columns)  # se unen las columnas en un solo texto
        text = text.split('\n')  # el texto se separa en lineas
        while True:
            try:
                text.remove(' ') #Se eliminan las lineas en blanco
            except ValueError:
                break
        currentGroup['text'] = text  # el texto crudo se almacena en el diccionario
    else:
        text = currentGroup['text']
    i = 0
    currentFamily = sppNamesDF.sort_values('Familia')['Familia'].values[0]
    while i < len(text):
        familyFound = family_search.search(text[i])
        if familyFound:
            trueFam = familyFound.group(1)
            currentFamily = 'Capparaceae' if trueFam == 'Cleomaceae' else trueFam
            print(f'currentFam changed to: {currentFamily}')
        genusFound = currentGroup['Familias'][currentFamily]['genusRegex'].search(text[i])
        if genusFound:
            genus = genusFound.group(0)
            sppFound = currentGroup['Familias'][currentFamily][genus]['sppRegex'].search(text[i])
            if sppFound:
                sppName = sppFound.group(0)
                publishLocStart = i + 1
                if len(sppName)>40:
                    candidateSpp = sppNamesDF['Especie'][sppNamesDF['Especie'].str.contains(sppName)].unique()
                    candidateSppRegex = re.compile('^'+'('+'|'.join(candidateSpp)+')')
                    trueSppName = candidateSppRegex.search(text[i]+text[i+1])
                    print('long spp name: ',text[i]+text[i+1])
                    sppName = trueSppName.group(1) if trueSppName else sppName
                    author = re.split(sppName.replace('(','\(').replace(')','\)')+'\s*', text[i]+text[i+1])[1]
                    publishLocStart = i + 2
                else:
                    author = re.split(sppName.replace('(','\(').replace(')','\)')+'\s*', text[i])
                    if len(author)>1:
                        author = author[1]
                    else:
                        author = text[i+1]
                        publishLocStart = i + 2
                auxBreak = True
                for j in range(i+1,i+6):
                    if re.compile(sppName).search(text[j]):
                        break
                    if iucn_category_search.search(text[j]):
                        auxBreak = False
                        break
                if auxBreak:
                    i+=1
                    continue
                print(f'Especie {sppName} encontrada')
                for ii in range(publishLocStart+1,publishLocStart+7):
                    iucnSearchResults = iucn_category_search.search(text[ii])
                    if iucnSearchResults:
                        IUCNstart = ii
                        publishLoc = ' '.join(text[publishLocStart:IUCNstart])
                        rawIUCN = text[ii]
                        IUCN = iucnSearchResults.group(0)
                        lifeForm = text[ii + 1]
                        break
                provStart = ii+4 #default provinces start 4 lines after IUCN category
                for j in range(ii+2,ii+7):
                    if prov_search.search(text[j]):
                        provStart = j
                        break
                habitat = ''.join(text[ii + 2:provStart])
                if ':' in habitat:
                    aux = habitat.rsplit(':', 1)
                    altitude = aux[1] if len(aux)>1 else 'desconocido'
                else:
                    altitude = habitat
                if len(altitude)>1:
                    if altitude[0] == ' ':
                        altitude = altitude[1:]
                else:
                    altitude = ''
                j = provStart
                while j<len(text):
                    if prov_search.search(text[j][:3]):
                        j += 1
                    elif desconocid_search.search(text[j]):
                        descrStart = j+1
                        break
                    else:
                        descrStart = j
                        break
                prov = ''.join(text[provStart:descrStart])
                herbStart = -1
                for j in range(descrStart+1,len(text)):
                    if herbarios_search.search(text[j]):
                        herbStart = j
                        break
                    if text[j][-1] == '.':
                        herbStart = j+1
                        break
                # La descripcion contiene multiples lineas que estan delimitadas por la lista de provincias (arriba)
                # y por la lista de herbarios (abajo):
                descr = ''.join(text[descrStart:herbStart])
                # la tabla termina con la lista de 'Herbarios Ecuatorianos' o con 'Ref:'
                refs = ''
                if j+1<len(text):
                    refs = text[j+1][7:] if ref_search.search(text[j+1][:4]) else ''
                herbarios = herbarios_search.split(text[i])[-1]
                spp = [sppName,author,trueFam,GroupName,publishLoc,rawIUCN,IUCN,lifeForm,habitat,altitude,prov,descr,herbarios,refs]
                species.append(spp)
                i = j
        i += 1
    currentGroup['digestedSpecies'] = pd.DataFrame(species,columns = cols)
#Se unen las especies de los cuatro grupos leídos:
LibroRojo = pd.concat([Groups[GroupName]['digestedSpecies'] for GroupName in Groups])
#Crea una columna lógica cuyo valor es 1 (True) si la especie ocurre en Imbabura ó 0 (False) si no.
LibroRojo['Imbabura'] = LibroRojo['Provincias'].str.contains("IMB")
#Se añaden las especies que no fueron encontradas por el algoritmo en el cuerpo del texto pero si en el listado de especies:
LibroRojo = pd.merge(sppNames, LibroRojo, on="Especie",how="left")
LibroRojo.to_excel('LibroRojo a excel.xlsx', index = False, header=True)
print(f'tiempo total de ejecución del algoritmo: {(time.time() - start)/60} minutos')
