/* =========================================================
 * SALES BI DASHBOARD
 * =========================================================
 *
 * Responsibilities of this file:
 *
 *   - request KPI and analytics data from the backend
 *   - manage loading / error / empty states
 *   - format values for presentation only
 *   - render charts from the returned data
 *   - handle theme switching
 *
 * This file does NOT calculate business KPIs.
 * The backend BI layer is the single source of truth.
 * ======================================================= */

(function () {

    "use strict";

    // =====================================================
    // CONFIGURATION
    // =====================================================

    const CONFIG = {

        endpoints: {
            summary: "/api/dashboard/summary",
            trend: "/api/dashboard/trend",
            categories: "/api/dashboard/categories",
            states: "/api/dashboard/states",
            status: "/api/dashboard/status",
            fulfilment: "/api/dashboard/fulfilment",
            channels: "/api/dashboard/channels",
            products: "/api/dashboard/top-products"
        },

        locale: "en-IN",

        currency: "INR",

        // Metric that must be present for the dashboard
        // to be considered populated.
        presenceKey: "total_rows",

        // Chart display limits.
        topCategories: 9,
        topStates: 10,
        topStatuses: 8,

        themeStorageKey: "salesbi-theme"
    };


    // =====================================================
    // STATE
    // =====================================================

    const dashboardState = {

        summary: null,

        analytics: {
            trend: null,
            categories: null,
            states: null,
            status: null,
            fulfilment: null,
            channels: null,
            products: null
        },

        loading: false,

        error: null,

        lastUpdated: null,

        theme: "light"
    };


    // =====================================================
    // ELEMENT REFERENCES
    // =====================================================

    const elements = {};


    function cacheElements() {

        const byId = function (id) {
            return document.getElementById(id);
        };

        elements.workspace = byId("workspace");
        elements.statStrip = byId("statStrip");
        elements.metricList = byId("metricList");

        elements.errorState = byId("errorState");
        elements.errorMessage = byId("errorMessage");
        elements.emptyState = byId("emptyState");

        elements.refreshButton = byId("refreshButton");
        elements.retryButton = byId("retryButton");

        elements.themeToggle = byId("themeToggle");
        elements.themeIcon = byId("themeIcon");

        elements.datasetLabel = byId("datasetLabel");
        elements.railPeriod = byId("railPeriod");
        elements.lastUpdated = byId("lastUpdated");

        elements.valueNodes = Array.prototype.slice.call(
            document.querySelectorAll("[data-kpi]")
        );

        elements.charts = {};

        document.querySelectorAll("[data-chart]").forEach(function (node) {
            elements.charts[node.getAttribute("data-chart")] = node;
        });

        elements.metas = {};

        document.querySelectorAll("[data-meta]").forEach(function (node) {
            elements.metas[node.getAttribute("data-meta")] = node;
        });

        elements.sparks = {};

        document.querySelectorAll("[data-spark]").forEach(function (node) {
            elements.sparks[node.getAttribute("data-spark")] = node;
        });

        elements.sparkCaptions = {};

        document.querySelectorAll("[data-spark-caption]")
            .forEach(function (node) {
                elements.sparkCaptions[
                    node.getAttribute("data-spark-caption")
                ] = node;
            });
    }


    // =====================================================
    // FORMATTING
    // =====================================================
    //
    // Presentation only. The underlying API values are
    // never mutated.
    // =====================================================

    const numberFormatter = new Intl.NumberFormat(CONFIG.locale);

    const currencyFormatter = new Intl.NumberFormat(CONFIG.locale, {
        style: "currency",
        currency: CONFIG.currency,
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });

    const compactFormatter = new Intl.NumberFormat(CONFIG.locale, {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });

    const shortFormatter = new Intl.NumberFormat(CONFIG.locale, {
        minimumFractionDigits: 1,
        maximumFractionDigits: 1
    });


    function toFiniteNumber(value) {

        if (value === null || value === undefined) {
            return null;
        }

        const parsed = Number(value);

        return Number.isFinite(parsed) ? parsed : null;
    }


    function formatNumber(value) {

        const parsed = toFiniteNumber(value);

        return parsed === null ? "—" : numberFormatter.format(parsed);
    }


    function formatCurrency(value) {

        const parsed = toFiniteNumber(value);

        return parsed === null ? "—" : currencyFormatter.format(parsed);
    }


    /**
     * Large monetary values shortened for display.
     *
     *   78592678.3  ->  ₹78.59M
     *   574.84      ->  ₹574.84
     */
    function formatCurrencyCompact(value, digits) {

        const parsed = toFiniteNumber(value);

        if (parsed === null) {
            return "—";
        }

        const formatter = digits === 1 ? shortFormatter : compactFormatter;
        const absolute = Math.abs(parsed);

        const units = [
            { limit: 1e9, suffix: "B" },
            { limit: 1e6, suffix: "M" },
            { limit: 1e3, suffix: "K" }
        ];

        for (let index = 0; index < units.length; index += 1) {

            const unit = units[index];

            if (absolute >= unit.limit) {
                return "₹" + formatter.format(parsed / unit.limit) +
                    unit.suffix;
            }
        }

        return formatCurrency(parsed);
    }


    function formatValue(value, format) {

        if (format === "currency") {
            return formatCurrency(value);
        }

        if (format === "currency-compact") {
            return formatCurrencyCompact(value);
        }

        return formatNumber(value);
    }


    function formatPercent(value) {

        const parsed = toFiniteNumber(value);

        return parsed === null ? "—" : shortFormatter.format(parsed) + "%";
    }


    function formatShortDate(iso) {

        const date = new Date(iso + "T00:00:00");

        if (Number.isNaN(date.getTime())) {
            return iso;
        }

        return date.toLocaleDateString(CONFIG.locale, {
            day: "numeric",
            month: "short"
        });
    }


    function titleCase(text) {

        if (!text) {
            return "Unknown";
        }

        return String(text)
            .toLowerCase()
            .replace(/\b[a-z]/g, function (character) {
                return character.toUpperCase();
            });
    }


    function formatTimestamp(date) {

        if (!date) {
            return "";
        }

        return "Last updated " + date.toLocaleString(CONFIG.locale, {
            dateStyle: "medium",
            timeStyle: "short"
        });
    }


    // =====================================================
    // DOM HELPERS
    // =====================================================

    const SVG_NS = "http://www.w3.org/2000/svg";


    function setHidden(element, hidden) {

        if (element) {
            element.hidden = Boolean(hidden);
        }
    }


    function createElement(tag, className, text) {

        const node = document.createElement(tag);

        if (className) {
            node.className = className;
        }

        if (text !== undefined && text !== null) {
            node.textContent = text;
        }

        return node;
    }


    function createSvg(tag, attributes) {

        const node = document.createElementNS(SVG_NS, tag);

        Object.keys(attributes || {}).forEach(function (name) {
            node.setAttribute(name, attributes[name]);
        });

        return node;
    }


    function clearNode(node) {

        while (node.firstChild) {
            node.removeChild(node.firstChild);
        }
    }


    function renderChartMessage(container, message) {

        clearNode(container);
        container.appendChild(createElement("div", "chart__empty", message));
    }


    /**
     * Builds the "M… L…" path for a series scaled into a
     * width x height box, plus the closed area variant.
     */
    function buildPaths(values, width, height) {

        const maximum = Math.max.apply(null, values);
        const range = maximum || 1;
        const stepX = width / (values.length - 1);

        const line = values.map(function (value, index) {

            const x = index * stepX;
            const y = height - (value / range) * height;

            return (index === 0 ? "M" : "L") +
                x.toFixed(2) + " " + y.toFixed(2);

        }).join(" ");

        const area = line +
            " L" + width.toFixed(2) + " " + height +
            " L0 " + height + " Z";

        return { line: line, area: area, maximum: maximum };
    }


    // =====================================================
    // CHART RENDERERS
    // =====================================================

    /**
     * Vertical column chart with a value scale and
     * wrapping category labels.
     *
     * rows: [{ label, value, display }]
     */
    function renderColumnChart(container, rows) {

        clearNode(container);

        if (!rows.length) {
            renderChartMessage(container, "No data available.");
            return;
        }

        const maximum = rows.reduce(function (largest, row) {
            return Math.max(largest, row.value || 0);
        }, 0);

        const chart = createElement("div", "column-chart");

        // Value scale
        const scale = createElement("div", "column-chart__scale");

        [1, 0.75, 0.5, 0.25, 0].forEach(function (fraction) {
            scale.appendChild(
                createElement(
                    "span",
                    null,
                    formatCurrencyCompact(maximum * fraction, 1)
                )
            );
        });

        chart.appendChild(scale);

        const plot = createElement("div", "column-chart__plot");

        // Gridlines
        const grid = createElement("div", "column-chart__grid");

        for (let index = 0; index < 5; index += 1) {
            grid.appendChild(createElement("div", "column-chart__grid-line"));
        }

        plot.appendChild(grid);

        // Bars
        const bars = createElement("div", "column-chart__bars");

        rows.forEach(function (row) {

            const wrap = createElement("div", "column-chart__bar-wrap");

            const bar = createElement("div", "column-chart__bar");

            const percent = maximum > 0
                ? (row.value / maximum) * 100
                : 0;

            bar.style.height = Math.max(percent, 0.4).toFixed(2) + "%";
            bar.title = row.label + " — " + row.display;

            wrap.appendChild(bar);
            bars.appendChild(wrap);
        });

        plot.appendChild(bars);

        // Labels
        const labels = createElement("div", "column-chart__labels");

        rows.forEach(function (row) {

            const label = createElement(
                "span",
                "column-chart__label",
                row.label
            );

            label.title = row.label + " — " + row.display;

            labels.appendChild(label);
        });

        plot.appendChild(labels);

        chart.appendChild(plot);

        container.appendChild(chart);
    }


    /**
     * Compact sparkline for a metric card.
     */
    function renderSparkline(container, values) {

        clearNode(container);

        if (!Array.isArray(values) || values.length < 2) {
            return;
        }

        const width = 300;
        const height = 56;

        const paths = buildPaths(values, width, height);

        const svg = createSvg("svg", {
            "class": "sparkline",
            viewBox: "0 0 " + width + " " + height,
            preserveAspectRatio: "none",
            "aria-hidden": "true",
            focusable: "false"
        });

        svg.appendChild(createSvg("path", {
            "class": "sparkline__area",
            d: paths.area
        }));

        svg.appendChild(createSvg("path", {
            "class": "sparkline__line",
            d: paths.line
        }));

        container.appendChild(svg);
    }


    /**
     * Horizontal bar chart.
     *
     * rows: [{ label, value, display, variant }]
     */
    function renderBarChart(container, rows) {

        clearNode(container);

        if (!rows.length) {
            renderChartMessage(container, "No data available.");
            return;
        }

        const maximum = rows.reduce(function (largest, row) {
            return Math.max(largest, row.value || 0);
        }, 0);

        const chart = createElement("div", "bar-chart");

        rows.forEach(function (row) {

            const variant = row.variant ? " bar-row--" + row.variant : "";

            const line = createElement("div", "bar-row" + variant);

            const label = createElement("span", "bar-row__label", row.label);
            label.title = row.label;

            const track = createElement("div", "bar-row__track");
            const fill = createElement("div", "bar-row__fill");

            const percent = maximum > 0 ? (row.value / maximum) * 100 : 0;

            fill.style.width = percent.toFixed(2) + "%";

            track.appendChild(fill);

            line.appendChild(label);
            line.appendChild(track);
            line.appendChild(
                createElement("span", "bar-row__value", row.display)
            );

            chart.appendChild(line);
        });

        container.appendChild(chart);
    }


    /**
     * Trend line, drawn as inline SVG.
     *
     * points: [{ date, revenue }]
     */
    function renderLineChart(container, points) {

        clearNode(container);

        if (points.length < 2) {
            renderChartMessage(
                container,
                "Not enough data points to draw a trend."
            );
            return;
        }

        const width = 1000;
        const height = 150;

        const values = points.map(function (point) {
            return toFiniteNumber(point.revenue) || 0;
        });

        const paths = buildPaths(values, width, height);

        const wrapper = createElement("div", "line-chart");

        const scale = createElement("div", "line-chart__scale");
        scale.appendChild(
            createElement("span", null, formatCurrencyCompact(paths.maximum, 1))
        );
        scale.appendChild(createElement("span", null, "₹0"));
        wrapper.appendChild(scale);

        const svg = createSvg("svg", {
            "class": "line-chart__svg",
            viewBox: "0 0 " + width + " " + height,
            preserveAspectRatio: "none",
            role: "img",
            "aria-label":
                "Daily net revenue from " + points[0].date +
                " to " + points[points.length - 1].date
        });

        [0.25, 0.5, 0.75].forEach(function (fraction) {

            svg.appendChild(createSvg("line", {
                "class": "line-chart__grid",
                x1: "0",
                x2: String(width),
                y1: (height * fraction).toFixed(2),
                y2: (height * fraction).toFixed(2)
            }));
        });

        svg.appendChild(createSvg("path", {
            "class": "line-chart__area",
            d: paths.area
        }));

        svg.appendChild(createSvg("path", {
            "class": "line-chart__line",
            d: paths.line
        }));

        wrapper.appendChild(svg);

        const axis = createElement("div", "line-chart__axis");
        const middle = Math.floor(points.length / 2);

        [0, middle, points.length - 1].forEach(function (index) {
            axis.appendChild(
                createElement("span", null, formatShortDate(points[index].date))
            );
        });

        wrapper.appendChild(axis);

        container.appendChild(wrapper);
    }


    /**
     * Pie chart with percentage labels and a legend.
     *
     * segments: [{ label, value }]
     */
    function renderPieChart(container, segments) {

        clearNode(container);

        const usable = segments.filter(function (segment) {
            return (toFiniteNumber(segment.value) || 0) > 0;
        });

        const total = segments.reduce(function (sum, segment) {
            return sum + (toFiniteNumber(segment.value) || 0);
        }, 0);

        if (!segments.length || total <= 0) {
            renderChartMessage(container, "No data available.");
            return;
        }

        const SIZE = 200;
        const CENTRE = SIZE / 2;
        const RADIUS = 92;

        const wrapper = createElement("div", "pie-chart");

        const svg = createSvg("svg", {
            "class": "pie-chart__svg",
            viewBox: "0 0 " + SIZE + " " + SIZE,
            role: "img",
            "aria-label": segments.map(function (segment) {
                return segment.label + " " +
                    formatPercent((segment.value / total) * 100);
            }).join(", ")
        });

        // Start at 12 o'clock and sweep clockwise.
        let angle = -Math.PI / 2;

        segments.forEach(function (segment, index) {

            const value = toFiniteNumber(segment.value) || 0;

            if (value <= 0) {
                return;
            }

            const share = value / total;
            const sweep = share * Math.PI * 2;
            const variant = "pie-chart__slice pie-chart__slice--" +
                ((index % 4) + 1);

            // A single slice covering the whole circle cannot be
            // expressed as an arc, so draw it as a plain circle.
            if (usable.length === 1 || share >= 0.9999) {

                svg.appendChild(createSvg("circle", {
                    "class": variant,
                    cx: String(CENTRE),
                    cy: String(CENTRE),
                    r: String(RADIUS)
                }));

            } else {

                const end = angle + sweep;

                const x1 = CENTRE + RADIUS * Math.cos(angle);
                const y1 = CENTRE + RADIUS * Math.sin(angle);
                const x2 = CENTRE + RADIUS * Math.cos(end);
                const y2 = CENTRE + RADIUS * Math.sin(end);

                const largeArc = sweep > Math.PI ? 1 : 0;

                svg.appendChild(createSvg("path", {
                    "class": variant,
                    d: "M" + CENTRE + " " + CENTRE +
                       " L" + x1.toFixed(2) + " " + y1.toFixed(2) +
                       " A" + RADIUS + " " + RADIUS + " 0 " +
                       largeArc + " 1 " +
                       x2.toFixed(2) + " " + y2.toFixed(2) + " Z"
                }));
            }

            // Only label slices wide enough to hold the text.
            if (share >= 0.07) {

                const isWhole = usable.length === 1 || share >= 0.9999;
                const middle = angle + sweep / 2;

                const labelX = isWhole
                    ? CENTRE
                    : CENTRE + RADIUS * 0.6 * Math.cos(middle);

                const labelY = isWhole
                    ? CENTRE
                    : CENTRE + RADIUS * 0.6 * Math.sin(middle);

                const label = createSvg("text", {
                    "class": "pie-chart__slice-label",
                    x: labelX.toFixed(2),
                    y: labelY.toFixed(2),
                    "text-anchor": "middle",
                    "dominant-baseline": "central"
                });

                label.textContent = formatPercent(share * 100);

                svg.appendChild(label);
            }

            angle += sweep;
        });

        wrapper.appendChild(svg);

        const legend = createElement("div", "pie-chart__legend");

        segments.forEach(function (segment, index) {

            const item = createElement("div", "pie-chart__legend-item");

            item.appendChild(
                createElement(
                    "span",
                    "pie-chart__swatch pie-chart__swatch--" +
                        ((index % 4) + 1)
                )
            );

            item.appendChild(
                createElement(
                    "span",
                    "pie-chart__legend-label",
                    segment.label
                )
            );

            item.appendChild(
                createElement(
                    "span",
                    "pie-chart__legend-percent",
                    formatPercent((segment.value / total) * 100)
                )
            );

            item.appendChild(
                createElement(
                    "span",
                    "pie-chart__legend-value",
                    formatCurrencyCompact(segment.value)
                )
            );

            legend.appendChild(item);
        });

        wrapper.appendChild(legend);

        container.appendChild(wrapper);
    }


    /**
     * Top products table.
     */
    function renderProductsTable(container, products) {

        clearNode(container);

        if (!products.length) {
            renderChartMessage(container, "No product data available.");
            return;
        }

        const wrap = createElement("div", "data-table-wrap");
        const table = createElement("table", "data-table");

        const columns = [
            { label: "SKU", numeric: false },
            { label: "Style", numeric: false },
            { label: "Category", numeric: false },
            { label: "Units", numeric: true },
            { label: "Net Revenue", numeric: true }
        ];

        const thead = createElement("thead");
        const headRow = createElement("tr");

        columns.forEach(function (column) {
            headRow.appendChild(
                createElement(
                    "th",
                    column.numeric ? "data-table__num" : null,
                    column.label
                )
            );
        });

        thead.appendChild(headRow);
        table.appendChild(thead);

        const tbody = createElement("tbody");

        products.forEach(function (product) {

            const row = createElement("tr");

            row.appendChild(createElement("td", null, product.sku || "—"));

            row.appendChild(
                createElement("td", "data-table__muted", product.style || "—")
            );

            const categoryCell = createElement("td");

            categoryCell.appendChild(
                createElement(
                    "span",
                    "data-table__tag",
                    product.category || "—"
                )
            );

            row.appendChild(categoryCell);

            row.appendChild(
                createElement(
                    "td",
                    "data-table__num",
                    formatNumber(product.quantity)
                )
            );

            row.appendChild(
                createElement(
                    "td",
                    "data-table__num",
                    formatCurrency(product.revenue)
                )
            );

            tbody.appendChild(row);
        });

        table.appendChild(tbody);
        wrap.appendChild(table);
        container.appendChild(wrap);
    }


    // =====================================================
    // ANALYTICS RENDERING
    // =====================================================

    function setMeta(key, text) {

        const node = elements.metas[key];

        if (node) {
            node.textContent = text || "";
        }
    }


    /**
     * Metric-card sparklines are driven by the daily trend
     * series. Only metrics the backend actually reports a
     * series for get a sparkline — nothing is synthesised.
     */
    function renderSparklines(rows) {

        const series = {
            revenue: [],
            orders: [],
            quantity: []
        };

        if (!Array.isArray(rows) || rows.length < 2) {

            Object.keys(elements.sparks).forEach(function (key) {
                clearNode(elements.sparks[key]);
            });

            return;
        }

        rows.forEach(function (row) {
            series.revenue.push(toFiniteNumber(row.revenue) || 0);
            series.orders.push(toFiniteNumber(row.orders) || 0);
            series.quantity.push(toFiniteNumber(row.quantity) || 0);
        });

        const caption = "Daily · " + formatShortDate(rows[0].date) +
            " – " + formatShortDate(rows[rows.length - 1].date);

        Object.keys(series).forEach(function (key) {

            if (elements.sparks[key]) {
                renderSparkline(elements.sparks[key], series[key]);
            }

            if (elements.sparkCaptions[key]) {
                elements.sparkCaptions[key].textContent = caption;
            }
        });

        if (elements.railPeriod) {
            elements.railPeriod.textContent = rows.length + " days";
        }
    }


    function renderTrend(rows) {

        const container = elements.charts.trend;

        renderSparklines(rows);

        if (!container) {
            return;
        }

        if (!Array.isArray(rows) || !rows.length) {
            renderChartMessage(container, "No trend data available.");
            setMeta("trend", "");
            return;
        }

        renderLineChart(container, rows);
        setMeta("trend", rows.length + " days");
    }


    function renderCategories(rows) {

        const container = elements.charts.categories;

        if (!container) {
            return;
        }

        if (!Array.isArray(rows) || !rows.length) {
            renderChartMessage(container, "No category data available.");
            return;
        }

        const top = rows.slice(0, CONFIG.topCategories);

        renderColumnChart(container, top.map(function (row) {
            return {
                label: titleCase(row.category),
                value: toFiniteNumber(row.revenue) || 0,
                display: formatCurrencyCompact(row.revenue)
            };
        }));
    }


    function renderStates(rows) {

        const container = elements.charts.states;

        if (!container) {
            return;
        }

        if (!Array.isArray(rows) || !rows.length) {
            renderChartMessage(container, "No geographic data available.");
            return;
        }

        const top = rows.slice(0, CONFIG.topStates);

        renderBarChart(container, top.map(function (row) {
            return {
                label: titleCase(row.state),
                value: toFiniteNumber(row.revenue) || 0,
                display: formatCurrencyCompact(row.revenue)
            };
        }));

        setMeta("states", rows.length + " states");
    }


    function renderStatus(rows) {

        const container = elements.charts.status;

        if (!container) {
            return;
        }

        if (!Array.isArray(rows) || !rows.length) {
            renderChartMessage(container, "No status data available.");
            return;
        }

        const top = rows.slice(0, CONFIG.topStatuses);

        renderBarChart(container, top.map(function (row) {

            const isCancelled = String(row.status || "")
                .toLowerCase() === "cancelled";

            return {
                label: row.status || "Unknown",
                value: toFiniteNumber(row.orders) || 0,
                display: formatNumber(row.orders),
                variant: isCancelled ? "danger" : null
            };
        }));

        setMeta("status", rows.length + " statuses");
    }


    function renderFulfilment(rows) {

        const container = elements.charts.fulfilment;

        if (!container) {
            return;
        }

        if (!Array.isArray(rows) || !rows.length) {
            renderChartMessage(container, "No fulfilment data available.");
            return;
        }

        renderPieChart(container, rows.map(function (row) {
            return {
                label: row.fulfilment || "Unknown",
                value: toFiniteNumber(row.revenue) || 0
            };
        }));
    }


    function renderChannels(rows) {

        const container = elements.charts.channels;

        if (!container) {
            return;
        }

        if (!Array.isArray(rows) || !rows.length) {
            renderChartMessage(container, "No channel data available.");
            return;
        }

        renderPieChart(container, rows.map(function (row) {
            return {
                label: row.channel || "Unknown",
                value: toFiniteNumber(row.revenue) || 0
            };
        }));
    }


    function renderProducts(rows) {

        const container = elements.charts.products;

        if (!container) {
            return;
        }

        if (!Array.isArray(rows) || !rows.length) {
            renderChartMessage(container, "No product data available.");
            return;
        }

        renderProductsTable(container, rows);
        setMeta("products", "Top " + rows.length);
    }


    function renderAnalytics(analytics) {

        renderTrend(analytics.trend);
        renderCategories(analytics.categories);
        renderStates(analytics.states);
        renderStatus(analytics.status);
        renderFulfilment(analytics.fulfilment);
        renderChannels(analytics.channels);
        renderProducts(analytics.products);
    }


    function showChartsMessage(message) {

        Object.keys(elements.charts).forEach(function (key) {
            renderChartMessage(elements.charts[key], message);
            setMeta(key, "");
        });
    }


    // =====================================================
    // STATE RENDERING
    // =====================================================

    function setBusy(busy) {

        [elements.statStrip, elements.metricList].forEach(function (node) {

            if (node) {
                node.setAttribute("aria-busy", busy ? "true" : "false");
            }
        });
    }


    function showLoadingState() {

        setBusy(true);

        setHidden(elements.workspace, false);
        setHidden(elements.errorState, true);
        setHidden(elements.emptyState, true);

        showChartsMessage("Loading…");

        if (elements.refreshButton) {
            elements.refreshButton.disabled = true;
        }
    }


    function clearLoadingState() {

        setBusy(false);

        if (elements.refreshButton) {
            elements.refreshButton.disabled = false;
        }
    }


    function showErrorState(message) {

        clearLoadingState();

        if (elements.errorMessage) {
            elements.errorMessage.textContent = message;
        }

        setHidden(elements.errorState, false);
        setHidden(elements.emptyState, true);

        // Keep the page structure intact but never show
        // stale or fabricated values alongside an error.
        setHidden(elements.workspace, true);

        resetValues();
    }


    function showEmptyState() {

        clearLoadingState();

        setHidden(elements.emptyState, false);
        setHidden(elements.errorState, true);
        setHidden(elements.workspace, true);
    }


    function showDataState() {

        clearLoadingState();

        setHidden(elements.errorState, true);
        setHidden(elements.emptyState, true);
        setHidden(elements.workspace, false);
    }


    function resetValues() {

        elements.valueNodes.forEach(function (node) {
            node.textContent = "—";
        });
    }


    // =====================================================
    // SUMMARY RENDERING
    // =====================================================

    /**
     * A successful response with no underlying records is
     * an empty state, not an error. Zero is a valid value.
     */
    function isEmptySummary(summary) {

        const presence = toFiniteNumber(summary[CONFIG.presenceKey]);

        return presence === null || presence === 0;
    }


    function renderSummary(summary) {

        elements.valueNodes.forEach(function (node) {

            const key = node.getAttribute("data-kpi");
            const format = node.getAttribute("data-format");

            const raw = Object.prototype.hasOwnProperty.call(summary, key)
                ? summary[key]
                : null;

            node.textContent = formatValue(raw, format);
        });

        if (elements.datasetLabel) {
            elements.datasetLabel.textContent =
                formatNumber(summary.total_rows) + " records";
        }

        if (elements.lastUpdated) {
            elements.lastUpdated.textContent = formatTimestamp(
                dashboardState.lastUpdated
            );
        }
    }


    // =====================================================
    // DATA LOADING
    // =====================================================

    async function requestJson(url) {

        const response = await fetch(url, {
            headers: { "Accept": "application/json" }
        });

        let payload = null;

        try {
            payload = await response.json();
        } catch (parseError) {
            throw new Error(
                "The server returned a response that could not " +
                "be read as JSON."
            );
        }

        if (!response.ok) {
            throw new Error(
                (payload && payload.error) ||
                ("Request failed with status " + response.status + ".")
            );
        }

        return payload;
    }


    async function loadSummary() {

        const payload = await requestJson(CONFIG.endpoints.summary);

        if (!payload || payload.success !== true) {
            throw new Error(
                (payload && payload.error) ||
                "The dashboard API reported an unsuccessful response."
            );
        }

        if (!payload.data || typeof payload.data !== "object") {
            throw new Error(
                "The dashboard API response did not include any data."
            );
        }

        return payload.data;
    }


    /**
     * Analytics panels are secondary: a failure there must
     * not take down the KPI dashboard, so each request
     * resolves to null instead of rejecting.
     */
    async function loadAnalytics() {

        const keys = [
            "trend",
            "categories",
            "states",
            "status",
            "fulfilment",
            "channels",
            "products"
        ];

        const results = await Promise.all(keys.map(function (key) {

            return requestJson(CONFIG.endpoints[key])
                .catch(function (error) {
                    console.error("[dashboard] " + key + " failed:", error);
                    return null;
                });
        }));

        const analytics = {};

        keys.forEach(function (key, index) {
            analytics[key] = results[index];
        });

        return analytics;
    }


    async function loadDashboard() {

        if (dashboardState.loading) {
            return;
        }

        dashboardState.loading = true;
        dashboardState.error = null;

        showLoadingState();

        try {

            const summary = await loadSummary();

            dashboardState.summary = summary;
            dashboardState.lastUpdated = new Date();

            if (isEmptySummary(summary)) {
                showEmptyState();
                return;
            }

            renderSummary(summary);
            showDataState();

            const analytics = await loadAnalytics();

            dashboardState.analytics = analytics;

            renderAnalytics(analytics);

        } catch (error) {

            dashboardState.summary = null;
            dashboardState.error = error.message || String(error);

            showErrorState(dashboardState.error);

            console.error("[dashboard] load failed:", error);

        } finally {

            dashboardState.loading = false;
        }
    }


    // =====================================================
    // THEME
    // =====================================================

    function applyTheme(theme) {

        dashboardState.theme = theme;

        document.documentElement.setAttribute("data-theme", theme);

        const isDark = theme === "dark";

        if (elements.themeIcon) {
            elements.themeIcon.textContent = isDark ? "☀" : "🌙";
        }

        if (elements.themeToggle) {

            elements.themeToggle.setAttribute(
                "aria-pressed",
                isDark ? "true" : "false"
            );

            elements.themeToggle.setAttribute(
                "aria-label",
                isDark ? "Switch to light mode" : "Switch to dark mode"
            );
        }
    }


    function initTheme() {

        let stored = null;

        try {
            stored = window.localStorage.getItem(CONFIG.themeStorageKey);
        } catch (storageError) {
            stored = null;
        }

        if (stored !== "dark" && stored !== "light") {

            const prefersDark = window.matchMedia &&
                window.matchMedia("(prefers-color-scheme: dark)").matches;

            stored = prefersDark ? "dark" : "light";
        }

        applyTheme(stored);
    }


    function toggleTheme() {

        const next = dashboardState.theme === "dark" ? "light" : "dark";

        applyTheme(next);

        try {
            window.localStorage.setItem(CONFIG.themeStorageKey, next);
        } catch (storageError) {
            // Storage is optional; the theme still applies.
        }
    }


    // =====================================================
    // EVENT BINDING
    // =====================================================

    function bindEvents() {

        if (elements.refreshButton) {
            elements.refreshButton.addEventListener("click", function (event) {
                event.preventDefault();
                loadDashboard();
            });
        }

        if (elements.retryButton) {
            elements.retryButton.addEventListener("click", function (event) {
                event.preventDefault();
                loadDashboard();
            });
        }

        if (elements.themeToggle) {
            elements.themeToggle.addEventListener("click", toggleTheme);
        }

    }


    // =====================================================
    // INITIALISATION
    // =====================================================

    function init() {

        cacheElements();
        initTheme();
        bindEvents();
        loadDashboard();
    }


    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }

}());
