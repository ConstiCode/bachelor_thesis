import WarehouseModel from './WarehouseModel.js';
import CoordinateTranslator from './CoordinateTranslator.js';

export default class WarehouseRenderer {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext("2d");
        this.dpr = window.devicePixelRatio || 1;
        this.setupCanvas(this.canvas, this.ctx);

        // translator for the main canvas
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
        // update translator
        const {width, height} = this.canvas.getBoundingClientRect();
        this.translator.update(model, width, height);

        this.clearCanvas(this.ctx, width, height);

        // draw components
        this._drawShelves(this.ctx, model, this.translator);
        this._drawPackingTable(this.ctx, model, this.translator);
        this._drawPickingMarkers(this.ctx, model, this.translator);

        // draw routes
        for (const [algoName, data] of Object.entries(model.routes)) {
            const color = (algoName === 'christofides') ? 'yellow' : (algoName === 'nearestNeighbor') ? 'red' : (algoName === 'scfsPlus') ? 'cyan' : 'pink';
            this._drawWarehouseRoute(this.ctx, data.route, color, this.translator);
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

        const color = (routeName === 'christofides') ? 'yellow' : (routeName === 'nearestNeighbor') ? 'red' : (routeName === 'scfsPlus') ? 'cyan' : 'pink';

        this._drawWarehouseRoute(ctx, routeData.route, color, modalTranslator);

    }

    _drawShelves(ctx, model, translator) {
        const cellW = translator.horizontalGridSize;
        const cellH = translator.verticalGridSize;
        const shelfPixelWidth = WarehouseModel.SHELF_GRID_WIDTH * cellW;
        const shelfPixelHeight = WarehouseModel.SHELF_GRID_HEIGHT * cellH;
        const padding = Math.max(1, Math.min(cellW, cellH) * 0.08);

        for (let r = 0; r < model.numCrossings; r++) {
            for (let c = 0; c < model.numColumns; c++) {

                let gridX = c * WarehouseModel.SHELF_TOTAL_WIDTH + WarehouseModel.AISLE_GRID_WIDTH;
                let gridY = r * WarehouseModel.SHELF_TOTAL_HEIGHT + WarehouseModel.AISLE_GRID_HEIGHT;

                let pixelX = translator.offsetX + (gridX * cellW);
                let pixelY = translator.offsetY + (gridY * cellH);

                // Shadow
                ctx.fillStyle = "rgba(0, 0, 0, 0.25)";
                ctx.fillRect(pixelX + 2, pixelY + 2, shelfPixelWidth, shelfPixelHeight);

                // Shelf base
                ctx.fillStyle = "#3a3a4a";
                ctx.fillRect(pixelX, pixelY, shelfPixelWidth, shelfPixelHeight);

                // Individual compartments (6 rows × 2 columns)
                for (let row = 0; row < WarehouseModel.SHELF_GRID_HEIGHT; row++) {
                    for (let col = 0; col < WarehouseModel.SHELF_GRID_WIDTH; col++) {
                        const cx = pixelX + col * cellW + padding;
                        const cy = pixelY + row * cellH + padding;
                        const cw = cellW - padding * 2;
                        const ch = cellH - padding * 2;

                        // Gradient per compartment for 3D depth effect
                        const grad = ctx.createLinearGradient(cx, cy, cx, cy + ch);
                        grad.addColorStop(0, "#6b8cae");
                        grad.addColorStop(0.5, "#4a6d8c");
                        grad.addColorStop(1, "#3a5a75");

                        ctx.fillStyle = grad;
                        ctx.fillRect(cx, cy, cw, ch);

                        // Inner highlight (top edge)
                        ctx.fillStyle = "rgba(255, 255, 255, 0.12)";
                        ctx.fillRect(cx, cy, cw, Math.max(1, ch * 0.15));
                    }
                }

                // Center divider between the two shelf columns
                const dividerX = pixelX + cellW - 0.5;
                ctx.strokeStyle = "#2a2a3a";
                ctx.lineWidth = Math.max(1, cellW * 0.06);
                ctx.beginPath();
                ctx.moveTo(dividerX, pixelY);
                ctx.lineTo(dividerX, pixelY + shelfPixelHeight);
                ctx.stroke();

                // Outer border
                ctx.strokeStyle = "#555";
                ctx.lineWidth = 1;
                ctx.strokeRect(pixelX, pixelY, shelfPixelWidth, shelfPixelHeight);
            }
        }
    }

    _drawPackingTable(ctx, model, translator) {
        const rect = translator.getPackingTablePixelRect(model);

        // Shadow
        ctx.fillStyle = "rgba(0, 0, 0, 0.25)";
        ctx.fillRect(rect.x + 2, rect.y + 2, rect.w, rect.h);

        // Table surface with gradient
        const grad = ctx.createLinearGradient(rect.x, rect.y, rect.x, rect.y + rect.h);
        grad.addColorStop(0, "#e8a845");
        grad.addColorStop(1, "#c4872e");
        ctx.fillStyle = grad;
        ctx.fillRect(rect.x, rect.y, rect.w, rect.h);

        // Border
        ctx.strokeStyle = "#8a5e1a";
        ctx.lineWidth = 1.5;
        ctx.strokeRect(rect.x, rect.y, rect.w, rect.h);

        // Label
        let fontSize = Math.max(8, Math.floor(45 / model.numColumns));
        ctx.font = `bold ${fontSize}px Arial`;
        ctx.fillStyle = "#fff";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText("Depot", rect.x + rect.w / 2, rect.y + rect.h / 2);
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
}