"""DrawBeam Shark
Version 0.1
"""
from xml.dom.minidom import Document


# from zipfile import ZipFile

class BeamSharkLayer():
    """DOM DrawBeam Creation script"""

    def __init__(self, name):
        self.document = Document()
        self.layer = self.document.createElement("Layer")
        self.layer.setAttribute("Version", "1.0")
        self.layer.setAttribute("Name", name)
        self.document.appendChild(self.layer)

    def settings(self, Process="I-Etching", WriteFieldSize=1e-4, Accuracy="Fine", Spacing=1.0, BeamCurrent=1e-9,
                 SpotSize=5e-8, Parallel=0, Dose=2.0, Rate=3e-10, DwellTime=1e-6):
        """Settings of the milling/exposition conditions
            Process (mandatory): "E-Exposition" or "I-Etching" must be specified.
            WriteFieldSize:     Write field size in meters. Default value is 0.001 m.
            Accuracy:             Exposition mesh accuracy. Default is Fine. Available options are Coarse, Medium, Fine, ExtraFine.
            BeamCurrent:        Electron beam current in Amps. Default is 1 nA=1e-9
            Spacing:             Exposition mesh spacing. Default is 1.0.

            E-Exposition specific parameters:
            Dose:                Resist exposition dose in C/ m2. Default is 2.0 C/m2= 200 uC/cm2. Spot size si calculated automatically

            I-Etching specific parameters:
            SpotSize:             I-Ecthing parameter only - ion beam spot size in meters. Default is 50 nm.
            Parallel:            Parallel processing flag. Default is 0. Available options are 0 (serial etching) or 1 (parallel etching).
            Rate:                  Ion etching rate in m3/A/s. Default is 0.3 μm3/nA/s=3e-10m3/A/s
            DwellTime:             Pixel dwell time in seconds. Default is 1 μs=1e-6 s

            """
        setting = self.document.createElement("Settings")
        setting.setAttribute("WriteFieldSize", "%e" % (WriteFieldSize))
        setting.setAttribute("Process", Process)
        setting.setAttribute("Accuracy", Accuracy)
        setting.setAttribute("Spacing", "%e" % (Spacing))
        setting.setAttribute("BeamCurrent", "%e" % (BeamCurrent))
        if Process == "I-Etching":
            setting.setAttribute("SpotSize", "%e" % (SpotSize))
            setting.setAttribute("Parallel", "%d" % (Parallel))
            setting.setAttribute("Rate", "%e" % (Rate))
            setting.setAttribute("DwellTime", "%e" % (DwellTime))
        elif Process == "E-Exposition":
            setting.setAttribute("Dose", "%e" % (Dose))
        self.layer.appendChild(setting)

    def add_rectangle(self, Name, DepthUnit="m", Center=[0, 0], Width=1e-6, Height=1e-6, Depth=5e-6, ExpositionFactor=1,
                      LineSettleFactor=1, Angle=0):
        """Add an outlined rectangle. It is scanned from bottom left corner,
counterclockwise    DepthUnit=["m","scan"]"""
        rectangle = self.document.createElement("Object")
        rectangle.setAttribute("Type", "RectangleOutline")
        rectangle.setAttribute("Name", Name)
        rectangle.setAttribute("DepthUnit", DepthUnit)
        rectangle.setAttribute("Center", "%e %e" % (Center[0], Center[1]))
        rectangle.setAttribute("Width", "%e" % (Width))
        rectangle.setAttribute("Height", "%e" % (Height))
        rectangle.setAttribute("Depth", "%e" % (Depth))
        rectangle.setAttribute("Angle", "%f" % (Angle))
        rectangle.setAttribute("ExpositionFactor", "%f" % (ExpositionFactor))
        rectangle.setAttribute("LineSettleFactor", "%f" % (LineSettleFactor))
        self.layer.appendChild(rectangle)

    def add_fill_rectangle(self, Name, DepthUnit="m", Center=[0, 0], Width=1e-6, Height=1e-6, Depth=5e-6,
                           ExpositionFactor=1, LineSettleFactor=1, Angle=0, ScanningPath=0):
        """Add a filled rectangle. Scanning starts in the bottom left corner, from left to
right.     Default unit is meter, degrees
DepthUnit=["m","scan"]
ScanningPath – scanning strategy flag. 0 – scan with flyback, 1 – zig-zag scanning.
Optional, default is 0."""
        rectangle = self.document.createElement("Object")
        rectangle.setAttribute("Type", "RectangleFilled")
        rectangle.setAttribute("Name", Name)
        rectangle.setAttribute("DepthUnit", DepthUnit)
        rectangle.setAttribute("Center", "%e %e" % (Center[0], Center[1]))
        rectangle.setAttribute("Width", "%e" % (Width))
        rectangle.setAttribute("Height", "%e" % (Height))
        rectangle.setAttribute("Depth", "%e" % (Depth))
        rectangle.setAttribute("Angle", "%f" % (Angle))
        rectangle.setAttribute("ExpositionFactor", "%f" % (ExpositionFactor))
        rectangle.setAttribute("LineSettleFactor", "%f" % (LineSettleFactor))
        rectangle.setAttribute("ScanningPath", "%d" % (ScanningPath))
        self.layer.appendChild(rectangle)

    def add_polish_rectangle(self, Name, DepthUnit="m", Center=[0, 0], Width=1e-6, Height=1e-6, Depth=5e-6,
                             ExpositionFactor=1, LineSettleFactor=1, Angle=0, ScanningPath=0):
        """Add a polishing rectangle. Only suitable for I-Etching. To achieve the required depth, scanning is not repeated for the whole object, but rather for each scan line. Scanning starts in the bottom left corner, from left to right.

Default unit is meter, degrees
DepthUnit=["m","scan"]
ScanningPath – scanning strategy flag. 0 – scan with flyback, 1 – zig-zag scanning. Optional, default is 0."""
        rectangle = self.document.createElement("Object")
        rectangle.setAttribute("Type", "RectanglePolish")
        rectangle.setAttribute("Name", Name)
        rectangle.setAttribute("DepthUnit", DepthUnit)
        rectangle.setAttribute("Center", "%e %e" % (Center[0], Center[1]))
        rectangle.setAttribute("Width", "%e" % (Width))
        rectangle.setAttribute("Height", "%e" % (Height))
        rectangle.setAttribute("Depth", "%e" % (Depth))
        rectangle.setAttribute("Angle", "%e" % (Angle))
        rectangle.setAttribute("ExpositionFactor", "%e" % (ExpositionFactor))
        rectangle.setAttribute("LineSettleFactor", "%e" % (LineSettleFactor))
        rectangle.setAttribute("ScanningPath", "%d" % (ScanningPath))
        self.layer.appendChild(rectangle)

    def add_polygon(self, Points, Name="Polyline", DepthUnit="m", Center=[0, 0], Angle=0, ScanAngle=0, Depth=5e-006,
                    ExpositionFactor=1, LineSettleFactor=1):
        """Add an outlined polygon. """
        polyline = self.document.createElement("Object")
        polyline.setAttribute("Name", Name)
        polyline.setAttribute("Type", "PolygonOutline")
        polyline.setAttribute("DepthUnit", DepthUnit)
        polyline.setAttribute("Depth", "%e" % (Depth))
        polyline.setAttribute("Angle", "%e" % (Angle))
        polyline.setAttribute("ScanAngle", "%e" % (ScanAngle))
        polyline.setAttribute("ExpositionFactor", "%e" % (ExpositionFactor))
        polyline.setAttribute("LineSettleFactor", "%e" % (LineSettleFactor))
        polyline.setAttribute("Center", "%e %e" % (Center[0], Center[1]))
        for p in Points:
            vertex = self.document.createElement("Vertex")
            vertex.setAttribute("Position", "%e %e" % (p[0], p[1]))
            polyline.appendChild(vertex)
        self.layer.appendChild(polyline)

    def add_fill_polygon(self, Name, Points, DepthUnit="m", Center=[0, 0], Angle=0, ScanAngle=0, Depth=5e-006,
                         ExpositionFactor=1, LineSettleFactor=1, ScanningPath=0):
        polygon = self.document.createElement("Object")
        polygon.setAttribute("Name", Name)
        polygon.setAttribute("Type", "PolygonFilled")
        polygon.setAttribute("DepthUnit", DepthUnit)
        polygon.setAttribute("Depth", "%e" % (Depth))
        polygon.setAttribute("Angle", "%e" % (Angle))
        polygon.setAttribute("ScanAngle", "%e" % (ScanAngle))
        polygon.setAttribute("ExpositionFactor", "%f" % (ExpositionFactor))
        polygon.setAttribute("LineSettleFactor", "%f" % (LineSettleFactor))
        polygon.setAttribute("ScanningPath", "%d" % (ScanningPath))
        polygon.setAttribute("Center", "%e %e" % (Center[0], Center[1]))
        for p in Points:
            vertex = self.document.createElement("Vertex")
            vertex.setAttribute("Position", "%e %e" % (p[0], p[1]))
            polygon.appendChild(vertex)
        self.layer.appendChild(polygon)

    def add_arc(self, Name, DepthUnit="m", Center=[0, 0], Depth=5e-006, Radius=5e-6, AngleA=0, AngleB=0, Orientation=0,
                ExpositionFactor=1, LineSettleFactor=1):
        """Makes a circle or arc. Orientation: 0 = c-clockwise,1 = clockwise """
        arc = self.document.createElement("Object")
        arc.setAttribute("Type", "ArcOutline")
        arc.setAttribute("Name", Name)
        arc.setAttribute("Center", "%e %e" % (Center[0], Center[1]))
        arc.setAttribute("DepthUnit", DepthUnit)
        arc.setAttribute("Depth", "%e" % (Depth))
        arc.setAttribute("Radius", "%e" % (Radius))
        arc.setAttribute("AngleA", "%f" % (AngleA))
        arc.setAttribute("AngleB", "%f" % (AngleB))
        arc.setAttribute("Orientation", "%d" % (Orientation))
        arc.setAttribute("ExpositionFactor", "%d" % (ExpositionFactor))
        arc.setAttribute("LineSettleFactor", "%d" % (LineSettleFactor))
        self.layer.appendChild(arc)

    def add_annulus(self, Name, DepthUnit="m", Center=[0, 0], Depth=5e-006, RadiusA=5e-6, RadiusB=2e-6, AngleA=0,
                    AngleB=0, Orientation=0, ExpositionFactor=1, LineSettleFactor=1):
        """filled circle, annulus or pie. Scanned from outside to the center. Orientation: 0 = c-clockwise,1 = clockwise """
        arc = self.document.createElement("Object")
        arc.setAttribute("Type", "AnnulusFilled")
        arc.setAttribute("Name", Name)
        arc.setAttribute("Center", "%e %e" % (Center[0], Center[1]))
        arc.setAttribute("DepthUnit", DepthUnit)
        arc.setAttribute("Depth", "%e" % (Depth))
        arc.setAttribute("RadiusA", "%e" % (RadiusA))
        arc.setAttribute("RadiusB", "%e" % (RadiusB))
        arc.setAttribute("AngleA", "%f" % (AngleA))
        arc.setAttribute("AngleB", "%f" % (AngleB))
        arc.setAttribute("Orientation", "%d" % (Orientation))
        arc.setAttribute("ExpositionFactor", "%f" % (ExpositionFactor))
        arc.setAttribute("LineSettleFactor", "%f" % (LineSettleFactor))
        self.layer.appendChild(arc)

    def add_polish_annulus(self, Name, DepthUnit="m", Center=[0, 0], Depth=5e-006, RadiusA=5e-6, RadiusB=2e-6, AngleA=0,
                           AngleB=0, Orientation=0, ExpositionFactor=1, LineSettleFactor=1):
        """polishing circle, annulus or pie. The typical use of this object is polishing
of thin pillars. Orientation: 0 = c-clockwise,1 = clockwise """
        arc = self.document.createElement("CirclePolish")
        arc.setAttribute("Name", Name)
        arc.setAttribute("Center", "%e %e" % (Center[0], Center[1]))
        arc.setAttribute("DepthUnit", DepthUnit)
        arc.setAttribute("Depth", "%e" % (Depth))
        arc.setAttribute("RadiusA", "%e" % (RadiusA))
        arc.setAttribute("RadiusB", "%e" % (RadiusB))
        arc.setAttribute("AngleA", "%f" % (AngleA))
        arc.setAttribute("AngleB", "%f" % (AngleB))
        arc.setAttribute("Orientation", "%d" % (Orientation))
        arc.setAttribute("ExpositionFactor", "%f" % (ExpositionFactor))
        arc.setAttribute("LineSettleFactor", "%f" % (LineSettleFactor))
        self.layer.appendChild(arc)

    def add_dot(self, Name="Point", DepthUnit="m", Center=[0, 0], Depth=5e-6, ExpositionFactor=1, LineSettleFactor=1):
        """Dot is a special case of polyline - with only one point
    DepthUnit=["m","scan"]"""
        self.add_polygon(Points=[Center, Center], Name=Name, DepthUnit=DepthUnit, Center=Center, Depth=Depth,
                         ExpositionFactor=1, LineSettleFactor=1)

    def add_line(self, Begin, End, Name="Line", DepthUnit="m", Depth=5e-6, ExpositionFactor=1, LineSettleFactor=1):
        """Add a dot to a parent object (e.g. Layer, Mesh, Group).
    DepthUnit=["m","scan"]"""
        self.add_polygon(Points=[Begin, End], Name=Name, DepthUnit=DepthUnit, Center=Begin, Depth=Depth,
                         ExpositionFactor=1, LineSettleFactor=1)

    def add_cross(self, parent, Name="Cross", DepthUnit="m", Center=[0, 0], Depth=5e-6, Width=5e-6, ExpositionFactor=1,
                  LineSettleFactor=1):
        """Add a dot to a parent object (e.g. Layer, Mesh, Group).
    DepthUnit=["m","scan"]"""
        self.add_line(Begin=[Center + Width / 2, Center], End=[Center - Width / 2, Center], Name=Name, DepthUnit="m",
                      Center=Center, Depth=Depth, ExpositionFactor=1, LineSettleFactor=1)
        self.add_line(Begin=[Center, Center + Width / 2], End=[Center, Center - Width / 2], Name=Name, DepthUnit="m",
                      Center=Center, Depth=Depth, ExpositionFactor=1, LineSettleFactor=1)

    def add_stairs_rectangle(self, Name, DepthUnit="m", Center=[0, 0], Width=1e-6, Height=1e-6, Depth=5e-6,
                             ExpositionFactor=1, LineSettleFactor=1, Angle=0, ScanningPath=0):
        """Add a filled rectangle. Scanning starts in the bottom left corner, from left to
right.     Default unit is meter, degrees
DepthUnit=["m","scan"]
ScanningPath – scanning strategy flag. 0 – scan with flyback, 1 – zig-zag scanning.
Optional, default is 0."""
        rectangle = self.document.createElement("Object")
        rectangle.setAttribute("Type", "RectangleFilled")
        rectangle.setAttribute("Name", Name)
        rectangle.setAttribute("DepthUnit", DepthUnit)
        rectangle.setAttribute("Center", "%e %e" % (Center[0], Center[1]))
        rectangle.setAttribute("Width", "%e" % (Width))
        rectangle.setAttribute("Height", "%e" % (Height))
        rectangle.setAttribute("Depth", "%e" % (Depth))
        rectangle.setAttribute("Angle", "%f" % (Angle))
        rectangle.setAttribute("ExpositionFactor", "%f" % (ExpositionFactor))
        rectangle.setAttribute("LineSettleFactor", "%f" % (LineSettleFactor))
        rectangle.setAttribute("ScanningPath", "%d" % (ScanningPath))
        self.layer.appendChild(rectangle)

    def save_xml(self, filename="project.xml"):
        outfile = open(filename, "w")
        outfile.write(self.document.toprettyxml(encoding="utf-8").decode())
        outfile.close()


def Example():
    """Makes a line"""
    proj = BeamSharkLayer("MyRectangles")
    proj.settings()
    proj.add_rectangle("Rectangle1", DepthUnit="m", Center=[0, 0], Width=4e-6, Height=4e-6, Depth=1e-6,
                       ExpositionFactor=1, LineSettleFactor=1, Angle=0)
    proj.add_rectangle("Rectangle2", DepthUnit="m", Center=[0, 0], Width=4e-6, Height=4e-6, Depth=1e-6,
                       ExpositionFactor=1, LineSettleFactor=1, Angle=45)
    proj.add_rectangle("Rectangle3", DepthUnit="m", Center=[0, 0], Width=10e-6, Height=10e-6, Depth=5e-7,
                       ExpositionFactor=1, LineSettleFactor=1, Angle=0)
    proj.add_rectangle("Rectangle4", DepthUnit="m", Center=[0, 0], Width=10e-6, Height=10e-6, Depth=5e-7,
                       ExpositionFactor=1, LineSettleFactor=1, Angle=45)
    print("writing as MyRectangle.xml")
    proj.save_xml("MyRectangle.xml")


if __name__ == '__main__':
    Example()
