import WarehouseModel from './WarehouseModel.js';
import CoordinateTranslator from './CoordinateTranslator.js';

/**
 * Darstellung der Routen, gemeinsame Quelle fuer die Hauptansicht und das
 * Vergleichsfenster, damit beide nicht auseinanderlaufen koennen.
 *
 * Die Reihenfolge der Eintraege ist die Zeichenreihenfolge: breite Linien
 * zuerst, schmale darueber. Deckungsgleiche Routen bleiben so alle sichtbar.
 * Das ist hier der Normalfall und nicht die Ausnahme, weil die Verfahren auf
 * kleinen Instanzen oft dieselbe Tour finden.
 *
 * Rot fehlt bewusst: die Auftragspositionen sind rot, eine rote Route waere
 * von ihnen nicht zu unterscheiden.
 */
export const ROUTE_STYLES = {
    fixedParameter:  {label: "Fixed Parameter",  color: "#bf5af2", width: 6, dash: []},
    christofides:    {label: "Christofides",     color: "#ffd60a", width: 4, dash: [10, 6]},
    nearestNeighbor: {label: "Nearest Neighbor", color: "#32d74b", width: 2, dash: [3, 4]},
    scfsPlus:        {label: "SCFS+",            color: "#64d2ff", width: 2, dash: [1, 5]},
};

const FALLBACK_ROUTE_STYLE = {label: "Route", color: "#f5f5f7", width: 3, dash: []};

function routeStyle(algorithmName) {
    return ROUTE_STYLES[algorithmName] || FALLBACK_ROUTE_STYLE;
}

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

        // Draw the routes in the fixed order of ROUTE_STYLES, not in the order
        // the backend happened to return them. Otherwise the last one drawn
        // hides the others wherever they run along the same aisles.
        const drawn = Object.keys(ROUTE_STYLES).filter(name => model.routes[name]);
        for (const algoName of drawn) {
            this._drawWarehouseRoute(this.ctx, model.routes[algoName].route,
                routeStyle(algoName), this.translator);
        }

        // Anything the styles do not know about, drawn with the fallback.
        const unknown = Object.keys(model.routes).filter(name => !ROUTE_STYLES[name]);
        for (const algoName of unknown) {
            this._drawWarehouseRoute(this.ctx, model.routes[algoName].route,
                routeStyle(algoName), this.translator);
        }

        this._drawLegend(this.ctx, [...drawn, ...unknown], width);
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

        this._drawWarehouseRoute(ctx, routeData.route, routeStyle(routeName), modalTranslator);

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
                // Gezeichnet wird von oben nach unten, das Gitter zaehlt aber
                // vom Depot weg nach oben. Ankerzeile ist deshalb die oberste
                // Regalzeile dieses Blocks, nicht die unterste.
                let gridYTop = r * WarehouseModel.SHELF_TOTAL_HEIGHT
                    + WarehouseModel.AISLE_GRID_HEIGHT
                    + (WarehouseModel.SHELF_GRID_HEIGHT - 1);

                let pixelX = translator.offsetX + (gridX * cellW);
                let pixelY = translator.gridYToPixel(gridYTop);

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

    _drawWarehouseRoute(ctx, route, style, translator) {
        if (!route || route.length === 0) return;

        ctx.beginPath();
        const start = translator.gridToPixel({x: route[0][0], y: route[0][1]});
        ctx.moveTo(start.x, start.y);

        for (const point of route) {
            const pos = translator.gridToPixel({x: point[0], y: point[1]});
            ctx.lineTo(pos.x, pos.y);
        }
        ctx.strokeStyle = style.color;
        ctx.lineWidth = style.width;
        ctx.setLineDash(style.dash);
        ctx.stroke();
        // Reset, otherwise the pattern leaks into everything drawn afterwards.
        ctx.setLineDash([]);
    }

    /**
     * Draws a legend for the routes currently on the canvas. Without it the
     * colours mean nothing once the comparison window is closed.
     */
    _drawLegend(ctx, algorithmNames, canvasWidth) {
        if (algorithmNames.length === 0) return;

        const lineHeight = 20;
        const swatchWidth = 24;
        const gap = 8;
        const padding = 10;

        // Set every text property explicitly. The depot label runs before this
        // and leaves textAlign at "center", which would shift the labels.
        ctx.font = "12px sans-serif";
        ctx.textAlign = "left";
        ctx.textBaseline = "middle";

        const entries = algorithmNames.map(routeStyle);
        const textWidth = Math.max(...entries.map(e => ctx.measureText(e.label).width));
        const boxWidth = padding * 2 + swatchWidth + gap + textWidth;
        const boxHeight = padding * 2 + entries.length * lineHeight;
        // Keep the box inside the canvas even when it is narrow.
        const boxX = Math.max(12, canvasWidth - boxWidth - 12);
        const boxY = 12;

        ctx.fillStyle = "rgba(44, 44, 46, 0.9)";
        ctx.strokeStyle = "#3a3a3c";
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.rect(boxX, boxY, boxWidth, boxHeight);
        ctx.fill();
        ctx.stroke();

        entries.forEach((entry, index) => {
            const centerY = boxY + padding + index * lineHeight + lineHeight / 2;

            ctx.beginPath();
            ctx.strokeStyle = entry.color;
            // Cap the width so a 6 px route still fits the swatch row.
            ctx.lineWidth = Math.min(entry.width, 4);
            ctx.setLineDash(entry.dash);
            ctx.moveTo(boxX + padding, centerY);
            ctx.lineTo(boxX + padding + swatchWidth, centerY);
            ctx.stroke();
            ctx.setLineDash([]);

            ctx.fillStyle = "#f5f5f7";
            ctx.fillText(entry.label, boxX + padding + swatchWidth + gap, centerY);
        });
    }
}