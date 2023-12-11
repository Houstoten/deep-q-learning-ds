/// Constants
var MAP_STATES = {
    default: 0,
    fixed: 1,
    movable: 2
};
var SELECTION_TYPES = {
    ENEMY: 0,
    ALLY: 1
};
var DETALISATION_POINTS = {
    1: 5,
    2: 7,
    3: 10,
    4: 12,
    5: 15,
    6: 18,
    7: 20,
    8: 23,
    9: 27,
    10: 30,
    11: 35, 
    12: 40
};
var ANALYSIS_STATUSES = {
    NOT_STARTED: 0,
    IN_PROGRESS: 1,
    DONE: 2
}
// Colors
var ENEMY_COLOR = 'rgba(255, 10, 10, 0.25)';
var ALLY_COLOR = 'rgba(10, 255, 10, 0.15)';

/// Elements
var mapElement = document.getElementById('map');
var mapWrapperElement = document.getElementById('map-wrapper');
var gridElement = document.getElementById('grid-wrapper');
// Options elements
var fixBtnElement = document.getElementById('fix-btn');
var detalisationRangeElement = document.getElementById('details-range');
var radioSelectionTypeElementsList = document.getElementsByName('troop_selection');
var radioAllySelectionElement = document.getElementById('ally_troop_radio_label');
var radioEnemySelectionElement = document.getElementById('enemy_troop_radio_label');
var enemyPowerElement = document.getElementById('enemy_power');
var allyPowerElement = document.getElementById('ally_power');
var enemyQuantityElement = document.getElementById('enemy_quantity');
var allyQuantityElement = document.getElementById('ally_quantity');
var startAnalysisBtnElement = document.getElementById('run-btn');

/// State
var map;
var map_bounds = {};
var map_zoom = 5;
var map_current_state = MAP_STATES.default;
var detalisation = 1;
var selectionType = SELECTION_TYPES.ENEMY;
var selectionState = {};
var analysis_status = ANALYSIS_STATUSES.NOT_STARTED;
//
var markers = [];

toggleConfigControls(false);

window.initMap = function() {
    map = new google.maps.Map(mapElement, getMapOpts(map_current_state));
    if (markers && markers.length) {
        addMarkers();
    }
    console.log(Date(), 'Map initialized');
    map.addListener('idle', mapIdle);
};

/// When map was touched, and now remains idle, saving current state
window.mapIdle = function() {
    // Coords
    let bounds = map.getBounds();
    let ne = bounds.getNorthEast();
    let sw = bounds.getSouthWest();
    map_bounds.ne = {lat: ne.lat(), lng: ne.lng()};
    map_bounds.sw = {lat: sw.lat(), lng: sw.lng()};
    map_bounds.nw = {lat: ne.lat(), lng: sw.lng()};
    map_bounds.se = {lat: sw.lat(), lng: ne.lng()};
    map_bounds.center = bounds.getCenter();
    // Zoom
    map_zoom = map.getZoom();

    //console.log(Date(), 'Current Bounds:', bounds);
    console.log(Date(), 'Objected bounds', map_bounds);
};

window.changeDetails = function(value) {
    detalisation = value;
    refreshGrid();
};

function fixMap() {
    let toggler = true;
    if (map_current_state == MAP_STATES.movable || map_current_state == MAP_STATES.default) {
        map_current_state = MAP_STATES.fixed;
        fixBtnElement.innerHTML = '<i class="fa-solid fa-lock-open fa-sm"></i> Unfix map';
    }
    else {
        map_current_state = MAP_STATES.movable;
        fixBtnElement.innerHTML = '<i class="fa-solid fa-lock fa-sm"></i> Fix map';
        resetSelections();
        toggler = false;
    }
    toggleConfigControls(toggler);
    toggleGrid(toggler);
    map.setOptions(getMapOpts(map_current_state));
    map.addListener('idle', mapIdle);
    refreshGrid();
}

function addMarkers() {
    for (const marker of markers) {
        let markerObj = new google.maps.Marker({...marker, map: map});
        markerObj.setMap(map);
    }
}
function runAnalysis() {
    let allyPower = allyPowerElement.value;
    let enemyPower = enemyPowerElement.value;
    let allyQuantity = allyQuantityElement.value;
    let enemyQuantity = enemyQuantityElement.value;
    let allySelection = [];
    let enemySelection = [];
    let N = DETALISATION_POINTS[detalisation];
    for (let i = 0; i < N * N; i++) {
        if (selectionState['cell_' + i] == SELECTION_TYPES.ENEMY) {
            enemySelection.push({x: i % N, y: Math.floor(i / N)});
        }
        else if (selectionState['cell_' + i] == SELECTION_TYPES.ALLY) {
            allySelection.push({x: i % N, y: Math.floor(i / N)});
        }
    }
    let bounds_obj = map.getBounds().toJSON();
    let data = {
        ...bounds_obj,
        'ally_power': allyPower,
        'enemy_power': enemyPower,
        'ally_quantity': allyQuantity,
        'enemy_quantity': enemyQuantity,
        'ally_selection': allySelection,
        'enemy_selection': enemySelection,
        'N': N
    };
    console.log(Date(), 'Analysis data:', data);
    $.ajax({
        type: 'POST',
        url: '/analyze',
        data: JSON.stringify(data),
        contentType: 'application/json;charset=UTF-8',
        success: (response) => {
            console.log(Date(), 'Analysis response:', response);
            for (const path of response) {
                for (const point of path) {
                    const marker = {
                        position: new google.maps.LatLng(point.lat, point.lng),
                        title: "One step of ally units"
                    };
                    markers.push(marker);
                }
            }
            analysis_status = ANALYSIS_STATUSES.DONE;
            startAnalysisBtnElement.disabled = false;
            addMarkers();
        }
    });
    analysis_status = ANALYSIS_STATUSES.IN_PROGRESS;

    startAnalysisBtnElement.disabled = true;
}

function toggleGrid(enable = true) {
    if (enable) {
        gridElement.style.display = 'grid';
        gridElement.style.zIndex = 3;
    }
    else {
        gridElement.style.display = 'none';
    }
}

function handleGridSelection(event) {
    let id = event.target.id;
    let cell = document.getElementById(id);
    if (cell.checked || (selectionState[id] != selectionType)) {
        selectionState[id] = selectionType;
        let backgroundStyle = '';
        if (selectionType == SELECTION_TYPES.ENEMY) {
            backgroundStyle = ENEMY_COLOR;
        }
        else if (selectionType == SELECTION_TYPES.ALLY) {
            backgroundStyle = ALLY_COLOR;
        }
        cell.style.backgroundColor = backgroundStyle;
    }
    else {
        delete selectionState[id];
        cell.style.backgroundColor = 'transparent';
    }
    checkDataToStartAnalysis();
}

function selectionTypeChange(value) {
    if (value == 'enemy') {
        selectionType = SELECTION_TYPES.ENEMY;
        radioEnemySelectionElement.classList.remove('btn-outline-danger');
        radioEnemySelectionElement.classList.add('btn-danger');
        radioAllySelectionElement.classList.remove('btn-success');
        radioAllySelectionElement.classList.add('btn-outline-success');
    }
    else if (value == 'ally') {
        selectionType = SELECTION_TYPES.ALLY;
        radioAllySelectionElement.classList.remove('btn-outline-success');
        radioAllySelectionElement.classList.add('btn-success');
        radioEnemySelectionElement.classList.remove('btn-danger');
        radioEnemySelectionElement.classList.add('btn-outline-danger');
    }
}

function resetSelections() {
    selectionState = {};
    refreshGrid();
    checkDataToStartAnalysis();
}

function refreshGrid() {
    if (map_current_state != MAP_STATES.fixed) 
        return;
    console.log(Date(), 'refreshing')
    // Clear grid
    clearChildren(gridElement);

    // Fill grid
    let mapWidth = mapWrapperElement.offsetWidth;
    let N = DETALISATION_POINTS[detalisation];
    for (let i = 0; i < N * N; i++) {
        let checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.id = 'cell_' + i;
        checkbox.style.display = 'block';
        checkbox.style.width = checkbox.style.height = (mapWidth / N) + 'px';
        checkbox.classList.add('grid-selection-checkbox');
        checkbox.addEventListener('click', handleGridSelection);
        gridElement.appendChild(checkbox);
    }

    // Update grid style
    gridElement.style.zIndex = 3;
    gridElement.style.gridTemplateColumns = 'repeat(' + N + ', 1fr)';
    gridElement.style.gridTemplateRows = 'repeat(' + N + ', 1fr)';
}

function toggleConfigControls(enable = true) {
    detalisationRangeElement.disabled = !enable;
    for (let i = 0; i < radioSelectionTypeElementsList.length; i++) {
        radioSelectionTypeElementsList[i].disabled = !enable;
    }
    allyPowerElement.disabled = !enable;
    enemyPowerElement.disabled = !enable;
    allyQuantityElement.disabled = !enable;
    enemyQuantityElement.disabled = !enable;
}

function checkDataToStartAnalysis() {
    let checker = allyPowerElement.value && enemyPowerElement.value && allyQuantityElement.value && enemyQuantityElement.value && Object.keys(selectionState).length;
    startAnalysisBtnElement.disabled = !checker;
    //toggleConfigControls(false);
    //toggleGrid(false);
    return checker; 
}

function getMapOpts(variant) {
    let location;
    let baseOpts = {
        zoom: map_zoom,
        draggable: true,
        scrollwheel: true,
        zoomControl: true,
        disableDoubleClickZoom: false,
        streetViewControl: false,
        fullscreenControl: false,
        mapTypeId: 'hybrid', // Sets the map type to Satellite
        mapTypeControl: false,   // Disables the map type control
        minZoom: 6,
        maxZoom: 16,
        restriction: {
            latLngBounds: {
              north: 53,
              south: 44,
              east: 41,
              west: 22,
            },
          },
    }
    if (!variant || variant == MAP_STATES.default) {
        location = {lat: 50.450001, lng: 30.523333}; // Kyiv
        return {
            ...baseOpts,
            center: location
        };
    }
    else if (variant == MAP_STATES.fixed) {
        location = map_bounds.center;
        return {
            ...baseOpts,
            center: location,
            draggable: false,
            zoomControl: false,     // Hides zoom controls
            scrollwheel: false,     // Prevents zooming with the mouse scroll wheel
            disableDoubleClickZoom: true // Prevents zooming on double click
        }
    }
    else if (variant == MAP_STATES.movable) {
        location = map_bounds.center;
        return {
            ...baseOpts,
            center: location,
        }
    }
}

function clearChildren(element) {
    let child = element.lastElementChild;
    while (child) {
        element.removeChild(child);
        child = element.lastElementChild;
    }
}
