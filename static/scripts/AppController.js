import WarehouseModel from './WarehouseModel.js';
import WarehouseRenderer from './WarehouseRenderer.js';
import ApiService from './ApiService.js';
import ModalView from "./ModalView.js";
import MainView from "./MainView.js";

export default class AppController {
    constructor() {
        // --- STATE & SERVICES ---
        this.renderer = new WarehouseRenderer("warehouseCanvas");
        this.api = new ApiService();

        // --- VIEWS ---
        this.mainView = new MainView();
        this.modalView = new ModalView(this.renderer)
        const initialConfig = this.mainView.getFloorPlanConfig();
        this.model = new WarehouseModel(initialConfig.aisles, initialConfig.crossings);

        // --- BINDING ---
        // We tell the VIEW what to do when *it* is clicked.
        // We pass it the HANDLER.
        // Note the .bind(this) to maintain the correct "this" context.
        this.mainView.bindChangeFloorPlan(this._handleFloorPlanChange.bind(this));
        this.mainView.bindGenerateLocations(this._handleGenerateLocations.bind(this));
        this.mainView.bindCalculateRoute(this._handleCalculateRoute.bind(this));

        // --- INITIALIZATION ---
        this._handleFloorPlanChange();

    }

     /**
     * Controller handler for changing the floor plan.
     * Orchestrates model updates and view renders.
     */
    _handleFloorPlanChange() {
        // 1. Get data FROM the view
        const config = this.mainView.getFloorPlanConfig();

        // 2. Validate (Controller's job)
        if (config.aisles < 1 || config.crossings < 1) {
            this.mainView.showError("Please enter a valid number for aisles and crossings");
            return;
        }

        // 3. Update Model (Controller's job)
        this.model.updateDimensions(config.aisles, config.crossings);

        // 4. Delegate to Views (Controller's job)
        this.mainView.clearData();
        this.renderer.drawScene(this.model);
    }

     /**
     * Controller handler for generating locations.
     */
    async _handleGenerateLocations() {
        // 1. Clear previous errors/data
        this.mainView.clearData();

        // --- 2. THE A-GRADE "try...catch" BLOCK ---
        try {
            // 3. Get data from View & Validate
            const productCount = this.mainView.getLocationCount();
            if (productCount < 1) {
                this.mainView.showError("Please enter a valid product count.");
                return;
            }

            // 4. Call Service (the "happy path")
            const locations = await this.api.generateLocations(this.model, productCount);

            // 5. Update Model
            this.model.setStockLocations(locations);

            // 6. Delegate to Views
            this.mainView.renderLocations(locations); // Give the view DATA, not instructions
            this.renderer.drawScene(this.model);

        } catch (error) {
            // --- 6. THE "failure path" ---
            // If the api.generateLocations() throws an error, we catch it.
            // We then DELEGATE the error display to the view.
            this.mainView.showError(error.message);
        }
    }

    /**
     * Controller handler for calculating routes.
     */
    async _handleCalculateRoute() {
        this.mainView.clearData(); // Clear errors

        try {
            // 1. Validate (Controller's job)
            const algorithms = this.mainView.getSelectedAlgorithms();
            if (algorithms.length === 0) {
                this.mainView.showError("Please select at least one algorithm");
                return;
            }
            if (this.model.stockLocations.length === 0) {
                this.mainView.showError("Please generate locations first");
                return;
            }

            // 2. Call Service
            const routeData = await this.api.calculateRoutes(this.model, this.model.stockLocations, algorithms);

            // 3. Update Model
            this.model.setRoutes(routeData);

            // 4. Delegate to Views
            this.renderer.drawScene(this.model);
            if (algorithms.length > 1) {
                this.modalView.show(this.model);
            }

        } catch (error) {
            // 5. Catch and Delegate Error
            this.mainView.showError(error.message);
        }
    }
}