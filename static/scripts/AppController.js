import WarehouseModel from './WarehouseModel.js';
import WarehouseRenderer from './WarehouseRenderer.js';
import ApiService from './ApiService.js';
import {addLocationToTable, updateRouteInfoTable} from './domUtils.js';
//import ModalView from "./ModalView";

export default class AppController {
    constructor() {
        this.model = new WarehouseModel(2, 2); // Default values
        this.renderer = new WarehouseRenderer("warehouseCanvas");
        this.api = new ApiService();

        // this.modalView = new ModalView(this.renderer)

        this.aisleInput = document.getElementById("warehouseAisleCount");
        this.crossingInput = document.getElementById("warehouseCrossingCount");
        this.locationCountInput = document.getElementById("locationCount");

        this.changeFloorPlanBtn = document.getElementById("changeWarehouseFloorPlan");
        this.generateLocationsBtn = document.getElementById("generateLocationsButton");
        this.triggerRouteBtn = document.getElementById("triggerRouteCalculationButton");

        this.locationTableBody = document.querySelector("#locationTable tbody");
        this.routeInfoContainer = document.getElementById("routeInfo");

        this.modal = document.getElementById("comparison-modal");
        this.modalContainer = document.getElementById("modal-canvas-container");
        document.querySelector(".modal-close").addEventListener("click", () => this.modal.classList.remove("show"));

        this._bindEventListeners();

        this._handleFloorPlanChange();
    }

    _bindEventListeners() {
        this.changeFloorPlanBtn.addEventListener("click", () => this._handleFloorPlanChange());
        this.generateLocationsBtn.addEventListener("click", () => this._handleGenerateLocations());
        this.triggerRouteBtn.addEventListener("click", () => this._handleCalculateRoute());
    }

    _handleFloorPlanChange() {
        const aisles = this.aisleInput.value;
        const crossings = this.crossingInput.value;

        if (aisles < 1 || crossings < 1) {
            alert("Please enter a valid number for aisles and crossings");
            return;
        }

        this.model.updateDimensions(aisles, crossings);

        this.locationTableBody.innerHTML = "";
        this.routeInfoContainer.innerHTML = "";

        this.renderer.drawScene(this.model);
    }

    async _handleGenerateLocations() {
        const productCount = this.locationCountInput.value;
        if (productCount < 1) {
            alert("Please enter a valid product count.");
            return;
        }

        const locations = await this.api.generateLocations(this.model, productCount);
        if (locations.length === 0) {
            alert("No data available.");
            return;
        }

        this.model.setStockLocations(locations);

        this.locationTableBody.innerHTML = "";
        locations.forEach(loc => {
            addLocationToTable(this.locationTableBody, loc);
        });

        this.renderer.drawScene(this.model);
    }

    async _handleCalculateRoute() {
        const algorithms = this._checkSelectedAlgorithms();
        if (algorithms.length === 0) {
            alert("Please select at least one algorithm");
            return;
        }

        if (this.model.stockLocations.length === 0) {
            alert("Please generate locations first");
            return;
        }

        const routeData = await this.api.calculateRoutes(this.model, this.model.stockLocations, algorithms);

        this.model.setRoutes(routeData);

        this.renderer.drawScene(this.model);

        if (algorithms.length > 1) {
            this._showComparisonModal();
        }
    }

    _checkSelectedAlgorithms() {
        const checkboxes = document.querySelectorAll('input[name="selections"]:checked');
        return Array.from(checkboxes).map(cb => cb.value);
    }

    _showComparisonModal() {
        this.modalContainer.innerHTML = "";

        // 1. Create a list to hold the canvases and their data
        const canvasesToRender = [];

        // --- LOOP 1: BUILD THE DOM ---
        Object.entries(this.model.routes).forEach(([algoName, algoData]) => {
            if (!algoData) return;

            const wrapper = document.createElement("div");
            wrapper.classList.add("modal-canvas-wrapper");

            // Add the title (e.g., "christofides")
            const title = document.createElement("h3");
            title.textContent = algoName;
            wrapper.appendChild(title);

            // Add the canvas
            const cloneCanvas = document.createElement("canvas");
            cloneCanvas.style.width = "100%";
            cloneCanvas.style.height = "300px";
            wrapper.appendChild(cloneCanvas);

            const info = document.createElement("div");
            info.classList.add("modal-route-info"); // Add a class for styling

            const length = algoData.length ? algoData.length.toFixed(2) : 'N/A';
            const computationTime = algoData.computation_time ? algoData.computation_time.toFixed(2) : 'N/A';

            info.textContent = `Route Length: ${length} | Computation Time: ${computationTime}`;
            wrapper.appendChild(info);

            this.modalContainer.appendChild(wrapper);

            canvasesToRender.push({
                canvas: cloneCanvas,
                algoName: algoName,
                data: algoData
            });
        });

        // 2. Show the modal
        this.modal.classList.add("show");

        // --- LOOP 2: DRAW ON THE CANVASES ---
        canvasesToRender.forEach(item => {
            this.renderer.renderToCanvas(
                item.canvas,
                this.model,
                1.0, // scale
                this.model.stockLocations,
                item.algoName,
                item.data
            );
        });
    }
}