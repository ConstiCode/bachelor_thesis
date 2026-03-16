export default class ApiService {

    async generateLocations(model, productCount, locationGenerationSeed) {
        const response = await fetch('/generate-test-locations', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                warehouse_config: model.getConfigForAPI(),
                product_count: productCount,
                location_generation_seed: locationGenerationSeed,
            })
        });

        if (!response.ok) {
            const body = await response.json();
            throw new Error(body.error_message || `HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }

    async calculateRoutes(model, locations, algorithms) {
        const response = await fetch('/calculate-route', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                warehouse_config: model.getConfigForAPI(),
                locations: locations,
                algorithms: algorithms
            })
        });

        if (!response.ok) {
            const body = await response.json();
            throw new Error(body.error_message || `HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }
}