import math
import random
import itertools
import collections
from coolname import generate_slug

Point = collections.namedtuple('Point', 'x y')


class SphericalCell:
    def __init__(self, id, vertices, level=0):
        self.id = id
        self.vertices = vertices  # 3 points on sphere
        self.level = level
        self.children = []
        self.elevation = None
        self.biome = None

    def subdivide(self):
        # Split into 4 child spherical triangles
        # Compute midpoints, project to sphere
        # Create child SphericalCells with new vertices
        pass

    def contains_point(self, point):
        # Test if point lies in this spherical triangle
        pass


class Planet(object):
    def __init__(self, name, seed=None):
        self.name = name
        self.seed = seed or random.randint(0, 99999999)
        self.position = Point(0, 0)
        self.credits = 0
        self.supply = {}
        self.production = {}
        self.contracts = []
        self.surface_map = None  # We'll generate this on demand

    def generate_subdivision_tree(self, depth=3):
        self.root_cells = []
        for face in icosahedron_faces():
            cell = SphericalCell(face_id, face_vertices)
            self.subdivide_recursively(cell, depth)
            self.root_cells.append(cell)

    def find_cell_containing_point(self, point, target_level):
        for root in self.root_cells:
            cell = self._find_in_tree(root, point, target_level)
            if cell:
                return cell
        return None

    def _find_in_tree(self, cell, point, target_level):
        if not cell.contains_point(point):
            return None
        if cell.level == target_level or not cell.children:
            return cell
        for child in cell.children:
            found = self._find_in_tree(child, point, target_level)
            if found:
                return found
        return None

    def latlon_to_xyz(lat, lon):
        phi = math.radians(90 - lat)
        theta = math.radians(lon)
        x = math.sin(phi) * math.cos(theta)
        y = math.sin(phi) * math.sin(theta)
        z = math.cos(phi)
        return (x, y, z)

    def generate_spherical_map(self, resolution=1000):
        """
        Generates a minimal spherical map using seeded noise.
        """
        import numpy as np
        from noise import pnoise3

        random.seed(self.seed)
        np.random.seed(self.seed)

        # Create a naive icosahedral or spherical grid
        # For now, let's just use random points on the sphere
        points = []
        for _ in range(resolution):
            theta = random.uniform(0, 2 * math.pi)
            phi = random.uniform(0, math.pi)
            x = math.sin(phi) * math.cos(theta)
            y = math.sin(phi) * math.sin(theta)
            z = math.cos(phi)
            points.append((x, y, z))

        # Generate noise-based elevation
        elevation = []
        scale = 3.0
        for (x, y, z) in points:
            n = pnoise3(x * scale, y * scale, z * scale, octaves=4,
                        repeatx=1024, repeaty=1024, repeatz=1024, base=self.seed)
            elevation.append(n)

        # Classify land/water
        threshold = 0.0
        land_water = ['land' if e > threshold else 'water' for e in elevation]

        self.surface_map = list(zip(points, elevation, land_water))


class StarSystem(object):
    """
    Model of a single star system where our game takes place. Planet position   
    is measured in gigameters. Our system will have a possible area of approx. 
    10000^2 Gm. For reference, the Aphelion of Neptune (the outermost planet in 
    the Sol System is 4,554 Gm, which gives our virtual planets roughly the 
    same area to work in. We strangely stick a planet at (0,0), the spot you'd 
    expect to see the star of the system, but since we aren't modelling orbits, 
    or sticking a trading post in the sun, this should be ok.
    """

    def __init__(self):
        self.planets = []
        self.distance_map = collections.defaultdict(dict)

    def randomize(self, n_planets=8):
        """
        Build an inital population of planets.       
        """
        for i in range(n_planets):
            p = Planet(name=generate_slug(2))
            if i != 0:
                p.position = Point(
                    random.randrange(-5000, 5000),
                    random.randrange(-5000, 5000)
                )
            p.credits = 100000
            self.planets.append(p)
        self.build_distance_map()

    def build_distance_map(self):
        """
        Caches a distance map from each planet to every other planet.
        This is an integer representing the number of turns it would take to 
        reach that planet assuming a speed of 1000 Gm per turn.
        """
        for a, b in itertools.combinations(self.planets, 2):
            dx2 = (b.position.x - a.position.x) ** 2
            dy2 = (b.position.y - a.position.y) ** 2
            dist = int((math.ceil(math.sqrt(dx2 + dy2) / 1000)))
            self.distance_map[a][b] = dist
            self.distance_map[b][a] = dist
