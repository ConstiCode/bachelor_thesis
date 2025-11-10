import WarehouseModel from './WarehouseModel.js';

export default class CoordinateTranslator {
    // --- Pixel-space properties ---
    canvasWidth = 0;
    canvasHeight = 0;
    verticalGridSize = 0;
    horizontalGridSize = 0;

    // --- Grid-space offset properties ---
    // These are the top-left pixel coordinates of grid position (0, 0)
    offsetX = 0;
    offsetY = 0;

    /**
     * Recalculates all pixel-to-grid relationships.
     * @param {WarehouseModel} model - The data model
     * @param {number} canvasWidth - The pixel width of the target canvas
     * @param {number} canvasHeight - The pixel height of the target canvas
     * @param {number} scale - The drawing scale (for modals)
     */
    update(model, canvasWidth, canvasHeight, scale = 1.0) {
        this.canvasWidth = canvasWidth;
        this.canvasHeight = canvasHeight;

        const marginVertical = 20;
        const marginHorizontal = 20;

        // Calculate total grid units needed
        const totalGridUnitsV = (model.numCrossings * WarehouseModel.SHELF_TOTAL_HEIGHT) + marginVertical;
        const totalGridUnitsH = (model.numColumns * WarehouseModel.SHELF_TOTAL_WIDTH) + marginHorizontal;

        // Calculate pixel size of one grid unit
        this.verticalGridSize = (canvasHeight / totalGridUnitsV) * scale;
        this.horizontalGridSize = (canvasWidth / totalGridUnitsH) * scale;

        // --- Calculate Offsets ---
        // This logic was buried in drawStorageShelfRow and drawStorageShelfFloorPlan
        const totalGridPixelWidth = model.numColumns * WarehouseModel.SHELF_TOTAL_WIDTH * this.horizontalGridSize;
        const totalGridPixelHeight = model.numCrossings * WarehouseModel.SHELF_TOTAL_HEIGHT * this.verticalGridSize;

        const startX = (canvasWidth / 2) - (totalGridPixelWidth / 2);

        // Y-axis is inverted (0 is top)
        const startY = (canvasHeight / 2) + (totalGridPixelHeight / 2);

        // This is the new, reliable "normalizedCoordinate"
        // It's the pixel coordinate for the top-left of the *entire grid structure*.
        this.offsetX = startX;
        this.offsetY = startY - ((model.numCrossings - 1) * WarehouseModel.SHELF_TOTAL_HEIGHT * this.verticalGridSize);

        // ... This math might need tweaking, but the *structure* is correct.
        // The point is to isolate it here.
    }

    /**
     * Converts a backend grid coordinate (e.g., {x: 1, y: 1}) to a pixel coordinate.
     */
    gridToPixel(gridPos) {
        // This logic was in drawPickingMarkers
        // Note: The -1 is because your grid seems to be 1-indexed
        let x = ((gridPos.x) * this.horizontalGridSize) + this.offsetX;
        let y = ((gridPos.y) * this.verticalGridSize) + this.offsetY;

        // Center the point in the grid cell
        x += 0.5 * this.horizontalGridSize;
        y += 0.5 * this.verticalGridSize;

        return {x, y};
    }

    /**
     * Gets the pixel position for the packing table.
     */
// Inside your CoordinateTranslator.js class

getPackingTablePixelRect(model) {

    // --- 1. Define Table Dimensions ---
    // (You can change these values)
    const tableWidthInGridUnits = 3;
    const tableHeightInGridUnits = 2;

    const width = tableWidthInGridUnits * this.horizontalGridSize;
    const height = tableHeightInGridUnits * this.verticalGridSize;

    // --- 2. Find the Top-Left Aisle Block ---

    // From _drawShelves, we know the first aisle's width in pixels:
    const aislePixelWidth = WarehouseModel.AISLE_GRID_WIDTH * this.horizontalGridSize;

    // And the first aisle's height in pixels:
    const aislePixelHeight = WarehouseModel.AISLE_GRID_HEIGHT * this.verticalGridSize;

    // --- 3. Calculate Table Position (Centered in Aisle) ---

    // Center the table horizontally within the left aisle
    const positionX = this.offsetX + (aislePixelWidth / 2) - (width / 2);

    // Center the table vertically within the top aisle
    const positionY = (this.offsetY + (aislePixelHeight / 2) - (height / 2)) - 100;

    return { x: positionX, y: positionY, w: width, h: height };
}
}