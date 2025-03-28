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
        let offset = (this.numCrossing * 7 * this.verticalGridSize) / 2;
        let startPositionY = (this.canvas.height / 2) + offset;
        let positionY = startPositionY - this.numCrossing * (this.verticalGridSize * 7);

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

    drawPickingMarker(positionX, positionY, horizontalGridSize, verticalGridSize) {
        // draws a small red dot to indicate the picking location
        this.ctx.beginPath();
        this.ctx.arc(positionX, positionY, Math.max(horizontalGridSize, verticalGridSize) / 5, 0, 2 * Math.PI);
        this.ctx.stroke();
        this.ctx.fillStyle = "red";
        this.ctx.fill();
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

        for (let i = 0; i < this.numAisles; i++) {
            this.drawStorageShelf(startPosition, this.startPositionY, this.horizontalGridSize);
            startPosition = startPosition + 4 * this.horizontalGridSize;
        }
    }

    drawStorageShelfFloorPlan(numAisles, numCrossings) {
        this.clearCanvas();
        this.numAisles = numAisles;
        this.numCrossing = numCrossings;

        this.marginVertical = 20;
        this.marginHorizontal = 20;

        this.shelfHeight = 6;

        // the grid sizes are dynamically calculated based on the number of aisles and the screen height
        this.verticalGridSize = Math.floor(this.canvas.height / ((numCrossings * 7) + this.marginVertical));
        this.horizontalGridSize = Math.floor(this.canvas.width / (numAisles * 4 + this.marginHorizontal));

        this.offset = (numCrossings * 7 * this.verticalGridSize) / 2;
        this.startPositionY = (this.canvas.height / 2) + this.offset;

        for (let i = 0; i < numCrossings; i++) {
            this.drawStorageShelfRow(this.startPositionY, this.horizontalGridSize, numAisles);
            this.startPositionY -= this.verticalGridSize * 7;
        }

        // draw the packing table that is the start and end point of the route
        this.drawPackingTable();
        this.drawPickingMarker();
    }
}

const wareHouseFloorPlan = new WarehouseFloorPlan("warehouseCanvas");
wareHouseFloorPlan.drawStorageShelfFloorPlan(4, 3, wareHouseFloorPlan.canvas.height, wareHouseFloorPlan.canvas.width);

document.getElementById("changeWarehouseFloorPlan").addEventListener("click", function () {
    let aisles = document.getElementById("warehouseAisleCount").value;
    let crossings = document.getElementById("warehouseCrossingCount").value;

    if (aisles < 1 || crossings < 1) {
        alert("Please enter a valid number for aisles and crossings");
        return;
    }
    wareHouseFloorPlan.drawStorageShelfFloorPlan(aisles, crossings);
});
/*
document.getElementById("generateLocationTestSet").addEventListener("click", function() {
    let productCount = document.getElementById("generateLocationTestSet").value;

    fetch('/generate-test-locations', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ product_count: productCount,
                               warehouse_aisles: document.getElementById("warehouseAisleCount").value,
                               warehouse_crossings: document.getElementById("warehouseCrossingCount").value,
                               warehouse_width: })
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
    })
    .catch(error => console.error('Error:', error));
});

*/
