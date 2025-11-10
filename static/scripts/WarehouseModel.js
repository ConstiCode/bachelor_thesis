export default class WarehouseModel {
    // --- LAYOUT CONSTANTS (NO MORE MAGIC NUMBERS) ---
    static SHELF_GRID_HEIGHT = 6;
    static SHELF_GRID_WIDTH = 2;
    static AISLE_GRID_HEIGHT = 1;
    static AISLE_GRID_WIDTH = 1;
    static SHELF_TOTAL_HEIGHT = this.SHELF_GRID_HEIGHT + this.AISLE_GRID_HEIGHT; // 7
    static SHELF_TOTAL_WIDTH = this.SHELF_GRID_WIDTH + this.AISLE_GRID_WIDTH;   // 3

    // --- STATE ---
    numColumns = 0;
    numCrossings = 0;
    stockLocations = [];
    routes = {}; // e.g., { christofides: { route: [], ... } }

    constructor(initialCols, initialRows) {
        this.updateDimensions(initialCols, initialRows);
    }

    /**
     * Updates the core layout dimensions.
     */
    updateDimensions(cols, rows) {
        this.numColumns = parseInt(cols, 10);
        this.numCrossings = parseInt(rows, 10);
        this.stockLocations = []; // Reset state
        this.routes = {};         // Reset state
    }

    /**
     * Sets the generated stock locations.
     */
    setStockLocations(locations) {
        this.stockLocations = locations;
    }

    /**
     * Sets the calculated route data.
     */
    setRoutes(routeData) {
        this.routes = routeData;
    }

    /**
     * Generates a minimal config object to send to the backend.
     * THIS is the correct API contract.
     */
    getConfigForAPI() {
        return {
            numColumns: this.numColumns,
            numCrossings: this.numCrossings,
            layout: {
                shelfHeight: WarehouseModel.SHELF_GRID_HEIGHT,
                shelfWidth: WarehouseModel.SHELF_GRID_WIDTH,
                aisleHeight: WarehouseModel.AISLE_GRID_HEIGHT,
                aisleWidth: WarehouseModel.AISLE_GRID_WIDTH
            }
        };
    }
}