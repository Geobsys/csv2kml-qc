import simplekml
kml = simplekml.Kml()
"""
### 3 plans
pol = kml.newpolygon(name='A Polygon', altitudemode='relativeToGround')
pol.outerboundaryis = [(2.4,48.65, 100), (2.4,48.7, 1500), (2.4,48.75, 100)]
pol.extrude = 1

pol = kml.newpolygon(name='A Polygon', altitudemode='relativeToGround')
pol.outerboundaryis = [(2.35,48.7, 100), (2.4,48.7, 1500), (2.45,48.7, 100)]
pol.extrude = 1

pol = kml.newpolygon(name='A Polygon', altitudemode='relativeToGround')
pol.outerboundaryis = [(2.4,48.65, 100), (2.35,48.7, 100), (2.4,48.75, 100), (2.45,48.7, 100)]
pol.extrude = 1

### pyramide

pol = kml.newpolygon(name='A Polygon', altitudemode='relativeToGround')
pol.outerboundaryis = [(2.35,48.7, 100), (2.4,48.7, 1500), (2.4,48.65, 100),(2.35,48.7, 100)]
pol.extrude = 0
pol = kml.newpolygon(name='A Polygon', altitudemode='relativeToGround')
pol.outerboundaryis = [(2.35,48.7, 100), (2.4,48.7, 1500), (2.4,48.75, 100),(2.35,48.7, 100)]
pol.extrude = 0
pol = kml.newpolygon(name='A Polygon', altitudemode='relativeToGround')
pol.outerboundaryis = [(2.45,48.7, 100), (2.4,48.7, 1500), (2.4,48.65, 100),(2.45,48.7, 100)]
pol.extrude = 0
pol = kml.newpolygon(name='A Polygon', altitudemode='relativeToGround')
pol.outerboundaryis = [(2.45,48.7, 100), (2.4,48.7, 1500), (2.4,48.75, 100),(2.45,48.7, 100)]
pol.extrude = 0
"""

# Boite
pol = kml.newpolygon(name='A Polygon', altitudemode='relativeToGround')
pol.outerboundaryis = [(2.35,48.7, 1500), (2.4,48.7, 1500), (2.4,48.65, 1500),(2.35,48.7, 1500)]
pol.extrude = 1


kml.save("Polygon3.kml")