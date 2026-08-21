
import { ROUTE_STYLES } from './WarehouseRenderer.js';

export default class ModalView {
    /**
     * @param {WarehouseRenderer} renderer - An instance of the renderer for drawing.
     */
    constructor(renderer) {
        this.renderer = renderer;

        this.modal = document.getElementById("comparison-modal");
        this.modalContainer = document.getElementById("modal-canvas-container");
        this.closeBtn = this.modal.querySelector(".modal-close");

        if (!this.modal || !this.modalContainer || !this.closeBtn) {
            console.error("ModalView could not find required DOM elements.");
            return;
        }

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
        this.modalContainer.innerHTML = "";

        const canvasesToRender = [];

        // build the dom structure first
        Object.entries(model.routes).forEach(([algoName, algoData]) => {
            if (!algoData) return;

            const wrapper = document.createElement("div");
            wrapper.classList.add("modal-canvas-wrapper");

            // add title, using the same readable label as the canvas legend
            const title = document.createElement("h3");
            title.textContent = ROUTE_STYLES[algoName] ? ROUTE_STYLES[algoName].label : algoName;
            wrapper.appendChild(title);

            // add canvas
            const cloneCanvas = document.createElement("canvas");
            cloneCanvas.style.width = "100%";
            cloneCanvas.style.height = "300px";
            wrapper.appendChild(cloneCanvas);

            // add route info
            const info = document.createElement("div");
            info.classList.add("modal-route-info");

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

        // show the modal
        this.modal.classList.add("show");

        // draw the canvases
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