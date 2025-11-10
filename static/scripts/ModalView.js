// NEW FILE: ModalView.js
import WarehouseRenderer from './WarehouseRenderer.js';

export default class ModalView {
    /**
     * @param {WarehouseRenderer} renderer - An instance of the renderer for drawing.
     */
    constructor(renderer) {
        this.renderer = renderer;

        // The View class queries and holds its own DOM elements
        this.modal = document.getElementById("comparison-modal");
        this.modalContainer = document.getElementById("modal-canvas-container");
        this.closeBtn = this.modal.querySelector(".modal-close");

        if (!this.modal || !this.modalContainer || !this.closeBtn) {
            console.error("ModalView could not find required DOM elements.");
            return;
        }

        // The View binds its own internal event listeners
        this._bindEventListeners();
    }

    _bindEventListeners() {
        this.closeBtn.addEventListener("click", () => this.hide());
    }

    /**
     * Hides the modal.
     */
    hide() {
        this.modal.classList.remove("show");
    }

    /**
     * Shows and populates the comparison modal with route data from the model.
     * @param {WarehouseModel} model - The application's main data model.
     */
    show(model) {
        // 1. Clear previous content
        this.modalContainer.innerHTML = "";

        // 2. Create a list to hold the canvases and their data
        const canvasesToRender = [];

        // --- LOOP 1: BUILD THE DOM ---
        // This is the *exact* same logic as before, but it now
        // lives in the correct class.
        Object.entries(model.routes).forEach(([algoName, algoData]) => {
            if (!algoData) return;

            const wrapper = document.createElement("div");
            wrapper.classList.add("modal-canvas-wrapper");

            // Add the title
            const title = document.createElement("h3");
            title.textContent = algoName;
            wrapper.appendChild(title);

            // Add the canvas
            const cloneCanvas = document.createElement("canvas");
            cloneCanvas.style.width = "100%";
            cloneCanvas.style.height = "300px";
            wrapper.appendChild(cloneCanvas);

            // Add route info
            const info = document.createElement("div");
            info.classList.add("modal-route-info");

            const length = algoData.length ? algoData.length.toFixed(2) : 'N/A';
            const computationTime = algoData.computation_time ? algoData.computation_time.toFixed(2) : 'N/A';

            info.textContent = `Route Length: ${length} | Computation Time: ${computationTime}`;
            wrapper.appendChild(info);

            this.modalContainer.appendChild(wrapper);

            // Store the work to be done in the next loop
            canvasesToRender.push({
                canvas: cloneCanvas,
                algoName: algoName,
                data: algoData
            });
        });

        // 3. Show the modal (and its new DOM structure)
        this.modal.classList.add("show");

        // --- LOOP 2: DRAW ON THE CANVASES ---
        // This two-loop structure is preserved as you requested
        // to ensure the canvases are in the DOM and visible
        // before the renderer attempts to draw on them.
        canvasesToRender.forEach(item => {
            this.renderer.renderToCanvas(
                item.canvas,
                model,
                1.0, // scale
                model.stockLocations, // Pass the locations
                item.algoName,
                item.data
            );
        });
    }
}