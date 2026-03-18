import { renderAllCharts } from "./BenchmarkCharts.js";

export default class BenchmarkView {
    constructor() {
        // Sidebar inputs
        this.configList = document.getElementById("warehouseConfigList");
        this.addConfigBtn = document.getElementById("addWarehouseConfig");
        this.productCountsInput = document.getElementById("benchmarkProductCounts");
        this.iterationsInput = document.getElementById("benchmarkIterations");
        this.baseSeedInput = document.getElementById("benchmarkBaseSeed");
        this.timeoutInput = document.getElementById("benchmarkTimeout");
        this.runBtn = document.getElementById("runBenchmarkButton");
        this.exportBtn = document.getElementById("exportCsvButton");

        // Preview
        this.totalCombinationsEl = document.getElementById("totalCombinations");
        this.totalRunsEl = document.getElementById("totalRuns");

        // Results area (left side)
        this.resultsArea = document.getElementById("benchmarkResultsArea");
        this.progressSection = document.getElementById("benchmarkProgress");
        this.progressTitle = document.getElementById("progressTitle");
        this.progressDetail = document.getElementById("progressDetail");
        this.progressBar = document.getElementById("progressBar");
        this.progressPercent = document.getElementById("progressPercent");
        this.resultsView = document.getElementById("benchmarkResultsView");
        this.summaryCards = document.getElementById("summaryCards");
        this.resultsTableBody = document.querySelector("#benchmarkResultsTable tbody");

        this._initConfigRows();
        this._initPreviewUpdater();
        this._initAddConfigBtn();
    }

    // --- Warehouse config rows ---

    _initConfigRows() {
        this._addConfigRow(2, 1);
    }

    _initAddConfigBtn() {
        this.addConfigBtn.addEventListener("click", () => this._addConfigRow(2, 1));
    }

    _addConfigRow(cols, rows) {
        const row = document.createElement("div");
        row.className = "config-row";
        row.innerHTML = `
            <span class="config-label">Col</span>
            <input type="number" class="config-cols" value="${cols}" min="1"/>
            <span class="config-label">Row</span>
            <input type="number" class="config-rows" value="${rows}" min="1"/>
            <button class="remove-config-btn" title="Remove">&times;</button>
        `;
        row.querySelector(".remove-config-btn").addEventListener("click", () => {
            if (this.configList.children.length > 1) {
                row.remove();
                this._updatePreview();
            }
        });
        // Update preview when values change
        row.querySelectorAll("input").forEach(input => {
            input.addEventListener("input", () => this._updatePreview());
        });
        this.configList.appendChild(row);
        this._updatePreview();
    }

    // --- Preview ---

    _initPreviewUpdater() {
        this.productCountsInput.addEventListener("input", () => this._updatePreview());
        this.iterationsInput.addEventListener("input", () => this._updatePreview());
    }

    _updatePreview() {
        const configs = this.getWarehouseConfigs();
        const products = this.getProductCounts();
        const iterations = this.getIterations();
        const algorithms = this.getSelectedAlgorithms();

        const combinations = configs.length * products.length * iterations;
        const totalRuns = combinations * algorithms.length;

        this.totalCombinationsEl.textContent = combinations;
        this.totalRunsEl.textContent = totalRuns;
    }

    // --- Getters ---

    getWarehouseConfigs() {
        const rows = this.configList.querySelectorAll(".config-row");
        return Array.from(rows).map(row => ({
            numColumns: parseInt(row.querySelector(".config-cols").value) || 0,
            numCrossings: parseInt(row.querySelector(".config-rows").value) || 0
        })).filter(c => c.numColumns > 0 && c.numCrossings > 0);
    }

    getProductCounts() {
        const raw = this.productCountsInput.value;
        return raw.split(",")
            .map(s => parseInt(s.trim()))
            .filter(n => !isNaN(n) && n > 0);
    }

    getSelectedAlgorithms() {
        const checkboxes = document.querySelectorAll('input[name="benchmarkAlgorithm"]:checked');
        return Array.from(checkboxes).map(cb => cb.value);
    }

    getIterations() {
        return parseInt(this.iterationsInput.value) || 0;
    }

    getBaseSeed() {
        return parseInt(this.baseSeedInput.value) || 0;
    }

    getTimeout() {
        return parseInt(this.timeoutInput.value) || 300;
    }

    // --- Binding ---

    bindRunBenchmark(handler) {
        this.runBtn.addEventListener("click", handler);
    }

    bindExportCsv(handler) {
        this.exportBtn.addEventListener("click", handler);
    }

    // --- Progress UI ---

    showProgress() {
        this.progressSection.classList.remove("hidden");
        this.resultsView.classList.add("hidden");
        this.setProgress(0, 0);
    }

    setProgress(current, total) {
        const pct = total > 0 ? Math.round((current / total) * 100) : 0;
        this.progressDetail.textContent = `Combination ${current} / ${total}`;
        this.progressBar.style.width = `${pct}%`;
        this.progressPercent.textContent = `${pct}%`;
    }

    hideProgress() {
        this.progressSection.classList.add("hidden");
    }

    // --- Results rendering ---

    showResults(results) {
        this.hideProgress();
        this.resultsView.classList.remove("hidden");
        this._renderSummaryCards(results);
        renderAllCharts(results);
        this._renderResultsTable(results);
    }

    _renderSummaryCards(results) {
        this.summaryCards.innerHTML = "";

        const okResults = results.filter(r => r.status === "ok");
        const timeouts = results.filter(r => r.status === "timeout").length;

        // Total runs card
        this._addSummaryCard("Total Runs", results.length,
            `${okResults.length} ok, ${timeouts} timeouts`, "accent-info");

        // Per-algorithm summary
        const algorithms = [...new Set(results.map(r => r.algorithm))];
        const accentMap = {
            nearestNeighbor: "accent-nn",
            christofides: "accent-christofides",
            fixedParameter: "accent-fixed",
            scfsPlus: "accent-scfs"
        };
        const nameMap = {
            nearestNeighbor: "Nearest Neighbor",
            christofides: "Christofides",
            fixedParameter: "Fixed Parameter (DP)",
            scfsPlus: "SCFS+ (MILP)"
        };

        for (const algo of algorithms) {
            const algoResults = okResults.filter(r => r.algorithm === algo);
            if (algoResults.length === 0) continue;

            const avgLength = algoResults.reduce((sum, r) => sum + r.route_length, 0) / algoResults.length;
            const avgTime = algoResults.reduce((sum, r) => sum + r.computation_time_ms, 0) / algoResults.length;

            this._addSummaryCard(
                nameMap[algo] || algo,
                Math.round(avgLength),
                `avg length | ${avgTime.toFixed(1)} ms avg time`,
                accentMap[algo] || "accent-info"
            );
        }
    }

    _addSummaryCard(label, value, sub, accentClass) {
        const card = document.createElement("div");
        card.className = `summary-card ${accentClass}`;
        card.innerHTML = `
            <div class="card-label">${label}</div>
            <div class="card-value">${value}</div>
            <div class="card-sub">${sub}</div>
        `;
        this.summaryCards.appendChild(card);
    }

    _renderResultsTable(results) {
        this.resultsTableBody.innerHTML = "";

        const nameMap = {
            nearestNeighbor: "Nearest Neighbor",
            christofides: "Christofides",
            fixedParameter: "Fixed Parameter (DP)",
            scfsPlus: "SCFS+ (MILP)"
        };

        for (const r of results) {
            const row = document.createElement("tr");
            row.innerHTML = `
                <td>${nameMap[r.algorithm] || r.algorithm}</td>
                <td>${r.num_columns}</td>
                <td>${r.num_crossings}</td>
                <td>${r.num_products}</td>
                <td>${r.iteration}</td>
                <td>${r.route_length !== null ? r.route_length : r.status}</td>
                <td>${r.computation_time_ms !== null ? r.computation_time_ms.toFixed(1) : "-"}</td>
                <td>${r.seed}</td>
            `;
            this.resultsTableBody.appendChild(row);
        }
    }

    // --- Button state ---

    setRunning(isRunning) {
        this.runBtn.disabled = isRunning;
        this.runBtn.textContent = isRunning ? "Running..." : "Run Benchmark";
    }
}