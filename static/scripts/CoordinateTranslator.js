import WarehouseModel from './WarehouseModel.js';

export default class CoordinateTranslator {
    canvasWidth = 0;
    canvasHeight = 0;
    verticalGridSize = 0;
    horizontalGridSize = 0;

    offsetX = 0;
    offsetY = 0;

    /**
     * Updates all pixel-to-grid relationships.
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

        // calculate the size of the grid dynamically
        this.verticalGridSize = (canvasHeight / totalGridUnitsV) * scale;
        this.horizontalGridSize = (canvasWidth / totalGridUnitsH) * scale;

        // --- Calculate Offsets ---
        const totalGridPixelWidth = model.numColumns * WarehouseModel.SHELF_TOTAL_WIDTH * this.horizontalGridSize;
        const totalGridPixelHeight = model.numCrossings * WarehouseModel.SHELF_TOTAL_HEIGHT * this.verticalGridSize;

        this.offsetX = (canvasWidth / 2) - (totalGridPixelWidth / 2);

        // Das Backend zaehlt Gitter-y vom Depot auf (0,0) weg nach oben, die
        // Zeichenflaeche zaehlt Pixel-y nach unten. Die Zeichnung wird deshalb
        // an der Waagerechten gespiegelt, sonst erscheint das Depot oben links
        // statt unten links. maxGridY ist der Index des obersten Quergangs,
        // offsetY die Pixelzeile genau dieser Gitterzeile.
        this.maxGridY = model.numCrossings * WarehouseModel.SHELF_TOTAL_HEIGHT;
        this.offsetY = (canvasHeight / 2) - (totalGridPixelHeight / 2);
    }

    /**
     * Converts a grid row to the pixel row of its upper edge. This is the only
     * place where the y-axis is mirrored.
     */
    gridYToPixel(gridY) {
        return this.offsetY + ((this.maxGridY - gridY) * this.verticalGridSize);
    }

    /**
     * Converts a backend grid coordinate (e.g., {x: 1, y: 1}) to a pixel coordinate.
     */
    gridToPixel(gridPos) {
        let x = ((gridPos.x) * this.horizontalGridSize) + this.offsetX;
        let y = this.gridYToPixel(gridPos.y);

        // Center the point in the grid cell
        x += 0.5 * this.horizontalGridSize;
        y += 0.5 * this.verticalGridSize;

        return {x, y};
    }

    /**
     * Gets the pixel position for the packing table.
     */

    getPackingTablePixelRect(model) {
        // table dimensions in grid units
        const tableWidthInGridUnits = 3;
        const tableHeightInGridUnits = 2;

        const width = tableWidthInGridUnits * this.horizontalGridSize;
        const height = tableHeightInGridUnits * this.verticalGridSize;


        const aislePixelWidth = WarehouseModel.AISLE_GRID_WIDTH * this.horizontalGridSize;

        // set the table on the left side, on the leftmost vertical aisle
        const positionX = this.offsetX + (aislePixelWidth / 2) - (width / 2);

        // Das Depot liegt auf (0,0), also am linken Ende des untersten
        // Quergangs, und wird ausserhalb des Gangnetzes gezeichnet. Der Kasten
        // sitzt deshalb 1,5 Zellen unterhalb dieses Quergangs. Das Mass in
        // Gitterzellen haelt den Abstand bei jeder Lagergroesse und in jeder
        // Zoomstufe gleich.
        const positionY = this.gridYToPixel(0) + (2.5 * this.verticalGridSize);

        return { x: positionX, y: positionY, w: width, h: height };
    }
}