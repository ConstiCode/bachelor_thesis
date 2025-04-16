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
        let positionY = startPositionY - this.numCrossings * (this.verticalGridSize * 7);

        let positionX = ((this.canvas.width / 2) - 2 * this.horizontalGridSize) - 0.5 * this.horizontalGridSize;
        this.ctx.rect(positionX, positionY, this.horizontalGridSize * 3, this.horizontalGridSize); // x, y, width, height
        this.ctx.fillStyle = "lightblue";
        this.ctx.fill(); // Draw the outline

        this.positionPackingTable = { x: positionX, y: positionY }; // Todo check if this is correct and adjust for center


        // Set text styles
        let fontSize = Math.floor(45 / this.numAisles);
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
        let offset = (this.numAisles * 4 * this.horizontalGridSize) / 2;
        let startPosition = (this.canvas.width / 2) - offset;

        this.normalizedCoordinate.x = startPosition;

        for (let i = 0; i < this.numAisles; i++) {
            this.drawStorageShelf(startPosition, this.startPositionY, this.horizontalGridSize);
            startPosition = startPosition + 4 * this.horizontalGridSize;
        }
    }

    drawPickingMarkers(positions) {
        // draws a small red dots for a given array of stock locations
        for (let i = 0; i < positions.length; i++) {
            let offsetX = this.normalizedCoordinate.x;
            let offsetY = this.normalizedCoordinate.y;
            let x = (positions[i].x * this.horizontalGridSize + 0.5 * this.horizontalGridSize) + offsetX;
            let y = (positions[i].y * this.verticalGridSize + 0.5 * this.verticalGridSize) + offsetY;

            this.ctx.beginPath();
            this.ctx.arc(x, y, Math.max(this.horizontalGridSize, this.verticalGridSize) / 12, 0, 2 * Math.PI);
            this.ctx.stroke();
            this.ctx.fillStyle = "red";
            this.ctx.fill();
        }
    }

    drawWarehouseRoute(route) {
        // draw the route that is given in tuples from the backend
        //      - valid aisles are multiples of xStart + or -4 as one shelf is 2 grids wide
        //      - valid columns are multiples of xStart + 0,5 offset and + or minus 6

        this.ctx.beginPath();
        for (let i = 0; i < route.length; i++) {
            this.ctx.lineTo(route[i].x * this.horizontalGridSize, route[i].y * this.verticalGridSize);
            this.ctx.strokeStyle = "red";
        }
        this.ctx.strokeStyle = "red"; // Set the line color to red
        this.ctx.lineWidth = 3;
        this.ctx.stroke();
    }

    drawStorageShelfFloorPlan(numAisles, numCrossings) {
        this.clearCanvas();
        this.numAisles = numAisles;
        this.numCrossings = numCrossings;

        let marginVertical = 20;
        let marginHorizontal = 20;

        this.shelfHeight = 6;

        // the grid sizes are dynamically calculated based on the number of aisles and the screen height
        this.verticalGridSize = this.canvas.height / ((numCrossings * 7) + marginVertical);
        this.horizontalGridSize = this.canvas.width / (numAisles * 4 + marginHorizontal);

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
}


const wareHouseFloorPlan = new WarehouseFloorPlan("warehouseCanvas", true);
const changeWarehouseFloorPlanButton = document.getElementById("changeWarehouseFloorPlan");
const generateLocationTestSetButton = document.getElementById("generateLocationsButton");
const triggerRouteCalculationButton = document.getElementById("triggerRouteCalculationButton");

// draw an initial warehouse floor plan
wareHouseFloorPlan.drawStorageShelfFloorPlan(5, 3, wareHouseFloorPlan.canvas.height, wareHouseFloorPlan.canvas.width);

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
            // store the locations in local storage for later route calculation
            localStorage.setItem("stockLocations", JSON.stringify(data));

            // draw the locations on the canvas
            wareHouseFloorPlan.drawPickingMarkers(data);

            // display the locations in a table
            let tableBody = document.querySelector("#locationTable tbody")
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

function checkSelected() {
    const checkboxes = document.querySelectorAll('input[name="selections"]:checked');
    let algorithms =  Array.from(checkboxes).map(cb => cb.value);
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

    fetch('/calculate-route', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            packing_table: {
                x : wareHouseFloorPlan.positionPackingTable.x,
                y : wareHouseFloorPlan.positionPackingTable.y
            },
            locations: stockLocations,
            algorithms: checkSelected()
        })
    })
        .then(response => response.json())
        .then(data => {
            // draw the route on the canvas
            console.log(wareHouseFloorPlan.positionPackingTable);
            wareHouseFloorPlan.drawWarehouseRoute(data);
        })
        .catch(error => console.error('Error:', error));
});
