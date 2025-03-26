let c = document.getElementById("warehouseCanvas");
let ctx = c.getContext("2d");

// Adjust for high DPI screens
let dpr = window.devicePixelRatio || 1; // Get device pixel ratio
let rect = c.getBoundingClientRect(); // Get canvas's display size

c.width = rect.width * dpr; // Set actual width
c.height = rect.height * dpr; // Set actual height

ctx.scale(dpr, dpr); // Scale the context

// Create the Packing Table (Rectangle)
function drawPackingTable(numAisles, horizontalGridSize, verticalGridSize, screenHeight, screenWidth) {
    let positionX = (screenWidth / 2) - ((numAisles * 4 * horizontalGridSize) / 2);

    ctx.rect(positionX, verticalGridSize, horizontalGridSize * 3, verticalGridSize); // x, y, width, height
    ctx.fillStyle = "lightblue";
    ctx.fill(); // Draw the outline

// Set text styles
    ctx.font = "15px Arial";
    ctx.fillStyle = "black";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";

// Calculate text position (center of the rectangle)
    let textX = positionX + (horizontalGridSize * 3) / 2;
    let textY = verticalGridSize + verticalGridSize / 2;

    ctx.fillText("Packing Table", textX, textY);
}

function drawStorageShelf(positionX, positionY, horizontalGridSize, shelfHeight) {
    ctx.beginPath();
    ctx.rect(positionX, positionY, 2 * horizontalGridSize, shelfHeight); // x, y, width, height
    ctx.fillStyle = "lightblue";
    ctx.fill();

}

function drawStorageShelfRow(startPositionY, horizontalGridSize, shelfHeight, numAisles, screenWidth) {
    let offset = (numAisles * 4 * horizontalGridSize) / 2;
    let startPosition = (screenWidth / 2) - offset;

    for (let i = 0; i < numAisles; i++) {
        drawStorageShelf(startPosition, startPositionY, horizontalGridSize, shelfHeight);
        startPosition = startPosition + 4 * horizontalGridSize;
    }
}

function drawStorageShelfFloorPlan(numAisles, numCrossing, screenHeight, screenWidth) {
    // Set the canvas background color
    ctx.fillStyle = "#1e1e1e";
    ctx.fillRect(0, 0, c.width, c.height);

    let marginVertical = 20;
    let marginHorizontal = 20;

    // the grid sizes are dynamically calculated based on the number of aisles and the screen height
    let verticalGridSizeAmount = Math.floor(screenHeight / ((numCrossing * 7) + marginVertical));
    let horizontalGridSizeAmount = Math.floor(screenWidth / (numAisles * 4 + marginHorizontal));


    let verticalGridSize = verticalGridSizeAmount // Math.floor(screenHeight / verticalGridSizeAmount);
    let horizontalGridSize = horizontalGridSizeAmount // Math.floor(screenWidth / horizontalGridSizeAmount);

    let offset = (numCrossing * 7 * verticalGridSize) / 2;
    let startPositionY = (screenHeight / 2) + offset;

    for (let i = 0; i < numCrossing; i++) {
        drawStorageShelfRow(startPositionY, horizontalGridSize, verticalGridSize * 6, numAisles, screenWidth);
        startPositionY -= verticalGridSize * 7;
    }

    // Todo get the packing table to the right position
    drawPackingTable(numAisles, horizontalGridSize, verticalGridSize, screenHeight, screenWidth)
}

drawStorageShelfFloorPlan(4, 3, c.height, c.width);

document.getElementById("changeWarehouseFloorPlan").addEventListener("click", function () {
    let aisles = document.getElementById("warehouseAisleCount").value;
    let crossings = document.getElementById("warehouseCrossingCount").value;

    if (aisles < 1 || crossings < 1) {
        alert("Please enter a valid number for aisles and crossings");
        return;
    }

    ctx.clearRect(0, 0, c.width, c.height);
    drawStorageShelfFloorPlan(aisles, crossings, c.height, c.width);
});
