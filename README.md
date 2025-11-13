# Travelling Salesman Problem in Warehouse Networks

This repository contains the implementation of a flask app that allows users to generate warehouse router solving 
problems by generating random locations the travelling salesman must visit. For comparison there are 3 algorithms the 
User can choose from to solve the problem:

1. Nearest Neighbour Algorithm (Heuristical Approach)
2. Christofides Algorithm (3/2-approximation algorithm)
3. Steiner TSP Dynamic Programming Approach (Hadrien Cambazard and Nicolas Catusse)


Todo add Sceenshots of the frontend here

## Installation and setup
Todo 


## Algorithms implemented

### Nearest Neighbour Algorithm
The Nearest Neighbor algorithm is a simple heuristic for solving the Traveling Salesman Problem (TSP). 
The algorithm starts at a specified node(packer table) and repeatedly visits the nearest unvisited node until all nodes 
have been visited. While this approach is easy to implement and runs quickly, it does not guarantee an optimal solution 
and can produce suboptimal tours.
The implementation in this project is basd on optimized distance calculation, which is closely related to the manhattan 
distance, but adapted to the warehouse grid structure. It calculates the distance between two given points in constant 
time. Theta(1)
As the Nearst Neighbor algorithm iterates through all unvisited nodes to find the nearest one, the overall time 
complexity of the algorithm is O(n²), where n is the number of nodes (locations to visit).


### Christofides Algorithm
The Christofides algorithm is a well-known approximation algorithm for solving the Traveling Salesman Problem (TSP) that
guarantees a solution within 1.5 times the optimal solution for metric TSP instances. The algorithm consists of the 
following main steps:
1. Construct a Minimum Spanning Tree (MST) of the graph.
2. Find all vertices with odd degree in the MST.
3. Find a Minimum Weight Perfect Matching (MWPM) for the odd-degree vertices.
4. Combine the edges of the MST and the MWPM to form a multigraph.
5. Find an Eulerian circuit in the multigraph.
6. Convert the Eulerian circuit into a Hamiltonian circuit by skipping repeated vertices.
The time complexity of the Christofides algorithm is O(n^3), where n is the number of nodes (locations to visit).

This is primarily due to the steps involved in finding the Minimum Weight Perfect Matching, which can be computationally
intensive.


### Steiner TSP Dynamic Programming Approach
The Steiner TSP Dynamic Programming Approach is the core algorithm implemented in this project. It is based on the work 
of Hadrien Cambazard and Nicolas Catusse. This algorithm is designed to solve the Traveling Salesman Problem (TSP) in a
more efficient manner by leveraging dynamic programming techniques.
The algorithm systematically explores the edges of a given warehouse grid, and systematically builds a state space
representing all possible sub-paths through the grid. By using different pruning techniques, the algorithm is able to 
significantly reduce time complexity compared to traditional TSP solver approaches. 
The algorithm has a time complexity of O(nh5⁽h⁾), where n is the number of nodes (locations to visit) and h is the 
height of the warehouse grid.



## Features and Usage 
## Thesis context and results

## Overall Code Architecture

### Frontend JavaScript Architecture

![img.png](static/img/frontend_architecture.png)


The frontend is split into the following models:
- main.js: Calls the AppController
- AppController.js: Main controller that handles user input and communicates with the backend
    - **_handleFloorPlanChange()**: fetches the new floor plan from the main view updates the model and pases the new layout to the renderer
    - **_handleGenerateLocations()**: fetches the api call to generate new random locations from the flask backend via the ApiService and draws them via the Renderer
    - **_handleCalculateRoute()**: fetches the api call via the ApiService model and renders the routes via the renderer
- CoordinateTranslator.js: Translates the coordinates from the backend onto the canvas 
  - **update()**: recalculates all the pixel to coordinate relationships based on the current warehouse layout and canvas size
  - **gridToPixel()**: translates grid coordinates to pixel coordinates
  - **getPackingTablePixelRect()**: calculates the position for the packing tables and returns their coordinates in pixel values
- domUtils.js: Contains helper functions for DOM manipulation
  - **addLocationToTable()**: adds a new location to the location table in the UI
  - **updateRouteInfoTable()**: updates the location table with new locations
- mainView.js: Manages the main view of the application
  - **getFloorPlanConfig()**: a getter for the layout configuration of the warehouse
  - **getLocationCount()**: a getter for the number of locations
  - **clearData()**: clears all the data from the view
  - **renderLocations()**: renders the generated locations on the canvas
  - **showError()**: displays error messages to the user
  - **bindChangeFloorPlan()**: Todo understand binds the floor plan change event to the controller
  - **bindGenerateLocations()**: Todo understand binds the generate locations button to the controller
  - **bindCalculateRoute()**: Todo understand binds the calculate route button to the controller
  - **getSelectedAlgorithm()**: Todo understand retrieves the selected algorithm from the UI
- ModalView.js: manages the comparison modal view
  - **show()**: displays the modal and draws the canvases 
  - **hide()**: hides the modal
  - **_bindEventListeners()**: defines the event listeners for the modal buttons
- WareHouseModel.js: represents the warehouse model
  - **updateDimensions()**: updates the warehouse layout based on user input
  - **setStockLocations()**: generates random locations within the warehouse layout
  - **setRoutes()**: sets the calculated routes for the warehouse
  - **getConfigForAPI()**: prepares the warehouse configuration for API calls

### Backend Python Architecture

The python backend is coherent to the recommended flask application structure.
- app.py: Main entry point of the application that initializes the Flask app and listens for incoming requests.
    - **/api/generate_locations**: API endpoint to generate random stock locations
    - **/api/calculate_route**: API endpoint to calculate the route based on the selected algorithms. The Endpoint generates 
a route instance for each selected algorithm and returns the results to the frontend.

- /routes: Contains the route calculation solvers
  - base.py: Abstract base class for all route solvers that ensures a consistent interface
  - christofides.py: Implementation of the Christofides algorithm for TSP
  - nearest_neighbour.py: Implementation of the Nearest Neighbour heuristic for TSP
  - fixed_parameter.py: Implementation of the Steiner TSP Dynamic Programming Approach

- /warehouse: Contains the warehouse model and related utilities
  - warehouse.py: defines the grid class that represents the warehouse layout and stock locations
  - utils.py: Contains utility functions for warehouse operations, such as distance calculations


## Technologies Used

The following technologies were used in the development of this project:
- Python
- Flask
- HTML/CSS/JavaScript for the frontend
- python libraries: heapq, math, abc, collections, pytest, random, time
- canvas



## License and Contact
Author: Constantin Dietrich

E-Mail: constantindietrich@hotmail.de
