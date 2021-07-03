#Antes de ejecutar este código, se deben instalar las librerias: pdfplumber y pandas en python
import pdfplumber
import pandas as pd
import re
import time
year_search = re.compile(r'd{4}')
anyNumber = re.compile(r'\d')
iucn_category_search = re.compile(r'^(EX|EW|CR|EN|VU|NT|LC|DD|NE)')
prov_search = re.compile(r'^(AZU|BOL|CAÑ|CAR|CHI|COT|ESM|GAL|GUA|IMB|LOJ|MAN|MOR|NAP|ORO|ORE|PAS|PIC|RIO|SDT|SEL|SUC|TUN|ZAM)')
herbarios_search = re.compile(r'^Herbarios ecuatorianos')
ref_search = re.compile(r'^Refs')
desconocid_search = re.compile('desconocid')
pdf = pdfplumber.open('C:/Users/FranzCh/Documents/ProyectoOsos/librorojo2012pdf.pdf')
## las hojas de especies del PDF esta organizado en 2 columnas delimitadas por las coordenadas:
xleft,yup,xright,ydown,xmid = 45,137,567,735,306
leftSide = (xleft,yup,xmid,ydown)
rightSide = (xmid,yup,xright,ydown)
columns = []
start = time.time()
def readGroup(pages):#ayuda a separar la lectura de plantas en grupos: Angiospermas, Gimnospermas, helechos y licofitas, y briofitas
    for pageN in range(924,925):#list(range(70,818)) + list(range(825,863)) + list(range(866,879)):#(70,818)/825,863/866,879
        print("reading page N: ", pageN+1) #para la libreria pdfplumber, la primera pagina tiene numeracion 0.
        page = pdf.pages[pageN] #Lee y carga la pagina actual en la memoria
        lines = []
        #En este for loop se identifican los encabezados de las familias(ej: pag 76 encabezado de Actinidiaceae)
        for line in page.lines:
            skipL = False
            #El encabezado se reconoce porque siempre tiene una linea de longitud entre 114 y 170 pixels
            if 114 <= line['width'] <= 170 and line['stroking_color'] == [1]:
                #print('line y coord: ',line['top'],'yup: ',yup)
                for savedline in lines:
                    print('saved l ',savedline,line['top'])
                    print(savedline-2 <= line['top'] <= savedline+2)
                    if savedline-2 <= line['top'] <= savedline+2:
                        skipL = True
                if skipL:
                    continue
                lines.append(line['top'])
        lines.sort()
        #El encabezado tiene una altura de 114 pixeles con la linea ubicada en el medio
        lines = [{"lineBoxUp":yline-57,"lineBoxDown":yline+57} for yline in lines]
        linesN = len(lines)
        # Cada encabezado divide a la pagina horizontalmente creando multiples columnas
        # que se leen de izquierda a derecha y de arriba a abajo
        if linesN:
            for i,yline in enumerate(lines):
                if yline["lineBoxUp"] > yup and i == 0:
                    upperBoxLeft = page.crop((xleft,yup,xmid,yline["lineBoxUp"])).extract_text()
                    upperBoxRight = page.crop((xmid,yup,xright,yline["lineBoxUp"])).extract_text()
                    columns.extend([upperBoxLeft,upperBoxRight])
                #if linesN > 1:
                columnDown = lines[i + 1]["lineBoxUp"] if i+1 < linesN else ydown
                lowerBoxLeft = page.crop((xleft,yline["lineBoxDown"],xmid,columnDown)).extract_text()
                lowerBoxRight = page.crop((xmid,yline["lineBoxDown"],xright,columnDown)).extract_text()
                columns.extend([lowerBoxLeft,lowerBoxRight])
        else:
            leftColumn = page.crop(leftSide).extract_text()
            rightColumn = page.crop(rightSide).extract_text()
            columns.extend([leftColumn,rightColumn])
        page.close()
    columns = list(filter(None, columns)) #Se eliminan las columnas sin texto
    text = '\n'.join(columns) #se unen las columnas en un solo texto
    text = text.split('\n') #el texto se separa en lineas
    while True:
        try:
            text.remove(' ') #Se eliminan las lineas en blanco
        except ValueError:
            break
    species = []
    '''Cada especie se identifica por tener una secuencia de caracteres unica como lo es la categoría IUCN.
    Cuando se encuentra la categoria IUCN, se entiende que 2 lineas antes, comienza la tabla de la especie (con excepciones)
    la tabla termina con una linea que empieza con el texto: 'Herbarios Ecuatorianos' o con el texto 'Ref:'
    La descripcion contiene multiples lineas que estan delimitadas por la lista de provincias (arriba) y por la lista de herbarios (abajo)
    '''
    i = 0
    while i < len(text):
        if iucn_category_search.match(text[i][:2]):
            publishLoc = text[i - 1]
            sppStart = i-2
            if i > 5:
                for j in range(4):
                    if herbarios_search.match(text[i-3-j]) or ref_search.match(text[i-3-j]):
                        sppStart = i - 2 - j
                        for k in range(0,j+1):
                            if text[i-3-j+k][-1] == ')' or text[i-3-j+k][-7:] == 'ninguno':
                                sppStart = i-2-j+k
                                break
                        break
            sppName = ' '.join(text[sppStart:i - 1])
            iucn = text[i]
            iucn2letters = iucn[:2]
            lifeForm = text[i+1]
            for j in range(i+2,len(text)):
                if text[j][-1] == 'm' or desconocid_search.search(text[j]):
                    provStart = j+1
                    if desconocid_search.search(text[provStart]):
                        provStart += 1
                    break
            habitat = ''.join(text[i + 2:provStart])
            aux = habitat.rsplit(':', 1)
            altitude = aux[1] if len(aux)>1 else 'desconocido'
            if altitude[0] == ' ':
                altitude = altitude[1:]
            j = provStart
            while j<len(text):
                if prov_search.match(text[j][:3]):
                    j += 1
                elif desconocid_search.search(text[j]):
                    descrStart = j+1
                    break
                else:
                    descrStart = j
                    break
            prov = ''.join(text[provStart:descrStart])
            for j in range(descrStart+1,len(text)):
                if herbarios_search.match(text[j]):
                    herbStart = j
                    break
            descr = ''.join(text[descrStart:herbStart])
            if j+1<len(text):
                refs = text[j+1][7:] if ref_search.match(text[j+1][:4]) else ''
            else:
                refs = ''
            herbarios = text[herbStart][24:]
            spp = [sppName,publishLoc,iucn,iucn2letters,lifeForm,habitat,altitude,prov,descr,herbarios,refs]
            species.append(spp)
            i = j
        i += 1
    return pd.DataFrame(species,columns = ['Especie y Autor','Lugar de publicacion','Categoria de la IUCN (raw)','codigo IUCN','Forma de Vida','Habitat','Altitud','Provincias','Descripcion','Herbarios ecuatorianos','Referencias'])
AngiospyGimnosp, HelechyLicof, Briof = list(range(70,818)),list(range(825,863)),list(range(866,879))
LibroRojo = []
for group in [AngiospyGimnosp, HelechyLicof, Briof]:
    LibroRojo.append(readGroup(group))
LibroRojo = pd.concat(LibroRojo)
#Crea una columna lógica cuyo valor es 1 (True) si la especie ocurre en Imbabura, 0 (False) si no.
LibroRojo['Imbabura'] = LibroRojo['Provincias'].str.contains("IMB")
LibroRojo.to_excel('LibroRojo a excel.xlsx', index = False, header=True)
print(f'Total time: {time.time() - start}')

'''Para saber a que familia corresponde cada especie, se lee la lista de especies, organizadas por familias,
en las paginas 924:944; y se adjunta la familia correspondiente a cada especie'''

family_search = re.compile('ceae')
iucn_category_search = re.compile(r'\((EX|EW|CR|EN|VU|NT|LC|DD|NE)\)')
xleft,yup,xright,ydown,xmid = 45,230,567,721,306
mmtopx = 612/215.36
columns = []
start = time.time()
for pageN in range(924,944):
    print("reading page N: ", pageN+1)
    page = pdf.pages[pageN]
    lines = []
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
currFam = ''
i=-1
rows = []
while i < len(text)-1:
    i += 1
    if family_search.search(text[i]):
        currFam = text[i]
        continue
    if iucn_category_search.search(text[i]):
        currIUCN = iucn_category_search.search(text[i]).group(1)
        continue
    if text[i].isupper():
        grupo = text[i]
        continue
    spp = text[i]
    if i < len(text)-1:
        if text[i+1][0].islower():
            spp = spp + ' ' + text[i+1]
            i += 1
    rows.append([spp,currFam,currIUCN,grupo])
Familias = pd.DataFrame(rows,columns = ['Especie','Family','IUCN','grupo'])
#Familias.to_excel('Familias.xlsx', index = False, header=True) #Descomentar esta linea si se quiere obtener un excel solo con la informacion de las paginas 924:944
#LibroRojo = pd.read_excel('LibroRojo a excel.xlsx') #Descomentar esta linea si se quiere ejecutar el codigo desde esta seccion
for index, rows in LibroRojo.iterrows():
    if family_search.search(rows['Especie y Autor'].split()[0]):
        LibroRojo.loc[index, 'Especie y Autor'] = ' '.join(rows['Especie y Autor'].split()[1:])
#en esta seccion se separa el autor del nombre de la especie
sppNames = []
autores = []
for index, rows in LibroRojo.iterrows():
    if rows['Especie y Autor'].split()[1][0] == '(' or rows['Especie y Autor'].split()[1][0] == 'x':
        spp = ' '.join(rows['Especie y Autor'].split()[:3])
        autor = ' '.join(rows['Especie y Autor'].split()[3:])
    else:
        spp = ' '.join(rows['Especie y Autor'].split()[:2])
        autor = ' '.join(rows['Especie y Autor'].split()[2:])
    sppNames.append(spp)
    autores.append(autor)
LibroRojo['Especie'] = sppNames
LibroRojo['Autor(es)'] = autores
LibroRojo = LibroRojo.set_index('Especie')
allSpp = allSpp.set_index('Especie')
allSpp = allSpp.merge(LibroRojo, how='left', on='Especie') #Se unen las bases de datos de las familias (pags 924:944) con las especies (resto del libro)
allSpp.to_excel('C:/Users/FranzCh/Documents/ProyectoOsos/LibroRojo a excelv2.xlsx', index = True, header=True)
