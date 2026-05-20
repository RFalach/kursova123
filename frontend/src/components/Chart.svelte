<script>
  import { onDestroy } from 'svelte'
  import Chart from 'chart.js/auto'
  import 'chartjs-adapter-date-fns'
  import { getMeasurements } from '../lib/api.js'

  let { sensorId, parameter, fromDate, toDate } = $props()

  let canvas
  let chart = null

  $effect(() => {
    if (sensorId && parameter && fromDate && toDate) {
      loadData()
    }
  })

  async function loadData() {
    try {
      const raw = await getMeasurements(sensorId, parameter, fromDate, toDate, 500)
      const points = raw
        .map(d => ({
          x: new Date(d.timestamp),
          y: d[parameter],
          anomaly: d.anomaly
        }))
        .sort((a, b) => a.x - b.x)

      const allValues = points.map(p => p.y)
      const minVal = Math.min(...allValues, 0)
      const maxVal = Math.max(...allValues, 1)
      const padding = (maxVal - minVal) * 0.1 || 1

      if (!chart) {
        chart = new Chart(canvas, {
          type: 'line',
          data: {
            datasets: [{
              label: parameter.toUpperCase(),
              data: points,
              borderColor: '#38bdf8',
              backgroundColor: '#38bdf8',
              tension: 0.2,
              pointBackgroundColor: points.map(p => p.anomaly ? '#f87171' : '#38bdf8'),
              pointBorderColor: points.map(p => p.anomaly ? '#b91c1c' : '#0284c7'),
              pointRadius: points.map(p => p.anomaly ? 6 : 3),
              pointHoverRadius: points.map(p => p.anomaly ? 8 : 5)
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
              x: {
                type: 'time',
                time: { unit: 'hour' },
                ticks: { color: '#94a3b8' },
                grid: { color: '#334155' }
              },
              y: {
                min: minVal - padding,
                max: maxVal + padding,
                ticks: { color: '#94a3b8' },
                grid: { color: '#334155' }
              }
            },
            plugins: {
              legend: { labels: { color: '#e2e8f0' } }
            }
          }
        })
      } else {
        chart.data.datasets[0].data = points
        chart.data.datasets[0].pointBackgroundColor = points.map(p => p.anomaly ? '#f87171' : '#38bdf8')
        chart.data.datasets[0].pointBorderColor = points.map(p => p.anomaly ? '#b91c1c' : '#0284c7')
        chart.data.datasets[0].pointRadius = points.map(p => p.anomaly ? 6 : 3)
        chart.options.scales.y.min = minVal - padding
        chart.options.scales.y.max = maxVal + padding
        chart.update()
      }
    } catch (e) {
      console.error('Chart error:', e)
    }
  }

  onDestroy(() => {
    if (chart) chart.destroy()
  })
</script>

<div class="chart-container">
  <canvas bind:this={canvas}></canvas>
</div>

<style>
  .chart-container {
    flex: 1;
    min-height: 0;
  }
</style>