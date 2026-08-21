import { addLocationToTable } from "./domUtils.js";

// Wartezeit, bevor die Ladeanzeige erscheint. Kurz genug, dass ein langer
// Lauf sofort Rueckmeldung gibt, lang genug, dass schnelle Laeufe still
// bleiben.
const BUSY_DELAY_MS = 250;

export default class MainView {
    constructor() {
        this.aisleInput = document.getElementById("warehouseAisleCount");
        this.crossingInput = document.getElementById("warehouseCrossingCount");
        this.locationCountInput = document.getElementById("locationCount");
        this.locationGenerationSeed = document.getElementById("locationGenerationSeed");

        this.changeFloorPlanBtn = document.getElementById("changeWarehouseFloorPlan");
        this.generateLocationsBtn = document.getElementById("generateLocationsButton");
        this.triggerRouteBtn = document.getElementById("triggerRouteCalculationButton");

        this.locationTableBody = document.querySelector("#locationTable tbody");
        this.routeInfoContainer = document.getElementById("routeInfo");

        this.errorContainer = document.getElementById("error-container");
        this.busyIndicator = document.getElementById("busy-indicator");
        this.busyMessage = document.getElementById("busyMessage");

        // Tab elements
        this.tabButtons = document.querySelectorAll(".tab-btn");
        this.tabContents = document.querySelectorAll(".tab-content");
        this.canvas = document.getElementById("warehouseCanvas");
        this.benchmarkResultsArea = document.getElementById("benchmarkResultsArea");

        this._initTabs();

        if (!this.locationTableBody || !this.errorContainer || !this.busyIndicator) {
            console.error("MainView failed to find critical DOM elements.");
        }
    }

    /**
     * Initializes tab switching between Single Run and Benchmark modes.
     */
    _initTabs() {
        this.tabButtons.forEach(btn => {
            btn.addEventListener("click", () => {
                const targetTab = btn.dataset.tab;
                this._switchTab(targetTab);
            });
        });
    }

    /**
     * Switches the active tab and toggles the main content area.
     * @param {string} tabName - "singleRun" or "benchmark"
     */
    _switchTab(tabName) {
        // Update tab buttons
        this.tabButtons.forEach(btn => {
            btn.classList.toggle("active", btn.dataset.tab === tabName);
        });

        // Update tab content panels
        this.tabContents.forEach(content => {
            content.classList.toggle("active", content.id === `tab-${tabName}`);
        });

        // Toggle left-side area: canvas for single run, results area for benchmark
        if (tabName === "benchmark") {
            this.canvas.classList.add("hidden");
            this.benchmarkResultsArea.classList.remove("hidden");
        } else {
            this.canvas.classList.remove("hidden");
            this.benchmarkResultsArea.classList.add("hidden");
        }
    }

    /**
     * Returns the currently active tab name.
     * @returns {string} "singleRun" or "benchmark"
     */
    getActiveTab() {
        const activeBtn = document.querySelector(".tab-btn.active");
        return activeBtn ? activeBtn.dataset.tab : "singleRun";
    }

    /**
     * Gets the current floor plan values from the inputs.
     * @returns {{aisles: number, crossings: number}}
     */
    getFloorPlanConfig() {
        return {
            aisles: this.aisleInput.value,
            crossings: this.crossingInput.value
        };
    }

    /**
     * Gets the number of locations to generate.
     * @returns {number}
     */
    getLocationCount() {
        return this.locationCountInput.value;
    }

    /**
     * Gets the seed for the location generation.
     * @returns {number}
     */
    getLocationGenerationSeed() {
        return this.locationGenerationSeed.value;
    }

    /**
     * Clears all data from the view.
     */
    clearData() {
        this.locationTableBody.innerHTML = "";
        this.routeInfoContainer.innerHTML = "";
        this.errorContainer.textContent = "";
    }

    /**
     * Renders a list of locations into the table.
     * @param {Array<Object>} locations - The locations from the model.
     */
    renderLocations(locations) {
        // Clear only what's necessary
        this.locationTableBody.innerHTML = "";

        if (locations.length === 0) {
            this.showError("No locations were generated."); // Use the error system
            return;
        }

        locations.forEach(loc => {
            addLocationToTable(this.locationTableBody, loc);
        });
    }

    /**
     * Displays a non-blocking error message to the user.
     * @param {string} message
     */
    showError(message) {
        this.errorContainer.textContent = message;
    }

    /**
     * Shows the loading indicator and locks the controls that would start a
     * second run. The fixed-parameter solver takes tens of seconds on large
     * layouts, so without this the application looks frozen.
     * @param {string} message
     */
    showBusy(message) {
        this.busyMessage.textContent = message;
        this._setControlsDisabled(true);

        // Only show up after a short delay. Small layouts are done in a few
        // milliseconds, where the indicator would just flash up and vanish.
        clearTimeout(this._busyTimer);
        this._busyTimer = setTimeout(() => {
            this.busyIndicator.classList.remove("hidden");
        }, BUSY_DELAY_MS);
    }

    /**
     * Hides the loading indicator and unlocks the controls.
     */
    hideBusy() {
        clearTimeout(this._busyTimer);
        this.busyIndicator.classList.add("hidden");
        this._setControlsDisabled(false);
    }

    _setControlsDisabled(disabled) {
        this.changeFloorPlanBtn.disabled = disabled;
        this.generateLocationsBtn.disabled = disabled;
        this.triggerRouteBtn.disabled = disabled;
    }

    /**
     * Binds a handler to the 'Change Floor Plan' button.
     * @param {Function} handler
     * Todo understand this pattern better.
     */
    bindChangeFloorPlan(handler) {
        this.changeFloorPlanBtn.addEventListener("click", handler);
    }

    /**
     * Binds a handler to the 'Generate Locations' button.
     * @param {Function} handler
     */
    bindGenerateLocations(handler) {
        this.generateLocationsBtn.addEventListener("click", handler);
    }

    /**
     * Binds a handler to the 'Calculate Route' button.
     * @param {Function} handler
     */
    bindCalculateRoute(handler) {
        this.triggerRouteBtn.addEventListener("click", handler);
    }

    getSelectedAlgorithms() {
        const checkboxes = document.querySelectorAll('input[name="selections"]:checked');
        return Array.from(checkboxes).map(cb => cb.value);
    }
}