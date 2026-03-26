<!-- EChart.svelte — Reusable ECharts wrapper with iOS-style dark theme.
     Created: 2026-03-25 — PocketPaw Agent OS chart component with Apple HIG-inspired
     styling: no gridlines, organic curves, bold fills, rounded bars, neon accents.
-->
<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import * as echarts from "echarts";
  import type { EChartsOption } from "echarts";

  let {
    option,
    height = "100%",
    accentColor = "#0A84FF",
  }: {
    option: EChartsOption;
    height?: string;
    accentColor?: string;
  } = $props();

  let containerEl: HTMLDivElement;
  let chart: echarts.ECharts | null = null;

  // iOS-style theme defaults — merged under every chart
  const IOS_THEME: EChartsOption = {
    backgroundColor: "transparent",
    textStyle: {
      color: "rgba(255,255,255,0.50)",
      fontFamily: "Inter, -apple-system, system-ui, sans-serif",
      fontSize: 10,
    },
    grid: {
      left: 4, right: 4, top: 8, bottom: 4,
      containLabel: false,
    },
    xAxis: {
      show: false,
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: { show: false },
    },
    yAxis: {
      show: false,
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: { show: false },
    },
    tooltip: {
      trigger: "axis",
      backgroundColor: "rgba(30,30,28,0.92)",
      borderColor: "rgba(255,255,255,0.10)",
      borderWidth: 1,
      textStyle: { color: "#fff", fontSize: 11 },
      padding: [6, 10],
    },
    animation: true,
    animationDuration: 600,
    animationEasing: "cubicOut",
  };

  function mergeOptions(base: EChartsOption, user: EChartsOption): EChartsOption {
    return {
      ...base,
      ...user,
      textStyle: { ...base.textStyle, ...(user.textStyle || {}) },
      grid: { ...base.grid, ...(user.grid || {}) },
      tooltip: { ...base.tooltip, ...(user.tooltip || {}) },
    };
  }

  onMount(() => {
    chart = echarts.init(containerEl, undefined, { renderer: "canvas" });
    chart.setOption(mergeOptions(IOS_THEME, option));

    const observer = new ResizeObserver(() => chart?.resize());
    observer.observe(containerEl);

    return () => {
      observer.disconnect();
      chart?.dispose();
    };
  });

  // Reactively update when option changes
  $effect(() => {
    if (chart && option) {
      chart.setOption(mergeOptions(IOS_THEME, option), true);
    }
  });

  onDestroy(() => {
    chart?.dispose();
    chart = null;
  });
</script>

<div bind:this={containerEl} class="w-full" style="height:{height}"></div>
