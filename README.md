# Travelling Salesman Problem in Warehouse Networks

A Flask web application that solves the Travelling Salesman Problem (TSP) in warehouse environments. It compares three different algorithms — a greedy heuristic, an approximation algorithm, and an exact MILP solver — and visualizes the resulting pick routes on an interactive warehouse grid.

Built as part of my bachelor thesis in Computer Science at the Chair of Algorithms and Data Structure at the University of Freiburg.

![Warehouse Layout](static/img/screenshot_main.png)

![Algorithm Comparison](static/img/screenshot_comparison.png)

## Algorithms

| Algorithm | Type | Avg. Gap to Optimal | Worst Case | Avg. Time |
|---|---|---|---|---|
| Nearest Neighbor | Greedy heuristic (O(n²)) | +13.4% | +86.4% | ~5ms |
| Christofides | 3/2-approximation (O(n³)) | +8.2% | +30.5% | ~9ms |
| Fixed Parameter (MILP) | Exact optimal solution | 0% | 0% | ~12s |

*Benchmarked across 3,330 warehouse configurations with varying layouts and product counts.*

**Nearest Neighbor** always visits the closest unvisited location. Fast but can produce significantly suboptimal routes, especially in larger warehouses.

**Christofides** constructs a minimum spanning tree, finds a minimum weight perfect matching on odd-degree vertices (Blossom algorithm via NetworkX), and converts the resulting Eulerian circuit into a Hamiltonian tour. Guarantees solutions within 1.5x of optimal for metric TSP.

**Fixed Parameter (MILP)** is based on the Steiner TSP formulation by Cambazard & Catusse. It builds a graph of required and intermediate nodes, applies vertex/arc reduction preprocessing, and solves the resulting MILP (SCFS+ formulation) using PuLP/CBC. Finds the provably optimal solution with time complexity O(n * h * 5^h), where h is the warehouse grid height.

## Installation

```bash
git clone https://github.com/ConstiCode/bachelor_thesis.git
cd bachelor_thesis
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
python app.py
```

Open `http://localhost:5000` in your browser. Configure the warehouse layout (columns, rows), generate random stock locations, select one or more algorithms, and compare the resulting routes side by side.

## Running Tests

```bash
pytest tests/
```

## Architecture

### Backend (Python/Flask)

- `app.py` — Flask entry point with endpoints for location generation and route calculation
- `routes/` — Solver classes inheriting from a shared `BaseRoute` abstract class
  - `nearest_neighbor.py`, `christofides.py`, `fixed_parameter.py`
- `warehouse/grid.py` — Warehouse grid model with constant-time distance calculation
- `algorithms/a_star.py` — A* pathfinding for converting TSP visit sequences into walkable warehouse paths

### Frontend (Vanilla JavaScript)

MVC-style architecture with ES6 modules, no external libraries:

- `AppController.js` — Main controller coordinating user input, API calls, and rendering
- `WarehouseRenderer.js` — Canvas-based warehouse grid visualization
- `ModalView.js` — Side-by-side algorithm comparison view
- `CoordinateTranslator.js` — Grid-to-pixel coordinate mapping

## Technologies

- **Flask** — Web framework
- **NetworkX** — Graph operations (MST, Blossom matching)
- **PuLP** — MILP modeling with CBC solver
- **pytest** — Testing

## Author

GitHub: [ConstiCode](https://github.com/ConstiCode)
