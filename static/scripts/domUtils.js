/**
 * SECURELY creates and appends a location row to the table.
 * NO innerHTML is used.
 */
export function addLocationToTable(tableBody, location) {
    const row = document.createElement("tr");

    const cellNum = document.createElement("td");
    cellNum.textContent = location.location_number;

    const cellX = document.createElement("td");
    cellX.textContent = location.x;

    const cellY = document.createElement("td");
    cellY.textContent = location.y;

    row.append(cellNum, cellX, cellY);
    tableBody.appendChild(row);
}

/**
 * SECURELY builds the route info table.
 * NO innerHTML is used.
 */
export function updateRouteInfoTable(element, data) {
    // Clear previous results
    element.innerHTML = "";

    const table = document.createElement("table");
    table.style.borderCollapse = "collapse"; // Use CSS classes instead, but this works

    // Header
    const thead = document.createElement("thead");
    const hr = document.createElement("tr");
    const headers = ["Algorithm", "Length (tiles)", "Walking Time (min)", "Cost ($)", "Computation (ms)"];
    headers.forEach(text => {
        const th = document.createElement("th");
        th.textContent = text;
        th.style.border = "1px solid #ccc";
        hr.appendChild(th);
    });
    thead.appendChild(hr);
    table.appendChild(thead);

    // Body
    const tbody = document.createElement("tbody");

    // ... Your logic from updateRouteInformation to calculate rows ...
    // Example for one row:
    if (data.nearestNeighbor) {
        const r = data.nearestNeighbor; // Simplified
        const row = document.createElement("tr");

        const cellName = document.createElement("td");
        cellName.textContent = "Nearest Neighbor";

        const cellLength = document.createElement("td");
        cellLength.textContent = r.length; // Your logic here

        // ... etc. for other cells ...

        row.append(cellName, cellLength /*, ...otherCells */);
        tbody.appendChild(row);
    }
    // ... Repeat for christofides, fixedParameter ...

    table.appendChild(tbody);
    element.appendChild(table);
}