from os import listdir
from qgis.core import QgsLegendRenderer, QgsLegendStyle

'''Descargo de responsabilidad: (Por ahora) Este código no  fue diseñado para que se pueda ejecutar de forma universal en cualquier computadora, algunas variables
hacen referencia a archivos que se encuentran en mi computadora. Este código tiene el objetivo de servir como ejemplo de creacion de diseños de mapas en QGIS con Python.

Antes de ejecutar este código, se debe tener cargado en QGIS, el mapa base (en mi caso, el mapa satelital de Google), las capas vectoriales de:
las provincias de Ecuador, las parroquias de Pimampiro y el cantón pimampiro. Estas capas deben ser nombradas como se especifica en las lineas 94-99

Las coordenadas de ocurrencias y los modelos maxent se añaden cada vez que se ejecuta el script porque yo solía cambiar el estilo de visualizacion de estas capas frecuentemente.
Basta con cambiar el estilo de una capa de ocurrencia o modelo y guardarlo en el archivo occurrencesPoints.qml o Estilo probabilidades para qgis.qml, respectivamente (linea 27 o 54).
En la siguiente ejecución del script, todas las capas tendrán el nuevo estilo'''

pointsLabel = 'Ocurrencias (GBIF)'
maxentModelsPath = 'C:/Users/FranzCh/Documents/ProyectoOsos/Resultados MaxEnt AllSpp/'
sppNames = [f.split('.')[0] for f in listdir(maxentModelsPath) if f[-3:]=='asc']
sppCoordFolder = 'C:/Users/FranzCh/Documents/ProyectoOsos/Especies en peligro Imbabura/'
sppFiles = [sppCoordFolder+sppName.replace('_',' ')+'.csv' for sppName in sppNames]
regGroupName="registros de ocurrencias (GBIF)"
root = QgsProject.instance().layerTreeRoot()
group = root.findGroup(regGroupName)
if bool(group):
    print('group found, removing sublayers')
    group.removeAllChildren()
else:
    print('group not found, creating new group')
    group = root.addGroup(regGroupName)
for i,spp in enumerate(sppFiles):
    uri = 'file:///'+spp+'?type=csv&crs=epsg:4326&xField=decimalLongitude&yField=decimalLatitude'
    csv = QgsVectorLayer(uri, sppNames[i].replace('_',' '),'delimitedtext')
    csv.loadNamedStyle('C:/Users/FranzCh/Documents/ProyectoOsos/maxent/occurrencesPoints.qml')
    QgsProject.instance().addMapLayer(csv)
    root = QgsProject.instance().layerTreeRoot()
    layer = root.findLayer(csv.id())
    clone = layer.clone()
    group.insertChildNode(0, clone)
    root.removeChildNode(layer)


maxentModelsPath = 'C:/Users/FranzCh/Documents/ProyectoOsos/Resultados MaxEnt AllSpp/'
models = [maxentModelsPath+f for f in listdir(maxentModelsPath) if f[-3:]=='asc']
modelGroupName="Probabilidad de presencia          "
root = QgsProject.instance().layerTreeRoot()
group = root.findGroup(modelGroupName)
if bool(group):
    print('group found, removing sublayers')
    group.removeAllChildren()
else:
    print('group not found, creating new group')
    group = root.addGroup(modelGroupName)
for model in models:
   rlayer = QgsRasterLayer(model, model.split('/')[-1][:-4].replace('_',' '))
   rlayer.setCrs(QgsCoordinateReferenceSystem(4326))
   rlayer.loadNamedStyle('C:/Users/FranzCh/Documents/ProyectoOsos/maxent/Estilo probabilidades para qgis.qml')#Muestra 
   QgsProject.instance().addMapLayer(rlayer)
   root = QgsProject.instance().layerTreeRoot()
   layer = root.findLayer(rlayer.id())
   clone = layer.clone()
   group.insertChildNode(0, clone)
   root.removeChildNode(layer)

print('adding models finished')

def boundingBoxInProjectCRS(sourceL):
    sourceBox = sourceL.extent()
    source_crs = sourceL.sourceCrs()
    dest_crs = iface.mapCanvas().mapSettings().destinationCrs()
    transform = QgsCoordinateTransform(source_crs, dest_crs, QgsProject.instance())
    new_box = transform.transformBoundingBox(sourceBox)
    return new_box

'''La funcion layoutUnitsToMapUnits sirve para simular que un simbolo de la leyenda
sea transparente. El truco consiste en sobreponer un minimapa encima del simbolo para que
parezca que se puede ver el mapa detras de la leyenda'''
def layoutUnitsToMapUnits(layoutRect, map):
    MapToLayRatioX = map.extent().width() / map.sizeWithUnits().width()
    MapToLayRatioY = map.extent().height() / map.sizeWithUnits().height()
    xleft = map.extent().xMinimum() + abs(layoutRect.xMinimum() - map.pagePos().x()) * MapToLayRatioX
    yup = map.extent().yMaximum() - abs(layoutRect.yMinimum() - map.pagePos().y()) * MapToLayRatioY
    xright = xleft + layoutRect.width() * MapToLayRatioX
    ydown = yup - layoutRect.height() * MapToLayRatioY
    return QgsRectangle(QgsPointXY(xleft, yup), QgsPointXY(xright, ydown))


##Create a layout for each species
print('setting env variables')
maxentModelsPath = 'C:/Users/FranzCh/Documents/ProyectoOsos/Resultados MaxEnt AllSpp/'
sppNames = [f.split('.')[0].replace('_', ' ') for f in listdir(maxentModelsPath) if f[-3:] == 'asc']
project = QgsProject.instance()
manager = project.layoutManager()
canvaslayer = project.mapLayersByName('Canvas for models')[0]
googleSat = project.mapLayersByName('Google Satellite')[0]
provincias = project.mapLayersByName('Provinces')[0]
cantones = project.mapLayersByName('nxcantones')[0]
parroquias = project.mapLayersByName('nxparroquias')[0]
pimampiro = project.mapLayersByName('Cantón Pimampiro')[0]
models = project.layerTreeRoot().findGroup(modelGroupName)
coords = project.layerTreeRoot().findGroup(regGroupName)
occInsideCanvas = ['Solanum imbaburense', 'Siphocampylus ecuadoriensis', 'Serjania brevipes', 'Ficus lacunata']
gridbar = 4 #distancia en mmm que ocupa los ejes de la cuadrícula de coordenadas
mapstroke = 0.5 #mitad del grosor del borde del mapa
ministroke = 0.01 #grosor del simbolo de la leyenda que se va a hacer transparente
eclegendstroke = 0.15 #mitad del grosor del borde de la leyenda
poligs = [polig for polig in layout.items() if polig.type() == 65644]#6544 is poligon id type
legWidth, legHeight = 87.5, 32.3-1
'''En mi proyecto de QGIS tengo un layout exclusivo('Layout 1') donde
guardo el estilo con degradado de la flecha Norte. Como no pude recrear ese estilo mediante codigo
simplemente copio el estilo de la flecha norte que esta en 'Layout 1' con las siguientes 2 lineas.
Estas lineas estan comentadas ya que ese poligono esta en mi computadora y no en la suya'''
#layout = manager.layoutByName('Layout 1')
#fillAux = poligs[0].symbol().clone()

for sppName in sppNames:
    layoutsList = manager.printLayouts()
    for layer in coords.findLayers():
        if layer.name() == sppName:
            sppCoords = layer.layer()
    for layer in models.findLayers():
        if layer.name() == sppName:
            sppModel = layer.layer()
    for layout in layoutsList:  ##remove duplicated layers
        if ' '.join(layout.name().split()[:2]) == sppName:
            manager.removeLayout(layout)
    #Para cada especie, se crea dos layouts con el nombre de la especie
    pimpL = QgsPrintLayout(project)
    pimpL.initializeDefaults()
    EcL = QgsPrintLayout(project)
    EcL.initializeDefaults()
    pimpL.setName(sppName+' Pimampiro') #Un layout para el cantón Pimampiro
    EcL.setName(sppName+' Ecuador') #y otro layout para el país
    #Si quisiera rotar el layout para que sea vertical, descomentaría las siguientes 2 líneas
    #pimpPage = pimpL.pageCollection().pages()[0]
    #pimpPage.setPageSize('A4', QgsLayoutItemPage.Orientation.Portrait)
    manager.addLayout(pimpL)
    manager.addLayout(EcL)
    
    ##Agrego el mapa del Cantón Pimampiro
    pimp = QgsLayoutItemMap(pimpL)
    pimp.setRect(20, 20, 20, 20)
    pimp.setFrameEnabled(True)#Establezco el borde del mapa
    pimp.setFrameStrokeColor(QColor(1, 255, 5))#cambio el color del borde del mapa a verde
    #escojo las capas a mostrar en el mapa (en orden de visualizacion de frente a atras)
    pimp.setLayers([sppCoords, pimampiro, parroquias, sppModel, googleSat])
    pimpExtent = boundingBoxInProjectCRS(pimampiro).buffered(0.03)
    pimpExtent.scale(1.0)
    pimp.setExtent(pimpExtent)
    pimp.attemptMove(QgsLayoutPoint(0+eclegendstroke+gridbar, eclegendstroke, QgsUnitTypes.LayoutMillimeters))
    pimpHeight = 210 - gridbar - eclegendstroke
    pimpWidth = pimpHeight*pimpExtent.width()/pimpExtent.height()+eclegendstroke
    pimp.attemptResize(QgsLayoutSize(pimpWidth, pimpHeight, QgsUnitTypes.LayoutMillimeters))
    pimp.setBackgroundColor(QColor(255, 255, 255, 0))
    pimpL.addLayoutItem(pimp)
    pimpPageWidth = pimpWidth+gridbar
    pimpPage.setPageSize(QgsLayoutSize(pimpWidth+gridbar+eclegendstroke, pimpHeight+eclegendstroke+gridbar, QgsUnitTypes.LayoutMillimeters))
    pimplegx, pimplegy = pimpPageWidth-eclegendstroke, 210-gridbar-2*eclegendstroke

    pimp.grid().setEnabled(True)
    pimp.grid().setIntervalX(0.05)
    pimp.grid().setIntervalY(0.05)
    pimp.grid().setAnnotationEnabled(True)
    pimp.grid().setGridLineColor(QColor(0, 176, 246, 127))
    pimp.grid().setGridLineWidth(0.5)
    pimp.grid().setAnnotationPrecision(2)
    # map.grid().setAnnotationFrameDistance(1)
    pimp.grid().setAnnotationFontColor(QColor(0, 176, 246))
    pimp.grid().setAnnotationDisplay(QgsLayoutItemMapGrid.HideAll, QgsLayoutItemMapGrid.Right)
    pimp.grid().setAnnotationDisplay(QgsLayoutItemMapGrid.HideAll, QgsLayoutItemMapGrid.Top)
    pimp.grid().setAnnotationPosition(QgsLayoutItemMapGrid.OutsideMapFrame, QgsLayoutItemMapGrid.Bottom)
    # map.grid().setAnnotationDirection(QgsLayoutItemMapGrid.Horizontal, QgsLayoutItemMapGrid.Bottom)
    pimp.grid().setAnnotationPosition(QgsLayoutItemMapGrid.OutsideMapFrame, QgsLayoutItemMapGrid.Left)
    #map.grid().setAnnotationDirection(QgsLayoutItemMapGrid.Vertical, QgsLayoutItemMapGrid.Left)
    pimp.grid().setAnnotationDirection(QgsLayoutItemMapGrid.Vertical, QgsLayoutItemMapGrid.Left)
    pimp.updateBoundingRect()

    ec = QgsLayoutItemMap(EcL)
    ec.setRect(20, 20, 20, 20)
    ec.setFrameEnabled(True)
    ec.setLayers([sppCoords, pimampiro, provincias, sppModel])  # cantones, googleSat
    ecExtent = boundingBoxInProjectCRS(provincias)
    ecExtent.scale(1.0)
    ec.setExtent(ecExtent)
    ec.attemptMove(QgsLayoutPoint(0+eclegendstroke+gridbar, 0+eclegendstroke, QgsUnitTypes.LayoutMillimeters))
    ecHeight = 210 - gridbar - eclegendstroke
    ecWidth = ecHeight*ecExtent.width()/ecExtent.height()
    ec.attemptResize(QgsLayoutSize(ecWidth, ecHeight, QgsUnitTypes.LayoutMillimeters))
    ec.setBackgroundColor(QColor(255, 255, 255, 0))
    EcL.addLayoutItem(ec)
    EcPageWidth = ecWidth+gridbar+eclegendstroke
    EcPage.setPageSize(QgsLayoutSize(EcPageWidth, ecHeight+eclegendstroke+gridbar, QgsUnitTypes.LayoutMillimeters))
    eclegx, eclegy = EcPageWidth-2*eclegendstroke, 210-gridbar-2*eclegendstroke
    
    ec.grid().setEnabled(True)
    ec.grid().setIntervalX(1)
    ec.grid().setIntervalY(1)
    ec.grid().setAnnotationEnabled(True)
    ec.grid().setGridLineColor(QColor(0, 176, 246, 127))
    ec.grid().setGridLineWidth(0.5)
    ec.grid().setAnnotationPrecision(0)
    # map.grid().setAnnotationFrameDistance(1)
    ec.grid().setAnnotationFontColor(QColor(0, 176, 246))
    ec.grid().setAnnotationDisplay(QgsLayoutItemMapGrid.HideAll, QgsLayoutItemMapGrid.Right)
    ec.grid().setAnnotationDisplay(QgsLayoutItemMapGrid.HideAll, QgsLayoutItemMapGrid.Top)
    ec.grid().setAnnotationPosition(QgsLayoutItemMapGrid.OutsideMapFrame, QgsLayoutItemMapGrid.Bottom)
    # map.grid().setAnnotationDirection(QgsLayoutItemMapGrid.Horizontal, QgsLayoutItemMapGrid.Bottom)
    ec.grid().setAnnotationPosition(QgsLayoutItemMapGrid.OutsideMapFrame, QgsLayoutItemMapGrid.Left)
    #map.grid().setAnnotationDirection(QgsLayoutItemMapGrid.Vertical, QgsLayoutItemMapGrid.Left)
    ec.grid().setAnnotationDirection(QgsLayoutItemMapGrid.Vertical, QgsLayoutItemMapGrid.Left)
    ec.updateBoundingRect()
    
    polig = QPolygonF([QPointF(0,0),QPointF(legWidth,0),QPointF(legWidth,6),QPointF(0,6)])
    rectang = QgsLayoutItemPolygon(polig,pimpL)
    pimpL.addLayoutItem(rectang)
    rectang.setSymbol(QgsFillSymbol().createSimple({'color': '255,255,255,255','outline_style': 'no'}))
    legx, legy = pimpPageWidth-eclegendstroke, 210-gridbar-2*eclegendstroke
    rectang.setReferencePoint(QgsLayoutItem.ReferencePoint.LowerLeft)
    rectang.attemptMove(QgsLayoutPoint(legx-legWidth,legy-legHeight, QgsUnitTypes.LayoutMillimeters))
    
    layers_to_remove = [layer for layer in project.mapLayers().values() if layer.name() != sppName]
    EcLegend = QgsLayoutItemLegend(EcL)
    EcL.addLayoutItem(EcLegend)
    pimpLegend = QgsLayoutItemLegend(pimpL)
    pimpL.addLayoutItem(pimpLegend)
    pimpLegend2 = QgsLayoutItemLegend(pimpL)
    pimpL.addLayoutItem(pimpLegend2)
    for i,legend in enumerate([EcLegend,pimpLegend,pimpLegend2]):#
        legend.setBackgroundEnabled(True)
        legend.setBackgroundColor(QColor(255, 255, 255, 255))
        legend.setAutoUpdateModel(False)
        m = legend.model()
        g = m.rootGroup()
        occurr = g.findGroup(regGroupName)
        modls = g.findGroup(modelGroupName)
        legend.rstyle(QgsLegendStyle.Title).setMargin(QgsLegendStyle.Bottom, 0)
        for l in layers_to_remove:
            if l.name() != pimampiro.name():
                g.removeLayer(l)
            else:
                if i != 0:
                    g.removeLayer(l)
            occurr.removeLayer(l)
            modls.removeLayer(l)
        if i == 1:
            occurr.removeAllChildren()
            QgsLegendRenderer.setNodeLegendStyle(modls, QgsLegendStyle.Hidden)
            legend.setTitle('Probabilidad de presencia')
            legend.rstyle(QgsLegendStyle.Title).setMargin( QgsLegendStyle.Bottom , 1)
        QgsLegendRenderer.setNodeLegendStyle(occurr, QgsLegendStyle.Hidden)
        QgsLegendRenderer.setNodeLegendStyle(modls.children()[0], QgsLegendStyle.Hidden)
        if i == 2:
            modls.removeAllChildren()
            legend.rstyle(QgsLegendStyle.SymbolLabel).setFont(QFont('MS Sans Serif', 12,italic = True))
        legend.setReferencePoint(QgsLayoutItem.ReferencePoint.LowerRight)
        if i == 0:
            legx, legy = eclegx, eclegy
            legend.setFrameEnabled(True)
            legend.rstyle(QgsLegendStyle.SymbolLabel).setFont(QFont('MS Sans Serif', 12,italic = True))
        elif i == 1:
            legx, legy = pimplegx, pimplegy
            legend.setColumnCount(2)
            legend.setColumnSpace(0)
            legend.setSplitLayer(True)
            legend.setBoxSpace(1)
        elif i == 2:
            legend.setReferencePoint(QgsLayoutItem.ReferencePoint.LowerLeft)
            legx, legy = pimplegx-legWidth, pimplegy-legHeight
            legend.setBoxSpace(1)
        legend.attemptMove(QgsLayoutPoint(legx,legy,QgsUnitTypes.LayoutMillimeters))
    
    poligFrame = QPolygonF([QPointF(0,0),QPointF(legWidth,0),QPointF(legWidth,legHeight+6),QPointF(0,legHeight+6)])
    rectangFrame = QgsLayoutItemPolygon(poligFrame,pimpL)
    pimpL.addLayoutItem(rectangFrame)
    rectangFrame.setSymbol(QgsFillSymbol().createSimple({"width_border" : str(2*eclegendstroke),'style': 'no'}))
    rectangFrame.setReferencePoint(QgsLayoutItem.ReferencePoint.LowerRight)
    rectangFrame.attemptMove(QgsLayoutPoint(pimplegx,pimplegy, QgsUnitTypes.LayoutMillimeters))
    
    for i,lay in enumerate([EcL,pimpL]):
        minimap = QgsLayoutItemMap(lay)
        minimap.setRect(20, 20, 20, 20)
        minimap.setLayers([sppModel, googleSat])  # cantones,
        miniWidth, miniHeight = 7, 4
        if i == 0:
            minimapx, minimapy = eclegx-74.4+2, eclegy-45
            mapaux = ec
            #minimapExtent = layoutUnitsToMapUnits(layoutRect, ec)  # boundingBoxInProjectCRS(pimampiro)
        else:
            minimapx, minimapy = pimplegx-legWidth+1, pimplegy-1-4*4-2.5*3
            mapaux = pimp
        layoutRect = QgsRectangle(QgsPointXY(minimapx, minimapy),
                              QgsPointXY(minimapx + miniWidth, minimapy + miniHeight))
        minimapExtent = layoutUnitsToMapUnits(layoutRect, mapaux)
        minimapExtent.scale(1.0)
        minimap.setExtent(minimapExtent)
        minimap.setBackgroundColor(QColor(255, 255, 255, 0))
        minimap.attemptSetSceneRect(QRectF(minimapx, minimapy, miniWidth, miniHeight))
        lay.addLayoutItem(minimap)
        
        NLetter = QgsLayoutItemLabel(lay)
        NLetter.setMode(QgsLayoutItemLabel.ModeHtml)
        NLetter.setText('<p style="text-shadow: 1.5px 1.5px 3px 820000  , 0 0 1em 660000, 0 0 0.2em 660000     ;">&nbsp N</p>')
        NLetter.setFont(QFont('Arial', 25))
        NLetter.setFontColor(QColor('red'))
        letterx, lettery = 12.119, 2.950
        arrowx,arrowy = 15.25, 13
        if i == 1:
            letterx,lettery=4,10.77
            arrowx,arrowy=7.119,20.808
        NLetter.attemptResize(QgsLayoutSize(16.262, 9.9, QgsUnitTypes.LayoutMillimeters))
        lay.addLayoutItem(NLetter)
        NLetter.attemptMove(QgsLayoutPoint(letterx,lettery, QgsUnitTypes.LayoutMillimeters))
        
        polig = QPolygonF([QPointF(0,0),QPointF(5,5),QPointF(0,-8),QPointF(-5,5)])
        northArrow = QgsLayoutItemPolygon(polig,lay)
        lay.addLayoutItem(northArrow)
        '''En mi computadora, agrego el estilo de la flecha norte con la siguiente linea,
        sin embargo, usted no tendrá este estilo en su computador, por lo que esta linea esta comentada.
        En cambio, se coloreará mediante codigo, a la flecha Norte con las lineas posteriores'''
        #northArrow.setSymbol(fillAux)
        northArrow.setSymbol(fillAux)
        arrowDegradade = QgsFillSymbol().createSimple({'border_width_map_unit_scale': '3x:0,0,0,0,0,0', 'color': '255,255,255,255', 'joinstyle': 'miter', 'offset': '0,0', 'offset_map_unit_scale': '3x:0,0,0,0,0,0', 'offset_unit': 'MM', 'outline_color': '0,0,0,255', 'outline_style': 'solid', 'outline_width': '0.3', 'outline_width_unit': 'MM', 'style': 'solid'})
        arrowShadow = QgsFillSymbol().createSimple({'angle': '0', 'color': '255,1,5,255', 'color1': '0,0,255,255', 'color2': '0,255,0,255', 'color_type': '0', 'coordinate_mode': '0', 'discrete': '0', 'gradient_color2': '255,255,255,255', 'offset': '0,0', 'offset_map_unit_scale': '3x:0,0,0,0,0,0', 'offset_unit': 'MM', 'rampType': 'gradient', 'reference_point1': '0.5,0', 'reference_point1_iscentroid': '0', 'reference_point2': '0.5,1', 'reference_point2_iscentroid': '0', 'spread': '0', 'type': '0'})
        arrowDegradade.insertSymbolLayer(1,arrowShadow.symbolLayer(0))
        northArrow.setSymbol(arrowDegradade)
        northArrow.attemptMove(QgsLayoutPoint(arrowx,arrowy, QgsUnitTypes.LayoutMillimeters))

    scalebar = QgsLayoutItemScaleBar(pimpL)
    scalebar.setStyle('Single Box')
    scalebar.setUnits(QgsUnitTypes.DistanceKilometers)
    scalebar.setNumberOfSegments(4)
    scalebar.setNumberOfSegmentsLeft(0)
    scalebar.setUnitsPerSegment(2.5)
    scalebar.setLinkedMap(pimp)
    scalebar.setUnitLabel('Km')
    scalebar.setFont(QFont('MS Shell Dlg 2', 14))
    bufferSetting = QgsTextBufferSettings()
    bufferSetting.setEnabled(True)
    textBuffered = QgsTextFormat()
    textBuffered.setBuffer(bufferSetting)
    scalebar.setTextFormat(textBuffered)
    scalebar.setLineWidth(0)
    scalebar.update()
    pimpL.addLayoutItem(scalebar)
    scalebar.setLabelBarSpace(1)
    scalebar.setReferencePoint(QgsLayoutItem.ReferencePoint.LowerLeft)
    scalx, scaly = 4*eclegendstroke+gridbar, 210-eclegendstroke
    scalebar.attemptMove(QgsLayoutPoint(scalx, scaly, QgsUnitTypes.LayoutMillimeters))
    
    ecscalebar = QgsLayoutItemScaleBar(EcL)
    ecscalebar.setStyle('Single Box')
    ecscalebar.setUnits(QgsUnitTypes.DistanceKilometers)
    ecscalebar.setNumberOfSegments(4)
    ecscalebar.setNumberOfSegmentsLeft(0)
    ecscalebar.setUnitsPerSegment(50)
    ecscalebar.setLinkedMap(ec)
    ecscalebar.setUnitLabel('Km')
    ecscalebar.setFont(QFont('MS Shell Dlg 2', 14))
    ecscalebar.setTextFormat(textBuffered)
    ecscalebar.setLineWidth(0)
    ecscalebar.update()
    EcL.addLayoutItem(ecscalebar)
    ecscalebar.setReferencePoint(QgsLayoutItem.ReferencePoint.UpperRight)
    ecscalebar.attemptMove(QgsLayoutPoint(eclegx, 2*eclegendstroke, QgsUnitTypes.LayoutMillimeters))

project = QgsProject.instance()
manager = project.layoutManager()
maxentModelsPath = 'C:/Users/FranzCh/Documents/ProyectoOsos/Resultados MaxEnt AllSpp/'
sppNames = [f.split('.')[0].replace('_',' ') for f in listdir(maxentModelsPath) if f[-3:]=='asc']
noExport = ['Drymonia laciniosa','Gasteranthus crispus','Gasteranthus trifoliatus','Serjania brevipes','Sorocea sarcocarpa']
for dpiaux in range(2):
    for sppName in sppNames:
        for mapType in [' Ecuador']:#' Ecuador',' Pimampiro'
            if sppName in noExport:
                continue
            layout = manager.layoutByName(sppName+mapType)
            mapdpi = 125 if dpiaux else 15
            layout.renderContext().setDpi(mapdpi)
            exporter = QgsLayoutExporter(layout)
            print(f'exporting {sppName+mapType}')
            exporter.exportToImage (f'C:/Users/FranzCh/Documents/ProyectoOsos/Resultados MaxEnt AllSpp/Mapas Modelos Maxent especies en peligro/{sppName+mapType}-sinSatelite.png',QgsLayoutExporter.ImageExportSettings())
    print('export finished')
