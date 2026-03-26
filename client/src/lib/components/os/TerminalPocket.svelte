<!-- TerminalPocket.svelte — Bloomberg Terminal-style chart-heavy pocket.
     Created: 2026-03-25 — Dark mode data dashboard with ECharts, iOS-style charts,
     neon accents, KPI strip, status badges, and dense widget grid.
     Inspired by Apple HIG Charts + Bloomberg Terminal aesthetics.
-->
<script lang="ts">
  import EChart from "./EChart.svelte";
  import TrendingUp from "@lucide/svelte/icons/trending-up";
  import DollarSign from "@lucide/svelte/icons/dollar-sign";
  import Users from "@lucide/svelte/icons/users";
  import ShoppingCart from "@lucide/svelte/icons/shopping-cart";
  import BarChart3 from "@lucide/svelte/icons/bar-chart-3";
  import Activity from "@lucide/svelte/icons/activity";
  import ArrowUp from "@lucide/svelte/icons/arrow-up";
  import ArrowDown from "@lucide/svelte/icons/arrow-down";
  import type { EChartsOption } from "echarts";

  // === KPI DATA ===
  const kpis = [
    { label: "Revenue MTD", value: "$142,800", change: "+18%", up: true, icon: DollarSign, color: "#30D158" },
    { label: "Events", value: "24", change: "+6", up: true, icon: BarChart3, color: "#0A84FF" },
    { label: "Occupancy", value: "78%", change: "+12%", up: true, icon: Activity, color: "#BF5AF2" },
    { label: "Members", value: "186", change: "+8", up: true, icon: Users, color: "#5E5CE6" },
    { label: "F&B Rev", value: "$38,400", change: "-3%", up: false, icon: ShoppingCart, color: "#FF9F0A" },
  ];

  // === CHART OPTIONS ===

  // 1. Revenue trend — smooth area with bold fill
  const revenueChart: EChartsOption = {
    grid: { left: 0, right: 0, top: 10, bottom: 20, containLabel: false },
    xAxis: {
      show: true, type: "category",
      data: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
      axisLine: { show: false }, axisTick: { show: false },
      axisLabel: { color: "rgba(255,255,255,0.25)", fontSize: 9 },
    },
    series: [{
      type: "line", smooth: 0.5, showSymbol: false,
      lineStyle: { width: 2.5, color: "#30D158" },
      areaStyle: {
        color: {
          type: "linear", x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: "rgba(48,209,88,0.45)" },
            { offset: 1, color: "rgba(48,209,88,0.02)" },
          ],
        },
      },
      data: [82, 95, 88, 112, 105, 128, 118, 135, 142, 138, 155, 142],
    }],
  };

  // 2. Occupancy by day — rounded bars with gradient
  const occupancyChart: EChartsOption = {
    grid: { left: 0, right: 0, top: 4, bottom: 20, containLabel: false },
    xAxis: {
      show: true, type: "category",
      data: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
      axisLine: { show: false }, axisTick: { show: false },
      axisLabel: { color: "rgba(255,255,255,0.25)", fontSize: 9 },
    },
    series: [{
      type: "bar",
      barWidth: "55%",
      itemStyle: {
        borderRadius: [4, 4, 0, 0],
        color: (params: any) => {
          const val = params.data as number;
          if (val >= 95) return "#FF453A";
          if (val >= 70) return "#BF5AF2";
          return "rgba(191,90,242,0.35)";
        },
      },
      data: [45, 60, 55, 92, 100, 100, 40],
    }],
  };

  // 3. F&B breakdown — donut
  const fbChart: EChartsOption = {
    series: [{
      type: "pie", radius: ["55%", "80%"],
      center: ["50%", "50%"],
      label: { show: false },
      itemStyle: { borderRadius: 4, borderColor: "#1e1e1c", borderWidth: 2 },
      data: [
        { value: 42, name: "Bar", itemStyle: { color: "#FF9F0A" } },
        { value: 28, name: "Food", itemStyle: { color: "#FF6B35" } },
        { value: 18, name: "Packages", itemStyle: { color: "#FEBC2E" } },
        { value: 12, name: "Bottles", itemStyle: { color: "#BF5AF2" } },
      ],
    }],
  };

  // 4. Member growth — stacked area
  const memberChart: EChartsOption = {
    grid: { left: 0, right: 0, top: 4, bottom: 20, containLabel: false },
    xAxis: {
      show: true, type: "category",
      data: ["Oct", "Nov", "Dec", "Jan", "Feb", "Mar"],
      axisLine: { show: false }, axisTick: { show: false },
      axisLabel: { color: "rgba(255,255,255,0.25)", fontSize: 9 },
    },
    series: [
      {
        name: "Active", type: "line", smooth: 0.5, showSymbol: false, stack: "total",
        lineStyle: { width: 0 },
        areaStyle: { color: "rgba(94,92,230,0.6)" },
        data: [140, 148, 155, 162, 174, 186],
      },
      {
        name: "Waitlist", type: "line", smooth: 0.5, showSymbol: false, stack: "total",
        lineStyle: { width: 0 },
        areaStyle: { color: "rgba(94,92,230,0.2)" },
        data: [680, 710, 740, 780, 820, 847],
      },
    ],
  };

  // 5. Event revenue by type — horizontal bars
  const eventTypeChart: EChartsOption = {
    grid: { left: 80, right: 10, top: 4, bottom: 4, containLabel: false },
    yAxis: {
      show: true, type: "category",
      data: ["Buyouts", "Dinners", "Mixers", "Launches", "Summits"],
      axisLine: { show: false }, axisTick: { show: false },
      axisLabel: { color: "rgba(255,255,255,0.45)", fontSize: 10 },
    },
    xAxis: { show: false, type: "value" },
    series: [{
      type: "bar",
      barWidth: "50%",
      itemStyle: { borderRadius: [0, 3, 3, 0], color: "#0A84FF" },
      data: [18, 14.5, 12, 22.5, 28],
      label: {
        show: true, position: "right",
        formatter: "${c}K",
        color: "rgba(255,255,255,0.50)", fontSize: 10,
      },
    }],
  };

  // 6. Revenue heatmap — week × hour
  const heatmapData: number[][] = [];
  const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
  const hours = ["10am", "12pm", "2pm", "4pm", "6pm", "8pm", "10pm"];
  for (let d = 0; d < 7; d++) {
    for (let h = 0; h < 7; h++) {
      // Higher on evenings and weekends
      const base = (h > 3 ? 60 : 20) + (d > 3 ? 30 : 0);
      heatmapData.push([h, d, Math.floor(base + Math.random() * 40)]);
    }
  }

  const heatmapChart: EChartsOption = {
    grid: { left: 36, right: 4, top: 4, bottom: 24, containLabel: false },
    xAxis: {
      show: true, type: "category", data: hours,
      axisLine: { show: false }, axisTick: { show: false },
      axisLabel: { color: "rgba(255,255,255,0.25)", fontSize: 8 },
    },
    yAxis: {
      show: true, type: "category", data: days,
      axisLine: { show: false }, axisTick: { show: false },
      axisLabel: { color: "rgba(255,255,255,0.25)", fontSize: 8 },
    },
    visualMap: {
      show: false, min: 0, max: 120,
      inRange: {
        color: ["rgba(48,209,88,0.1)", "rgba(48,209,88,0.3)", "#30D158", "#FEBC2E", "#FF453A"],
      },
    },
    series: [{
      type: "heatmap",
      data: heatmapData,
      itemStyle: { borderRadius: 2, borderColor: "#1e1e1c", borderWidth: 1 },
    }],
  };

  // 7. Live activity — sparkline (mini line, no axes)
  const sparkData = Array.from({ length: 30 }, () => Math.floor(40 + Math.random() * 60));
  const sparkChart: EChartsOption = {
    grid: { left: 0, right: 0, top: 2, bottom: 2 },
    series: [{
      type: "line", smooth: 0.4, showSymbol: false,
      lineStyle: { width: 1.5, color: "#64D2FF" },
      areaStyle: {
        color: {
          type: "linear", x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: "rgba(100,210,255,0.25)" },
            { offset: 1, color: "rgba(100,210,255,0.0)" },
          ],
        },
      },
      data: sparkData,
    }],
  };

  // 8. Gauge — NPS score
  const gaugeChart: EChartsOption = {
    series: [{
      type: "gauge",
      startAngle: 200, endAngle: -20,
      min: 0, max: 100,
      radius: "90%",
      progress: { show: true, width: 10, itemStyle: { color: "#30D158" } },
      axisLine: { lineStyle: { width: 10, color: [[1, "rgba(255,255,255,0.06)"]] } },
      axisTick: { show: false },
      splitLine: { show: false },
      axisLabel: { show: false },
      pointer: { show: false },
      title: { show: false },
      detail: {
        fontSize: 22, fontWeight: "bold", color: "#30D158",
        offsetCenter: [0, "10%"],
        formatter: "{value}",
      },
      data: [{ value: 72 }],
    }],
  };
</script>

<div class="terminal-pocket">
  <!-- KPI Strip -->
  <div class="kpi-strip">
    {#each kpis as kpi}
      {@const Icon = kpi.icon}
      <div class="kpi-card">
        <div class="kpi-icon" style="color:{kpi.color}"><Icon size={14} strokeWidth={1.8} /></div>
        <div class="kpi-data">
          <span class="kpi-label">{kpi.label}</span>
          <div class="kpi-row">
            <span class="kpi-value">{kpi.value}</span>
            <span class="kpi-change" class:kpi-up={kpi.up} class:kpi-down={!kpi.up}>
              {#if kpi.up}<ArrowUp size={10} strokeWidth={2.5} />{:else}<ArrowDown size={10} strokeWidth={2.5} />{/if}
              {kpi.change}
            </span>
          </div>
        </div>
      </div>
    {/each}
  </div>

  <!-- Chart Grid -->
  <div class="chart-grid">
    <!-- Revenue Trend (wide) -->
    <div class="chart-widget chart-wide">
      <div class="chart-head">
        <span class="chart-title">Revenue Trend</span>
        <span class="chart-badge badge-green">GROWING</span>
      </div>
      <div class="chart-hero">$142,800 <span class="chart-hero-sub">MTD</span></div>
      <div class="chart-body"><EChart option={revenueChart} height="120px" /></div>
    </div>

    <!-- Occupancy -->
    <div class="chart-widget">
      <div class="chart-head">
        <span class="chart-title">Occupancy Rate</span>
        <span class="chart-badge badge-purple">78% AVG</span>
      </div>
      <div class="chart-body"><EChart option={occupancyChart} height="120px" /></div>
    </div>

    <!-- F&B Breakdown -->
    <div class="chart-widget">
      <div class="chart-head">
        <span class="chart-title">F&B Mix</span>
      </div>
      <div class="chart-hero">$38,400 <span class="chart-hero-sub">this month</span></div>
      <div class="chart-body"><EChart option={fbChart} height="110px" /></div>
    </div>

    <!-- Member Pipeline (wide) -->
    <div class="chart-widget chart-wide">
      <div class="chart-head">
        <span class="chart-title">Member Pipeline</span>
        <span class="chart-badge badge-blue">847 WAITLIST</span>
      </div>
      <div class="chart-hero">186 <span class="chart-hero-sub">active members</span></div>
      <div class="chart-body"><EChart option={memberChart} height="100px" /></div>
    </div>

    <!-- Event Revenue by Type -->
    <div class="chart-widget">
      <div class="chart-head">
        <span class="chart-title">Revenue by Event Type</span>
      </div>
      <div class="chart-body"><EChart option={eventTypeChart} height="140px" /></div>
    </div>

    <!-- Revenue Heatmap -->
    <div class="chart-widget">
      <div class="chart-head">
        <span class="chart-title">Revenue Heatmap</span>
        <span class="chart-badge badge-orange">PEAK: SAT 8PM</span>
      </div>
      <div class="chart-body"><EChart option={heatmapChart} height="140px" /></div>
    </div>

    <!-- NPS Gauge -->
    <div class="chart-widget chart-compact">
      <div class="chart-head">
        <span class="chart-title">NPS Score</span>
      </div>
      <div class="chart-body"><EChart option={gaugeChart} height="110px" /></div>
      <div class="chart-foot">Guest satisfaction</div>
    </div>

    <!-- Live Activity Spark -->
    <div class="chart-widget chart-compact">
      <div class="chart-head">
        <span class="chart-title">Live Activity</span>
        <span class="chart-live-dot"></span>
      </div>
      <div class="chart-hero">47 <span class="chart-hero-sub">active now</span></div>
      <div class="chart-body"><EChart option={sparkChart} height="50px" /></div>
    </div>

    <!-- Operational Status -->
    <div class="chart-widget chart-compact">
      <div class="chart-head">
        <span class="chart-title">Status</span>
        <span class="chart-badge badge-green">OPTIMAL</span>
      </div>
      <div class="status-rows">
        <div class="status-row"><span class="status-label">Staff</span><span class="status-val status-good">9/9 on shift</span></div>
        <div class="status-row"><span class="status-label">Inventory</span><span class="status-val status-warn">2 alerts</span></div>
        <div class="status-row"><span class="status-label">Events</span><span class="status-val status-good">3 confirmed</span></div>
        <div class="status-row"><span class="status-label">Payments</span><span class="status-val status-good">All clear</span></div>
        <div class="status-row"><span class="status-label">Reviews</span><span class="status-val status-good">4.7★ avg</span></div>
      </div>
    </div>
  </div>
</div>

<style>
  .terminal-pocket {
    width: 100%; height: 100%;
    display: flex; flex-direction: column;
    overflow-y: auto; padding: 8px;
    scrollbar-width: thin; scrollbar-color: rgba(255,255,255,0.06) transparent;
    gap: 6px;
  }

  /* KPI Strip */
  .kpi-strip {
    display: flex; gap: 6px; flex-shrink: 0;
    overflow-x: auto; scrollbar-width: none;
  }
  .kpi-strip::-webkit-scrollbar { display: none; }
  .kpi-card {
    display: flex; align-items: center; gap: 7px;
    padding: 6px 10px; border-radius: 8px;
    background: rgba(255,255,255,0.025);
    border: 1px solid rgba(255,255,255,0.05);
    flex: 1; min-width: 0;
  }
  .kpi-icon { display: flex; flex-shrink: 0; }
  .kpi-data { display: flex; flex-direction: column; gap: 0; min-width: 0; }
  .kpi-label { font-size: 9px; color: rgba(255,255,255,0.30); white-space: nowrap; }
  .kpi-row { display: flex; align-items: baseline; gap: 5px; }
  .kpi-value { font-size: 14px; font-weight: 700; color: rgba(255,255,255,0.90); white-space: nowrap; }
  .kpi-change { display: flex; align-items: center; gap: 1px; font-size: 9px; font-weight: 600; }
  .kpi-up { color: #30D158; }
  .kpi-down { color: #FF453A; }

  /* Chart Grid */
  .chart-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 6px; flex: 1;
  }
  .chart-wide { grid-column: span 2; }
  .chart-compact { grid-column: span 1; }

  /* Widget Card */
  .chart-widget {
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.04);
    border-radius: 10px; padding: 10px;
    display: flex; flex-direction: column;
    overflow: hidden;
  }
  .chart-head {
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 2px;
  }
  .chart-title {
    font-size: 10px; font-weight: 600; color: rgba(255,255,255,0.40);
    text-transform: uppercase; letter-spacing: 0.04em;
  }
  .chart-badge {
    font-size: 7px; font-weight: 700; letter-spacing: 0.06em;
    padding: 2px 5px; border-radius: 3px;
  }
  .badge-green { color: #30D158; background: rgba(48,209,88,0.12); }
  .badge-purple { color: #BF5AF2; background: rgba(191,90,242,0.12); }
  .badge-blue { color: #0A84FF; background: rgba(10,132,255,0.12); }
  .badge-orange { color: #FF9F0A; background: rgba(255,159,10,0.12); }
  .badge-red { color: #FF453A; background: rgba(255,69,58,0.12); }

  .chart-hero {
    font-size: 20px; font-weight: 700; color: rgba(255,255,255,0.92);
    margin: 1px 0 3px; line-height: 1;
  }
  .chart-hero-sub {
    font-size: 10px; font-weight: 400; color: rgba(255,255,255,0.28);
    margin-left: 3px;
  }
  .chart-body { flex: 1; min-height: 0; margin-top: 2px; }
  .chart-foot {
    font-size: 9px; color: rgba(255,255,255,0.20); text-align: center;
    margin-top: 2px;
  }

  .chart-live-dot {
    width: 6px; height: 6px; border-radius: 50%; background: #30D158;
    box-shadow: 0 0 6px rgba(48,209,88,0.6);
    animation: pulse 2s ease-in-out infinite;
  }
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
  }

  /* Status widget */
  .status-rows { display: flex; flex-direction: column; gap: 4px; margin-top: 2px; }
  .status-row { display: flex; justify-content: space-between; align-items: center; }
  .status-label { font-size: 10px; color: rgba(255,255,255,0.30); }
  .status-val { font-size: 10px; font-weight: 600; }
  .status-good { color: #30D158; }
  .status-warn { color: #FF9F0A; }
  .status-bad { color: #FF453A; }
</style>
