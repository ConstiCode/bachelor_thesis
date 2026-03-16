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
        this.mainView.bindChangeFloorPlan(this._handleFloorPlanChange.bind(this));
        this.mainView.bindGenerateLocations(this._handleGenerateLocations.bind(this));
        this.mainView.bindCalculateRoute(this._handleCalculateRoute.bind(this));

        // --- INITIALIZATION ---
        this._handleFloorPlanChange();
    }

     /**
     * Controller handler for changing the floor plan.
     * Updates the model and render's the new floor plan.
     */
    _handleFloorPlanChange() {
        // get data from View
        const config = this.mainView.getFloorPlanConfig();

        if (config.aisles < 1 || config.crossings < 1) {
            this.mainView.showError("Please enter a valid number for aisles and crossings");
            return;
        }

        // update model
        this.model.updateDimensions(config.aisles, config.crossings);

        // rerender the scene
        this.mainView.clearData();
        this.renderer.drawScene(this.model);
    }

     /**
     * Controller handler for generating locations.
     */
    async _handleGenerateLocations() {
        // clear previous errors and data
        this.mainView.clearData();

        // api call for the stock locations
        try {
            const productCount = this.mainView.getLocationCount();
            const locationGenerationSeed = this.mainView.getLocationGenerationSeed();

            if (productCount < 1) {
                this.mainView.showError("Please enter a valid product count.");
                return;
            }

            // call flask service to generate locations
            const locations = await this.api.generateLocations(this.model, productCount, locationGenerationSeed);

            // update model with new locations
            this.model.setStockLocations(locations);

            // render locations in canvas via renderer
            this.mainView.renderLocations(locations);
            this.renderer.drawScene(this.model);

        } catch (error) {
            this.mainView.showError(error.message);
        }
    }

    /**
     * Controller handler for calculating routes.
     */
    async _handleCalculateRoute() {
        this.mainView.clearData();

        try {
            const algorithms = this.mainView.getSelectedAlgorithms();
            if (algorithms.length === 0) {
                this.mainView.showError("Please select at least one algorithm");
                return;
            }
            if (this.model.stockLocations.length === 0) {
                this.mainView.showError("Please generate locations first");
                return;
            }

            // call service
            const response = await this.api.calculateRoutes(this.model, this.model.stockLocations, algorithms);

            this.model.setRoutes(response.routes);

            // render results
            this.renderer.drawScene(this.model);
            if (algorithms.length > 1) {
                this.modalView.show(this.model);
            }

            // show errors for failed algorithms alongside successful results
            if (response.error_message && response.error_message.length > 0) {
                this.mainView.showError(response.error_message.join("\n"));
            }

        } catch (error) {
            this.mainView.showError(error.message);
        }
    }
}