class WarehouseFloorPlan {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext("2d");
        this.dpr = window.devicePixelRatio || 1;
        this.setupCanvas();
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
    }

    drawPackingTable() {
        // calculate the position of the packing table relative to the number of and crossings (Y)
        let offset = (this.numCrossings * 7 * this.verticalGridSize) / 2;
        let startPositionY = (this.canvas.height / 2) + offset;
        let positionY = startPositionY - this.numCrossings * (this.verticalGridSize * 7);

        let positionX = (this.canvas.width / 2) - 2 * this.horizontalGridSize;
        this.ctx.rect(positionX, positionY, this.horizontalGridSize * 3, this.horizontalGridSize); // x, y, width, height
        this.ctx.fillStyle = "lightblue";
        this.ctx.fill(); // Draw the outline

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

    drawPickingMarker(positionX, positionY) {
        // draws a small red dot to indicate the picking location
        this.ctx.beginPath();
        this.ctx.arc(positionX, positionY, Math.max(this.horizontalGridSize, this.verticalGridSize) / 12, 0, 2 * Math.PI);
        this.ctx.stroke();
        this.ctx.fillStyle = "red";
        this.ctx.fill();
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

        this.marginVertical = 20;
        this.marginHorizontal = 20;

        this.shelfHeight = 6;

        // the grid sizes are dynamically calculated based on the number of aisles and the screen height
        this.verticalGridSize = this.canvas.height / ((numCrossings * 7) + this.marginVertical);
        this.horizontalGridSize = this.canvas.width / (numAisles * 4 + this.marginHorizontal);

        this.offset = (numCrossings * 7 * this.verticalGridSize) / 2;
        this.startPositionY = (this.canvas.height / 2) + this.offset;

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
}


const wareHouseFloorPlan = new WarehouseFloorPlan("warehouseCanvas");
const changeWarehouseFloorPlanButton = document.getElementById("changeWarehouseFloorPlan");
const generateLocationTestSetButton = document.getElementById("generateLocationsButton");

wareHouseFloorPlan.drawStorageShelfFloorPlan(3, 2, wareHouseFloorPlan.canvas.height, wareHouseFloorPlan.canvas.width);
wareHouseFloorPlan.drawPickingMarker(wareHouseFloorPlan.normalizedCoordinate.x, wareHouseFloorPlan.normalizedCoordinate.y);
wareHouseFloorPlan.drawWarehouseRoute([{x: 0, y: 30.5}, {x: 50, y: 30.5}]);

changeWarehouseFloorPlanButton.addEventListener("click", function () {
    let aisles = document.getElementById("warehouseAisleCount").value;
    let crossings = document.getElementById("warehouseCrossingCount").value;

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
            alert(data.message);
        })
        .catch(error => console.error('Error:', error));
});

