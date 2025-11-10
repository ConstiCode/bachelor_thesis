import WarehouseModel from './WarehouseModel.js';
import CoordinateTranslator from './CoordinateTranslator.js';

export default class WarehouseRenderer {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext("2d");
        this.dpr = window.devicePixelRatio || 1;
        this.setupCanvas(this.canvas, this.ctx);

        // The main translator for the main canvas
        this.translator = new CoordinateTranslator();
    }

    /**
     * Sets up a canvas with correct DPR scaling.
     */
    setupCanvas(canvas, ctx) {
        let rect = canvas.getBoundingClientRect();
        canvas.width = rect.width * this.dpr;
        canvas.height = rect.height * this.dpr;
        ctx.scale(this.dpr, this.dpr);
        return {width: rect.width, height: rect.height};
    }

    /**
     * Clears the given canvas context.
     */
    clearCanvas(ctx, w, h) {
        ctx.clearRect(0, 0, w, h);
        ctx.fillStyle = "#1e1e1e";
        ctx.fillRect(0, 0, w, h);
    }

    /**
     * Renders the entire scene to the main canvas.
     */
    drawScene(model) {
        // 1. Update the translator with the main canvas dimensions
        const {width, height} = this.canvas.getBoundingClientRect();
        this.translator.update(model, width, height);

        // 2. Clear
        this.clearCanvas(this.ctx, width, height);

        // 3. Draw components
        this._drawShelves(this.ctx, model, this.translator);
        this._drawPackingTable(this.ctx, model, this.translator);
        this._drawPickingMarkers(this.ctx, model, this.translator);

        // 4. Draw routes
        for (const [algoName, data] of Object.entries(model.routes)) {
            const color = (algoName === 'christofides') ? 'yellow' : (algoName === 'nearestNeighbor') ? 'red' : 'pink';
            if (algoName === 'fixedParameter') {
                this._drawRouteSegments(this.ctx, data.route, color, this.translator);
            } else {
                this._drawWarehouseRoute(this.ctx, data.route, color, this.translator);
            }
        }
    }

    /**
     * THIS IS THE CORRECT MODAL LOGIC.
     * It renders a full scene to any target canvas, NOT by hijacking state.
     */
    renderToCanvas(targetCanvas, model, scale, locations, routeName, routeData) {
        const ctx = targetCanvas.getContext("2d");
        const {width, height} = this.setupCanvas(targetCanvas, ctx);

        const modalTranslator = new CoordinateTranslator();
        modalTranslator.update(model, width, height, scale);

        this.clearCanvas(ctx, width, height);
        this._drawShelves(ctx, model, modalTranslator);
        this._drawPackingTable(ctx, model, modalTranslator);

        this._drawPickingMarkers(ctx, {stockLocations: locations}, modalTranslator); // Pass a light-weight model

        const color = (routeName === 'christofides') ? 'yellow' : (routeName === 'nearestNeighbor') ? 'red' : 'pink';
        if (routeName === 'fixedParameter') {
            this._drawRouteSegments(ctx, routeData.route, color, modalTranslator);
        } else {
            this._drawWarehouseRoute(ctx, routeData.route, color, modalTranslator);
        }
    }

    _drawShelves(ctx, model, translator) {
        const shelfPixelWidth = WarehouseModel.SHELF_GRID_WIDTH * translator.horizontalGridSize;
        const shelfPixelHeight = WarehouseModel.SHELF_GRID_HEIGHT * translator.verticalGridSize;

        for (let r = 0; r < model.numCrossings; r++) {
            for (let c = 0; c < model.numColumns; c++) {

                let gridX = c * WarehouseModel.SHELF_TOTAL_WIDTH + WarehouseModel.AISLE_GRID_WIDTH;
                let gridY = r * WarehouseModel.SHELF_TOTAL_HEIGHT + WarehouseModel.AISLE_GRID_HEIGHT;

                // We need a different gridToPixel method for top-left corners, not centers
                // For now, I will use the offset directly.
                let pixelX = translator.offsetX + (gridX * translator.horizontalGridSize);
                let pixelY = translator.offsetY + (gridY * translator.verticalGridSize);

                ctx.beginPath();
                ctx.rect(pixelX, pixelY, shelfPixelWidth, shelfPixelHeight);
                ctx.fillStyle = "lightblue";
                ctx.fill();
            }
        }
    }

    _drawPackingTable(ctx, model, translator) {
        const rect = translator.getPackingTablePixelRect(model);

        ctx.beginPath();
        ctx.rect(rect.x, rect.y, rect.w, rect.h);
        ctx.fillStyle = "lightblue";
        ctx.fill();

        let fontSize = Math.floor(45 / model.numColumns); // Still a bit magic, but better
        ctx.font = `${fontSize}px Arial`;
        ctx.fillStyle = "black";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";

        let textX = rect.x + rect.w / 2;
        let textY = rect.y + rect.h / 2;
        ctx.fillText("Packing Table", textX, textY);
    }

    _drawPickingMarkers(ctx, model, translator) {
        for (const loc of model.stockLocations) {
            const pos = translator.gridToPixel(loc);

            ctx.beginPath();
            ctx.arc(pos.x, pos.y, Math.max(translator.horizontalGridSize, translator.verticalGridSize) / 12, 0, 2 * Math.PI);
            ctx.stroke();
            ctx.fillStyle = "red";
            ctx.fill();
        }
    }

    _drawWarehouseRoute(ctx, route, color, translator) {
        if (!route || route.length === 0) return;

        ctx.beginPath();
        const start = translator.gridToPixel({x: route[0][0], y: route[0][1]});
        ctx.moveTo(start.x, start.y);

        for (const point of route) {
            const pos = translator.gridToPixel({x: point[0], y: point[1]});
            ctx.lineTo(pos.x, pos.y);
        }
        ctx.strokeStyle = color;
        ctx.lineWidth = 3;
        ctx.stroke();
    }

    _drawRouteSegments(ctx, segments, color, translator) {
        if (!segments || segments.length === 0) {
            return;
        }

        // Set the drawing style once
        ctx.strokeStyle = color;
        ctx.lineWidth = 3;

        // Loop through the segments array, taking two points at a time
        // i will be 0, 2, 4, ...
        for (let i = 0; i < segments.length; i += 2) {

            // Make sure we have a pair of points
            if (i + 1 >= segments.length) {
                // This happens if there's an odd number of points
                break;
            }

            // Get the start and end points for *this segment*
            const point1 = segments[i];
            const point2 = segments[i + 1];

            // Convert grid coordinates to pixel coordinates
            const start = translator.gridToPixel({x: point1[0], y: point1[1]});
            const end = translator.gridToPixel({x: point2[0], y: point2[1]});

            // --- This is the important part ---

            // 1. Start a new, completely separate path
            ctx.beginPath();
            // 2. Move the "pen" to the start of this segment
            ctx.moveTo(start.x, start.y);
            // 3. Draw a line to the end of this segment
            ctx.lineTo(end.x, end.y);
            // 4. Render this segment to the canvas immediately
            ctx.stroke();
        }
    }
}