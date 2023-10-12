from xml.dom.minidom import parseString, Document
from beamshark import BeamSharkLayer
from zipfile import ZipFile
import os, logging

def startLogging(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    # create formatter
    formatter = logging.Formatter('%(asctime)s\t[%(levelname)s]\t %(name)s - %(message)s',datefmt='%Y-%m-%d %H:%M:%S')
    # add formatter to ch
    ch.setFormatter(formatter)
    # add ch to logger
    logger.addHandler(ch)
    return logger 

logger=startLogging('dbp2xml')

def parse_coords(point):
    [x,y]=point.split()
    logger.debug("point:  %s  to Coords [%.2e,%.2e]"%(point,float(x),float(y)))
    return [float(x),float(y)]

def handleLayerSettings(dbp_settings, dbp_layer, xml_proj):
    #global settings from project file
    if dbp_layer.getAttribute("Parallel")=="false":
        parallel=0
    else: parallel=1
    return xml_proj.settings(Process=dbp_layer.getAttribute("Process"),WriteFieldSize=float(dbp_settings.getAttribute("WfSize")), Accuracy="Fine",Spacing=float(dbp_layer.getAttribute("Spacing")), BeamCurrent=float(dbp_layer.getAttribute("BeamCurrent")), SpotSize=float(dbp_layer.getAttribute("SpotSize")),Parallel=parallel,Rate=float(dbp_layer.getAttribute("Rate")),DwellTime=float(dbp_layer.getAttribute("DwellTime"))*1e-9)

def handleObject(dom, proj):
    
    if dom.nodeName=="Dot":
        proj.add_dot(Name=dom.getAttribute("Name"), DepthUnit=dom.getAttribute("DepthUnit"), Center=parse_coords(dom.getAttribute("Center")), Depth=float(dom.getAttribute("Depth")),ExpositionFactor=float(dom.getAttribute("ExpositionFactor")), LineSettleFactor=float(dom.getAttribute("LineSettleFactor")))
    elif dom.nodeName=="Line":
      proj.add_line(Name=dom.getAttribute("Name"), DepthUnit=dom.getAttribute("DepthUnit"), Begin=parse_coords(dom.getAttribute("Begin")), End=parse_coords(dom.getAttribute("End")), Depth=float(dom.getAttribute("Depth")),ExpositionFactor=float(dom.getAttribute("ExpositionFactor")), LineSettleFactor=float(dom.getAttribute("LineSettleFactor")))
    elif dom.nodeName=="Cross":
      center=parse_coords(dom.getAttribute("Center"))
      width=float(dom.getAttribute("Width"))
      logger.debug("Parsing cross  to lines")
      line1=[[center[0]-width/2,center[1]], [center[0]+width/2,center[1]]]
      line2=[[center[0], center[1]-width/2],[center[0],center[1]+width/2]]
      logger.debug("line1 = [%e,%e] [%e,%e]"%(line1[0][0],line1[0][1], line1[1][0], line1[1][1] ))
      logger.debug("line2 = [%e,%e] [%e,%e]"%(line2[0][0],line2[0][1], line2[1][0], line2[1][1] ))
      proj.add_line(Name=dom.getAttribute("Name"), DepthUnit=dom.getAttribute("DepthUnit"), Begin=line1[0], End=line1[1], Depth=float(dom.getAttribute("Depth")),ExpositionFactor=float(dom.getAttribute("ExpositionFactor")), LineSettleFactor=float(dom.getAttribute("LineSettleFactor")))
      proj.add_line(Name=dom.getAttribute("Name"), DepthUnit=dom.getAttribute("DepthUnit"), Begin=line2[0], End=line2[1], Depth=float(dom.getAttribute("Depth")),ExpositionFactor=float(dom.getAttribute("ExpositionFactor")), LineSettleFactor=float(dom.getAttribute("LineSettleFactor")))
    elif dom.nodeName=="Rectangle":
        proj.add_rectangle(Name=dom.getAttribute("Name"),Center=parse_coords(dom.getAttribute("Center")), DepthUnit=dom.getAttribute("DepthUnit"), Width=float(dom.getAttribute("Width")), Height=float(dom.getAttribute("Height")), Depth=float(dom.getAttribute("Depth")),Angle=float(dom.getAttribute("Angle")),ExpositionFactor=float(dom.getAttribute("ExpositionFactor")), LineSettleFactor=float(dom.getAttribute("LineSettleFactor")))
    elif dom.nodeName=="RectangleFilled":
        proj.add_fill_rectangle(Name=dom.getAttribute("Name"),Center=parse_coords(dom.getAttribute("Center")), DepthUnit=dom.getAttribute("DepthUnit"), Width=float(dom.getAttribute("Width")), Height=float(dom.getAttribute("Height")), Depth=float(dom.getAttribute("Depth")),Angle=float(dom.getAttribute("Angle")),ExpositionFactor=float(dom.getAttribute("ExpositionFactor")), LineSettleFactor=float(dom.getAttribute("LineSettleFactor")),ScanningPath=float(dom.getAttribute("ScanningPath")))
    elif dom.nodeName=="RectanglePolish":
        proj.add_polish_rectangle(Name=dom.getAttribute("Name"),Center=parse_coords(dom.getAttribute("Center")), DepthUnit=dom.getAttribute("DepthUnit"), Width=float(dom.getAttribute("Width")), Height=float(dom.getAttribute("Height")), Depth=float(dom.getAttribute("Depth")),Angle=float(dom.getAttribute("Angle")),ExpositionFactor=float(dom.getAttribute("ExpositionFactor")), LineSettleFactor=float(dom.getAttribute("LineSettleFactor")),ScanningPath=float(dom.getAttribute("ScanningPath")))
    elif dom.nodeName=="RectangleStairs":
        proj.add_stairs_rectangle(Name=dom.getAttribute("Name"),Center=parse_coords(dom.getAttribute("Center")), DepthUnit=dom.getAttribute("DepthUnit"), Width=float(dom.getAttribute("Width")), Height=float(dom.getAttribute("Height")), Depth=float(dom.getAttribute("Depth")),Angle=float(dom.getAttribute("Angle")),ExpositionFactor=float(dom.getAttribute("ExpositionFactor")), LineSettleFactor=float(dom.getAttribute("LineSettleFactor")),ScanningPath=int(dom.getAttribute("ScanningPath")))
    elif dom.nodeName=="Arc":
        proj.add_arc( Name=dom.getAttribute("Name"), DepthUnit=dom.getAttribute("DepthUnit"), Center=parse_coords(dom.getAttribute("Center")), Depth=float(dom.getAttribute("Depth")),Radius=float(dom.getAttribute("Radius")),AngleA=float(dom.getAttribute("AngleA")),AngleB=float(dom.getAttribute("AngleB")),Orientation=int(dom.getAttribute("Orientation")), ExpositionFactor=float(dom.getAttribute("ExpositionFactor")), LineSettleFactor=float(dom.getAttribute("LineSettleFactor")))
    elif dom.nodeName=="ArcFilled":
        proj.add_annulus( Name=dom.getAttribute("Name"), DepthUnit=dom.getAttribute("DepthUnit"), Center=parse_coords(dom.getAttribute("Center")), Depth=float(dom.getAttribute("Depth")),RadiusA=float(dom.getAttribute("Radius")),RadiusB=0, AngleA=float(dom.getAttribute("AngleA")),AngleB=float(dom.getAttribute("AngleB")),Orientation=int(dom.getAttribute("Orientation")), ExpositionFactor=float(dom.getAttribute("ExpositionFactor")), LineSettleFactor=float(dom.getAttribute("LineSettleFactor")))
    elif dom.nodeName=="ArcAnnulus":
        proj.add_annulus( Name=dom.getAttribute("Name"), DepthUnit=dom.getAttribute("DepthUnit"), Center=parse_coords(dom.getAttribute("Center")), Depth=float(dom.getAttribute("Depth")),RadiusA=float(dom.getAttribute("RadiusA")),RadiusB=float(dom.getAttribute("RadiusB")), AngleA=float(dom.getAttribute("AngleA")),AngleB=float(dom.getAttribute("AngleB")),Orientation=int(dom.getAttribute("Orientation")), ExpositionFactor=float(dom.getAttribute("ExpositionFactor")), LineSettleFactor=float(dom.getAttribute("LineSettleFactor")))
    elif dom.nodeName=="CirclePolish":
        proj.add_polish_annulus( Name=dom.getAttribute("Name"), DepthUnit=dom.getAttribute("DepthUnit"), Center=parse_coords(dom.getAttribute("Center")), Depth=float(dom.getAttribute("Depth")),RadiusA=float(dom.getAttribute("RadiusA")),RadiusB=float(dom.getAttribute("RadiusB")), AngleA=float(dom.getAttribute("AngleA")),AngleB=float(dom.getAttribute("AngleB")),Orientation=int(dom.getAttribute("Orientation")), ExpositionFactor=float(dom.getAttribute("ExpositionFactor")), LineSettleFactor=float(dom.getAttribute("LineSettleFactor")))
    elif dom.nodeName=="Polygon":
        #logger.debug(dom.toprettyxml(encoding="utf-8").decode())
        Points=[]
        pointsnum=0
        for attribute in dom.attributes.keys():
            logger.debug("%s"%(attribute))
            if attribute[1:].isdigit():
                pointsnum+=1
        logger.debug("Polygon has %i points"%(pointsnum))
        for i in range(1,pointsnum+1):
                point=parse_coords(dom.getAttribute("P%i"%i))
                logger.debug("Parsing poly point %s [%.3e, %.3e]"%(("P%i"%i), point[0], point[1]))
                Points.append(point)
        proj.add_polygon( Points, Name=dom.getAttribute("Name"), DepthUnit=dom.getAttribute("DepthUnit"), Center=parse_coords(dom.getAttribute("Center")), Angle=float(dom.getAttribute("Angle")), Depth=float(dom.getAttribute("Depth")), ExpositionFactor=float(dom.getAttribute("ExpositionFactor")), LineSettleFactor=float(dom.getAttribute("LineSettleFactor")))
    else:
        logger.error("Object not supported yet")
        logger.error(dom.toprettyxml(encoding="utf-8").decode())


def handleObjects(dom, proj):
    """Parses objects in dom=layer"""
    allowed_obj=["Dot","Line", "Rectangle","RectangleFilled", "RectanglePolish", "RectangleStairs", "Polygon", "Cross","Arc", "ArcAnnulus","ArcFilled", "CirclePolish"]
    for Object in dom.childNodes:
        
        if Object.nodeName=="#text":
            #skipping - empty text node
            pass
        elif Object.nodeName=="Mesh":
            logger.error("Mesh objects parsing not supported yet")
        elif Object.nodeName=="Group":
            logger.debug("Processing:" + Object.nodeName )
            logger.warning("Group objects parsing is not tested properly")
            handleObjects(Object, proj)
        elif Object.nodeName in allowed_obj:
            logger.debug("Processing:" + Object.nodeName )
            handleObject(Object, proj)
        else:
            logger.error("Object: %s not supported" %(Object.nodeName))



def handleLayers(dom):
  dbp_settings=dom.getElementsByTagName("Settings")[0]
  layers=dom.getElementsByTagName("Layer")
  for layer in layers:
    logger.info("Parsing layer: %s"%(layer.getAttribute("Name")))
    #check unsupported layer type
    if (layer.getAttribute("Process")=='E-Deposition'):
        logger.error("E-Deposition not supported yet")
    elif (layer.getAttribute("Process")=='E-Exposition'):
        logger.error("E-Exposition not implemented yet")
    elif (layer.getAttribute("Process")=='I-Deposition'):
        logger.warning("Warning I-Deposition not supported yet - converting to I-Etching layer")
        lay_name=layer.getAttribute("Name")
        layer.setAttribute("Process",'I-Etching')
        proj=BeamSharkLayer(lay_name)
        handleLayerSettings(dbp_settings,layer,proj)
        if layer.hasChildNodes():
            handleObjects(layer,proj)
            proj.save_xml(lay_name+".xml")
        else: logger.debug("Empty layer")
    elif (layer.getAttribute("Process")=='I-Etching'):
        lay_name=layer.getAttribute("Name")
        proj=BeamSharkLayer(lay_name)
        handleLayerSettings(dbp_settings,layer,proj)
        if layer.hasChildNodes():
            handleObjects(layer,proj)
            proj.save_xml(lay_name+".xml")
        else: logger.debug("Empty layer")
        
        
def convert(dbp_proj_name):
  dbp=ZipFile(dbp_proj_name)
  dbp_xml=dbp.read('project.xml')
  dbp.close()
  logger.info("Creating Project Directory")
  os.mkdir(dbp_proj_name[:-4])
  os.chdir(dbp_proj_name[:-4])
  dom = parseString(dbp_xml.decode())
  handleLayers(dom)
  os.chdir("..//")


if __name__ == '__main__':
    convert("AutoDIC-all-in-one.dbp")
    
