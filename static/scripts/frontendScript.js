class WarehouseFloorPlan {
    constructor(canvasId, debug = false) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext("2d");
        this.dpr = window.devicePixelRatio || 1;
        this.setupCanvas();
        if (debug) {
            this.debug = true;
        }
    }

    setupCanvas() {
        let rect = this.canvas.getBoundingClientRect();
        this.canvas.width = rect.width * this.dpr;
        this.canvas.height = rect.height * this.dpr;
        this.ctx.scale(this.dpr, this.dpr);
    }

    renderBaseFloorToCanvas(targetCanvas, scale = 1) {
        const ctx = targetCanvas.getContext("2d");

        // set sizes
        targetCanvas.width = this.canvas.width;
        targetCanvas.height = this.canvas.height;

        ctx.scale(this.dpr, this.dpr);

        // run the same drawing code as the fresh warehouse
        ctx.fillStyle = "#1e1e1e";
        ctx.fillRect(0, 0, targetCanvas.width, targetCanvas.height);

        // temporarily replace ctx
        const originalCtx = this.ctx;
        this.ctx = ctx;

        // redraw shelves and packing table
        // 2. 'scale' HIER AN DIE NÄCHSTE FUNKTION WEITERGEBEN
        this.drawStorageShelfFloorPlan(this.numColumns, this.numCrossings, scale);

        this.ctx = originalCtx;
    }


    clearCanvas() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.ctx.fillStyle = "#1e1e1e";
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

        if (this.debug) {
            this.drawDebuggingGrid();
        }
    }

    drawPackingTable() {
        // calculate the position of the packing table relative to the number of and crossings (Y)
        let offset = (this.numCrossings * 7 * this.verticalGridSize) / 2;
        let startPositionY = (this.canvas.height / 2) + offset;
        let positionY = ((this.canvas.height / 2) + offset) + 8 * this.verticalGridSize; // this.numCrossings * (this.verticalGridSize * 7);

        let positionX = (((this.canvas.width / 2) - 2 * this.horizontalGridSize));
        this.ctx.rect(positionX, positionY, this.horizontalGridSize * 3, this.horizontalGridSize); // x, y, width, height
        this.ctx.fillStyle = "lightblue";
        this.ctx.fill(); // Draw the outline

        this.positionPackingTable = {x: positionX, y: positionY}; // Todo check if this is correct and adjust for center


        // Set text styles
        let fontSize = Math.floor(45 / this.numColumns);
        this.ctx.font = `${fontSize}px Arial`;
        this.ctx.fillStyle = "black";
        this.ctx.textAlign = "center";
        this.ctx.textBaseline = "middle";

        // Calculate text position (center of the rectangle)
        let textX = positionX + (this.horizontalGridSize * 3) / 2;
        let textY = positionY + this.verticalGridSize / 2;

        this.ctx.fillText("Packing Table", textX, textY);
    }

    drawStorageShelf(positionX, positionY) {
        this.ctx.beginPath();
        this.ctx.rect(positionX, positionY, 2 * this.horizontalGridSize, this.shelfHeight * this.verticalGridSize); // x, y, width, height
        this.ctx.fillStyle = "lightblue";
        this.ctx.fill();
    }

    drawStorageShelfRow() {
        let offset = (this.numColumns * 3 * this.horizontalGridSize) / 2;
        let startPosition = (this.canvas.width / 2) - offset;

        this.normalizedCoordinate.x = startPosition;

        for (let i = 0; i < this.numColumns; i++) {
            this.drawStorageShelf(startPosition, this.startPositionY, this.horizontalGridSize);
            startPosition = startPosition + 3 * this.horizontalGridSize;
        }
    }

    drawPickingMarkers(positions) {
        // draws a small red dots for a given array of stock locations
        for (let i = 0; i < positions.length; i++) {
            let offsetX = this.normalizedCoordinate.x;
            let offsetY = this.normalizedCoordinate.y;
            let x = ((positions[i].x - 1) * this.horizontalGridSize + 0.5 * this.horizontalGridSize) + offsetX;
            let y = ((positions[i].y - 1) * this.verticalGridSize + 0.5 * this.verticalGridSize) + offsetY;

            this.ctx.beginPath();
            this.ctx.arc(x, y, Math.max(this.horizontalGridSize, this.verticalGridSize) / 12, 0, 2 * Math.PI);
            this.ctx.stroke();
            this.ctx.fillStyle = "red";
            this.ctx.fill();
        }
    }

    drawRouteSegments(segments, color) {
        this.ctx.strokeStyle = color; // Use the provided color
        this.ctx.lineWidth = 3;       // Set the line width

        let offsetX = this.normalizedCoordinate.x + 0.5 * this.horizontalGridSize;
        let offsetY = this.normalizedCoordinate.y + 0.5 * this.verticalGridSize;

        // Check if the list is valid (must have an even number of points)
        if (segments.length % 2 !== 0) {
            console.error("drawRouteSegments: The segment list is invalid (odd number of points).");
            return;
        }

        // Iterate by 2, picking a start and end point for each segment
        for (let i = 0; i < segments.length; i += 2) {
            const start = segments[i];   // e.g., [0, 0]
            const end = segments[i + 1]; // e.g., [0, 1]

            // Check if start or end points are valid
            if (!Array.isArray(start) || start.length < 2 || !Array.isArray(end) || end.length < 2) {
                console.error("Invalid segment data at index:", i);
                continue; // Skip this invalid segment
            }

            let startX = (start[0] - 1) * this.horizontalGridSize + offsetX;
            let startY = (start[1] - 1) * this.verticalGridSize + offsetY;
            let endX = (end[0] - 1) * this.horizontalGridSize + offsetX;
            let endY = (end[1] - 1) * this.verticalGridSize + offsetY;

            this.ctx.beginPath();              // Start a new path for EACH segment
            this.ctx.moveTo(startX, startY);   // Move to the start point
            this.ctx.lineTo(endX, endY);       // Draw to the end point
            this.ctx.stroke();                 // Apply stroke for this segment
        }
    }

    drawWarehouseRoute(route, color) {
        // draw the route that is given in tuples from the backend
        //      - valid aisles are multiples of xStart + or -4 as one shelf is 2 grids wide
        //      - valid columns are multiples of xStart + 0,5 offset and + or minus 6

        this.ctx.beginPath();
        for (let i = 0; i < route.length; i++) {
            let offsetX = this.normalizedCoordinate.x + 0.5 * this.horizontalGridSize;
            let offsetY = this.normalizedCoordinate.y + 0.5 * this.verticalGridSize;
            this.ctx.lineTo((route[i][0] - 1) * this.horizontalGridSize + offsetX, (route[i][1] - 1) * this.verticalGridSize + offsetY);
            this.ctx.strokeStyle = "red";
        }
        this.ctx.strokeStyle = color; // Set the line color to red
        this.ctx.lineWidth = 3;
        this.ctx.stroke();
    }

    drawStorageShelfFloorPlan(numColumns, numCrossings, scale = 1) {
        this.clearCanvas();
        this.numColumns = numColumns;
        this.numCrossings = numCrossings;

        let marginVertical = 20;
        let marginHorizontal = 20;

        this.shelfHeight = 6;

        // the grid sizes are dynamically calculated based on the number of aisles and the screen height
        this.verticalGridSize = this.canvas.height / ((numCrossings * 7) + marginVertical);
        this.horizontalGridSize = this.canvas.width / (numColumns * 4 + marginHorizontal);

        this.verticalGridSize *= scale;
        this.horizontalGridSize *= scale;

        let offset = (numCrossings * 7 * this.verticalGridSize) / 2;
        this.startPositionY = (this.canvas.height / 2) + offset;

        // normalizedCoordinate is a field used to calculate the position of the storage shelf's in the backend
        this.normalizedCoordinate = {
            x: null,
            y: this.startPositionY - ((this.numCrossings - 1) * 7 * this.verticalGridSize)
        };

        for (let i = 0; i < numCrossings; i++) {
            this.drawStorageShelfRow();
            this.startPositionY -= this.verticalGridSize * 7;
        }

        // draw the packing table that is the start and end point of the route
        this.drawPackingTable();
    }

    drawDebuggingGrid() {
        this.ctx.beginPath();
        this.ctx.strokeStyle = "black";
        this.ctx.lineWidth = 1;

        // draw horizontal lines
        for (let i = 0; i < this.canvas.height; i += this.verticalGridSize) {
            this.ctx.moveTo(0, i);
            this.ctx.lineTo(this.canvas.width, i);
        }

        // draw vertical lines
        for (let i = 0; i < this.canvas.width; i += this.horizontalGridSize) {
            this.ctx.moveTo(i, 0);
            this.ctx.lineTo(i, this.canvas.height);
        }

        this.ctx.stroke();
    }

    drawWarehouseMst(mst) {
        this.ctx.strokeStyle = "green   "; // Set the line color to red
        this.ctx.lineWidth = 3;       // Set the line width

        let offsetX = this.normalizedCoordinate.x + 0.5 * this.horizontalGridSize;
        let offsetY = this.normalizedCoordinate.y + 0.5 * this.verticalGridSize;

        for (let i = 0; i < mst.length; i++) {
            const [start, end] = mst[i];

            let startX = (start[0] - 1) * this.horizontalGridSize + offsetX;
            let startY = (start[1] - 1) * this.verticalGridSize + offsetY;
            let endX = (end[0] - 1) * this.horizontalGridSize + offsetX;
            let endY = (end[1] - 1) * this.verticalGridSize + offsetY;

            this.ctx.beginPath();              // Start a new path for each segment
            this.ctx.moveTo(startX, startY);   // Move to the start point
            this.ctx.lineTo(endX, endY);       // Draw to the end point
            this.ctx.stroke();                 // Apply stroke
        }
    }

}


const wareHouseFloorPlan = new WarehouseFloorPlan("warehouseCanvas", true);
const changeWarehouseFloorPlanButton = document.getElementById("changeWarehouseFloorPlan");
const generateLocationTestSetButton = document.getElementById("generateLocationsButton");
const triggerRouteCalculationButton = document.getElementById("triggerRouteCalculationButton");

// draw an initial warehouse floor plan
wareHouseFloorPlan.drawStorageShelfFloorPlan(5, 3);

changeWarehouseFloorPlanButton.addEventListener("click", function () {
    let aisles = document.getElementById("warehouseAisleCount").value;
    let crossings = document.getElementById("warehouseCrossingCount").value;
    localStorage.setItem("wareHouseFloorPlan", JSON.stringify({
        aisles: aisles,
        crossings: crossings
    }));

    if (aisles < 1 || crossings < 1) {
        alert("Please enter a valid number for aisles and crossings");
        return;
    }
    wareHouseFloorPlan.drawStorageShelfFloorPlan(aisles, crossings);
});


generateLocationTestSetButton.addEventListener("click", function () {
    let productCount = document.getElementById("locationCount").value;

    fetch('/generate-test-locations', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({warehouse_floor_plan: wareHouseFloorPlan, product_count: productCount})
    })
        .then(response => response.json())
        .then(data => {
            if (data.length === 0) {
                alert("No data available.");  // Notify user here
            }
            // store the locations in local storage for later route calculation
            localStorage.setItem("stockLocations", JSON.stringify(data));

            // reset the canvas and draw the warehouse floor plan
            wareHouseFloorPlan.clearCanvas();
            wareHouseFloorPlan.drawStorageShelfFloorPlan(wareHouseFloorPlan.numColumns, wareHouseFloorPlan.numCrossings);

            // draw the locations on the canvas
            wareHouseFloorPlan.drawPickingMarkers(data);

            // clear the table before displaying new locations
            let tableBody = document.querySelector("#locationTable tbody")
            tableBody.innerHTML = "";

            // display the locations in a table
            data.forEach(location => {
                let row = document.createElement("tr");
                row.innerHTML = `
                <td>${location.location_number}</td>
                <td>${location.x}</td>
                <td>${location.y}</td>
            `;
                tableBody.appendChild(row);
            });
        })
        .catch(error => console.error('Error:', error));
});

function updateRouteInformation(
    data,
    metersPerTile = 1,
    walkingSpeedKmh = 5,
    pickerCostPerHour = 15
) {
    // walkingSpeedKmh to meters per minute
    const walkingSpeedMPerMin = (walkingSpeedKmh * 1000) / 60;

    // Collect rows for each algorithm
    const rows = [];

    if (data.christofides !== undefined) {
        const distanceMeters = data.christofides * metersPerTile;
        const timeMinutes = distanceMeters / walkingSpeedMPerMin;
        const cost = ((timeMinutes / 60) * pickerCostPerHour).toFixed(2);

        rows.push({
            name: "Christofides",
            tiles: data.christofides,
            minutes: timeMinutes.toFixed(1),
            cost: cost,
            computation: data.christofidesComputationTime?.toFixed(2) + " ms"
        });
    }

    if (data.nearestNeighbor !== undefined) {
        const distanceMeters = data.nearestNeighbor * metersPerTile;
        const timeMinutes = distanceMeters / walkingSpeedMPerMin;
        const cost = ((timeMinutes / 60) * pickerCostPerHour).toFixed(2);

        rows.push({
            name: "Nearest Neighbor",
            tiles: data.nearestNeighbor,
            minutes: timeMinutes.toFixed(1),
            cost: cost,
            computation: data.nearestNeighborComputationTime?.toFixed(2) + " ms"
        });
    }

    if (data.fixedParameter !== undefined) {
        const distanceMeters = data.fixedParameter * metersPerTile;
        const timeMinutes = distanceMeters / walkingSpeedMPerMin;
        const cost = ((timeMinutes / 60) * pickerCostPerHour).toFixed(2);

        rows.push({
            name: "Fixed Parameter",
            tiles: data.fixedParameter,
            minutes: timeMinutes.toFixed(1),
            cost: cost,
            computation: data.fixedParameterComputationTime?.toFixed(2) + " ms"
        });
    }

    // Build HTML table
    let tableHtml = `
        <table style="border-collapse: collapse; width: 100%; max-width: 600px;">
            <thead>
                <tr style="background-color: #f0f0f0;">
                    <th style="border: 1px solid #ccc; padding: 6px;">Algorithm</th>
                    <th style="border: 1px solid #ccc; padding: 6px;">Length (tiles)</th>
                    <th style="border: 1px solid #ccc; padding: 6px;">Walking Time (min)</th>
                    <th style="border: 1px solid #ccc; padding: 6px;">Cost ($)</th>
                    <th style="border: 1px solid #ccc; padding: 6px;">Computation Time</th>
                </tr>
            </thead>
            <tbody>
    `;

    rows.forEach(r => {
        tableHtml += `
            <tr>
                <td style="border: 1px solid #ccc; padding: 6px;">${r.name}</td>
                <td style="border: 1px solid #ccc; padding: 6px; text-align: right;">${r.tiles}</td>
                <td style="border: 1px solid #ccc; padding: 6px; text-align: right;">${r.minutes}</td>
                <td style="border: 1px solid #ccc; padding: 6px; text-align: right;">$${r.cost}</td>
                <td style="border: 1px solid #ccc; padding: 6px; text-align: right;">${r.computation}</td>
            </tr>
        `;
    });

    tableHtml += `
            </tbody>
        </table>
    `;

    document.getElementById("routeInfo").innerHTML = tableHtml;
}


function checkSelected() {
    const checkboxes = document.querySelectorAll('input[name="selections"]:checked');
    let algorithms = Array.from(checkboxes).map(cb => cb.value);
    if (algorithms.length === 0) {
        alert("Please select at least one algorithm");
    }
    return algorithms;
}

triggerRouteCalculationButton.addEventListener("click", function () {
    let stockLocations = JSON.parse(localStorage.getItem("stockLocations"));
    if (!stockLocations) {
        alert("Please generate locations first");
        return;
    }

    if (stockLocations.length === 1 && checkSelected().includes("christofides")) {
        alert("Christofides algorithm requires at least 2 locations");
        return;
    }

    let algorithms = checkSelected();

    fetch('/calculate-route', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            warehouse_floor_plan: wareHouseFloorPlan,
            packing_table: {
                x: wareHouseFloorPlan.positionPackingTable.x,
                y: wareHouseFloorPlan.positionPackingTable.y
            },
            locations: stockLocations,
            refactor_testing: true,
            algorithms: algorithms
        })
    })
        .then(response => response.json())
        .then(data => {
            // draw the route on the canvas
            console.log(wareHouseFloorPlan.positionPackingTable);
            let overallRouteInfo = {}
            if (data.christofides && data.christofides.length > 0) {
                wareHouseFloorPlan.drawWarehouseRoute(data.christofides.route, "yellow");
                overallRouteInfo.christofides = data.christofides.length;
                overallRouteInfo.christofidesComputationTime = data.christofides.computation_time;
            }
            if (data.nearestNeighbor && data.nearestNeighbor.length > 0) {
                wareHouseFloorPlan.drawWarehouseRoute(data.nearestNeighbor.route, "red");
                overallRouteInfo.nearestNeighbor = data.nearestNeighbor.length;
                overallRouteInfo.nearestNeighborComputationTime = data.nearestNeighbor.computation_time;
            }
            if (data.fixedParameter) { //  && data.fixedParameter.length > 0) todo maybe add this back?
                wareHouseFloorPlan.drawRouteSegments(data.fixedParameter.route, "pink");
                overallRouteInfo.fixedParameter = data.fixedParameter.length;
                overallRouteInfo.fixedParameterComputationTime = data.fixedParameter.computation_time;
            }
            if (algorithms.length > 1) {
                const modal = document.getElementById("comparison-modal");
                const modalContainer = document.getElementById("modal-canvas-container");
                modalContainer.innerHTML = "";
                modal.classList.add("show");

                const algoMap = {
                    christofides: data.christofides,
                    nearestNeighbor: data.nearestNeighbor,
                    fixedParameter: data.fixedParameter
                };

                algorithms.forEach(algo => {
                    const algoData = algoMap[algo];
                    if (!algoData) return;

                    const wrapper = document.createElement("div");
                    wrapper.classList.add("modal-canvas-wrapper");

                    const title = document.createElement("h3");
                    title.textContent = algo;
                    wrapper.appendChild(title);

                    const cloneCanvas = document.createElement("canvas");
                    cloneCanvas.style.width = "100%";
                    cloneCanvas.style.height = "auto";
                    wrapper.appendChild(cloneCanvas);
                    modalContainer.appendChild(wrapper);

                    const modalDrawingScale = 1.0;

                    // 1. Zeichne den Grundriss auf den geklonten Canvas
                    wareHouseFloorPlan.renderBaseFloorToCanvas(cloneCanvas, modalDrawingScale);

                    // 2. Erhalte den Kontext des geklonten Canvas
                    const cloneCtx = cloneCanvas.getContext("2d");
                    const originalCtx = wareHouseFloorPlan.ctx; // Speichere den originalen Kontext

                    // 3. Setze den Canvas-Kontext des WarehouseFloorPlan-Objekts auf den Klon
                    wareHouseFloorPlan.ctx = cloneCtx;

                    // --- NEU: Zeichne die Picking Markers auf den geklonten Canvas ---
                    // 'stockLocations' ist die Variable, die du bereits hast
                    wareHouseFloorPlan.drawPickingMarkers(stockLocations);

                    // 4. Zeichne die Route auf den geklonten Canvas
                    if (algo === "christofides") {
                        wareHouseFloorPlan.drawWarehouseRoute(algoData.route, "yellow");
                    }
                    if (algo === "nearestNeighbor") {
                        wareHouseFloorPlan.drawWarehouseRoute(algoData.route, "red");
                    }
                    if (algo === "fixedParameter") {
                        wareHouseFloorPlan.drawRouteSegments(algoData.route, "pink");
                    }

                    // 5. Setze den Kontext des WarehouseFloorPlan-Objekts zurück auf den Original-Canvas
                    wareHouseFloorPlan.ctx = originalCtx;
                });
            }


        })
        .catch(error => console.error('Error:', error));
});

document.querySelector(".modal-close").addEventListener("click", () => {
    document.getElementById("comparison-modal").classList.remove("show");
});