# Vendored frontend dependency

`plotly-2.35.2.min.js` is a verbatim copy of

    https://cdn.plot.ly/plotly-2.35.2.min.js

downloaded on 2026-08-21, 4,558,696 bytes. It is licensed under the MIT
license, Copyright 2012-2024 Plotly, Inc. The copyright notice is preserved in
the header of the file itself.

The library renders the two benchmark diagrams in `BenchmarkCharts.js`. It is
kept in the repository rather than loaded from the CDN so that the container
works without internet access, which keeps the reproduction path self
contained. Nothing else in the application uses it, and no measurement depends
on it.
