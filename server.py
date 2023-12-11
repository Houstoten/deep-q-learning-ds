from flask import Flask, request, jsonify, render_template, url_for, Response
from geoservice import GeoService
from battlefield import Pos, Unit, Enemy
import numpy as np
import requests
import random
import tryplay
import jsonpickle


app = Flask(__name__)

def download_water_data(east, north, south, west):
    print('Downloading water data...')
    overpass_url = "https://overpass-api.de/api/interpreter"
    overpass_query = f"""
    [out:json][timeout:25];
    // gather results
    (
    // query part for: “water=*”
    node["water"]({south},{west},{north},{east});
    way["water"]({south},{west},{north},{east});
    relation["water"]({south},{west},{north},{east});
    );
    // print results
    out body;
    >;
    out skel qt;
    """
    response = requests.get(overpass_url, params={'data': overpass_query})
    return response.json()

def create_standardized_grid(original_grid, key='elevation'):
    # Find the minimum and maximum elevation values
    elevations = [cell[key] for cell in original_grid if cell[key] is not None]
    min_elevation = min(elevations)
    max_elevation = max(elevations)

    new_grid = []
    for cell in original_grid:
        new_cell = cell.copy()  # Copy the original cell data
        elevation = cell[key]

        # Standardize the elevation
        if elevation is not None:
            standardized_elevation = (elevation - min_elevation) / (max_elevation - min_elevation) * 0.9
            new_cell[key] = standardized_elevation

        # Set elevation to 1 if the cell has water
        if cell.get('IsWater'):
            new_cell[key] = 1

        new_grid.append(new_cell)

    return new_grid

def create_elevation_matrix(data):
    # Determine the size of the matrix
    max_x = max(item['x'] for item in data) + 1  # +1 because indices start at 0
    max_y = max(item['y'] for item in data) + 1

    # Initialize the matrix with zeros
    elevation_matrix = np.zeros((max_x, max_y))

    # Populate the matrix with elevation data
    for item in data:
        x, y = item['x'], item['y']
        elevation_matrix[x][y] = item['elevation']

    return elevation_matrix

def create_ally_enemy_lists(data, ally_power, enemy_power):
    ally_list = []
    enemy_list = []

    for item in data:
        print(item, item)
        pos = Pos(item['x'], item['y'])

        if 'IsEnemy' in item and item['IsEnemy']:
            enemy_list.append(Enemy(enemy_power, pos))

        if 'IsAlly' in item and item['IsAlly']:
            ally = Unit(ally_power * 10, ally_power*10, pos)
            ally_list.append(ally)

    return ally_list, enemy_list


@app.route('/')
def home():
    return render_template('index.html')

'''
  {
    "south": 39.56620259621001,
    "west": 18.733886718750007,
    "north": 56.43417324253683,
    "east": 44.26611328125001,
    "ally_power": "4",
    "enemy_power": "4",
    "ally_quantity": "4",
    "enemy_quantity": "4",
    "ally_selection": [
        {
            "x": 2,
            "y": 1
        }
    ],
    "enemy_selection": [
        {
            "x": 1,
            "y": 1
        }
    ],
    "N": 5
}
}
'''

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    south, west, north, east = data['south'], data['west'], data['north'], data['east']
    southwest, northeast = (south, west), (north, east)
    rows, cols = data['N'], data['N']
    ally_power, enemy_power = int(data['ally_power']), int(data['enemy_power'])
    ally_quantity, enemy_quantity = data['ally_quantity'], data['enemy_quantity']
    ally_selection, enemy_selection = data['ally_selection'], data['enemy_selection']
    water_data = download_water_data(east, north, south, west)

    grid = GeoService.create_grid(southwest, northeast, rows, cols, water_data)
    for cell in grid:
        if not 'elevation' in list(cell.keys()):
            cell['elevation'] = 100 * random.random()
        if len(list(filter(lambda x: x['x'] == cell['x'] and x['y'] == cell['y'], ally_selection))) > 0:
            cell['IsAlly'] = True
            cell['IsEnemy'] = False
            cell['Power'] = ally_power
            cell['Quantity'] = ally_quantity
        if len(list(filter(lambda x: x['x'] == cell['x'] and x['y'] == cell['y'], enemy_selection))) > 0:
            cell['IsAlly'] = False
            cell['IsEnemy'] = True
            cell['Power'] = enemy_power
            cell['Quantity'] = enemy_quantity
    standartizedElevationGrid = create_standardized_grid(grid)

    battlemap = create_elevation_matrix(standartizedElevationGrid)
    allies, enemies = create_ally_enemy_lists(grid, ally_power, enemy_power)
    dataToPass = {
        'N': data['N'],
        'battlemap': battlemap,
        'allies': allies,
        'enemies': enemies,
    }
    for enemy in dataToPass['allies']:
        print(enemy.pos.x, enemy.pos.y, '  ', enemy.health)

    #print(dataToPass)
    resultPath = tryplay.play(dataToPass)
    endDrawPath = []
    for i, unitPath in enumerate(resultPath):
        endDrawPath.append([])
        for coord in unitPath:
            point = list(filter(lambda cell: cell['x'] == coord.x and cell['y'] == coord.y, grid))[0]['center']
            point = {'lat': point[0], 'lng': point[1]}
            endDrawPath[i].append(point)

    return Response(jsonpickle.encode(endDrawPath, make_refs=False, unpicklable=False), status=201, mimetype='application/json')

app.run(port=5025)