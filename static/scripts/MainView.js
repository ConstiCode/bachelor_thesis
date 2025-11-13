/**
 * Todo import it rather than leaving it here.
 * This helper function is from domUtils.js.
 * We move it here, or import it, because it is PURELY
 * a view-related function.
 */
function addLocationToTable(tbody, loc) {
    const row = document.createElement('tr');
    row.innerHTML = `
        <td>${loc.id}</td>
        <td>${loc.x}</td>
        <td>${loc.y}</td>
    `;
    tbody.appendChild(row);
}

export default class MainView {
    constructor() {
        this.aisleInput = document.getElementById("warehouseAisleCount");
        this.crossingInput = document.getElementById("warehouseCrossingCount");
        this.locationCountInput = document.getElementById("locationCount");

        this.changeFloorPlanBtn = document.getElementById("changeWarehouseFloorPlan");
        this.generateLocationsBtn = document.getElementById("generateLocationsButton");
        this.triggerRouteBtn = document.getElementById("triggerRouteCalculationButton");

        this.locationTableBody = document.querySelector("#locationTable tbody");
        this.routeInfoContainer = document.getElementById("routeInfo");


        this.errorContainer = document.getElementById("error-container");

        if (!this.locationTableBody || !this.errorContainer) {
            console.error("MainView failed to find critical DOM elements.");
        }
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