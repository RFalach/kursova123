<script>
  import Map from './components/Map.svelte'
  import Chart from './components/Chart.svelte'
  import { getSensors } from './lib/api.js'

  let sensors = $state([])
  let selectedSensor = $state(null)
  let selectedParameter = $state('pm25')
  let selectedPeriod = $state('day')   // 'day', 'week', 'month', 'custom'

  let customFrom = $state('')
  let customTo = $state('')

  $effect(() => {
    getSensors().then(data => sensors = data)
  })

  function handleSensorSelect(sensor) {
    selectedSensor = sensor
  }

  function getDateRange(period, fromStr, toStr) {
    if (period === 'custom') {
      if (!fromStr || !toStr) return null
      const from = new Date(fromStr + 'T00:00:00')
      const to = new Date(toStr + 'T23:59:59')
      return {
        from: from.toISOString(),
        to: to.toISOString()
      }
    }

    const now = new Date()
    let from = new Date()
    if (period === 'day') from.setDate(now.getDate() - 1)
    else if (period === 'week') from.setDate(now.getDate() - 7)
    else if (period === 'month') from.setMonth(now.getMonth() - 1)
    return {
      from: from.toISOString(),
      to: now.toISOString()
    }
  }

  let dateRange = $derived(getDateRange(selectedPeriod, customFrom, customTo))

  function onCustomDateChange() {
    selectedPeriod = 'custom'
  }
</script>

<div class="app">
  <header>
    <h1>Моніторинг якості повітря</h1>
  </header>

  <main>
    <div class="map-panel">
      <Map sensors={sensors} onSelectSensor={handleSensorSelect} />
    </div>

    <div class="chart-panel">
      {#if selectedSensor}
        <div class="chart-header">
          <h2>{selectedSensor.name}</h2>
          <div class="controls">
            <select bind:value={selectedParameter}>
              <option value="pm25">PM2.5</option>
              <option value="pm10">PM10</option>
              <option value="no2">NO₂</option>
              <option value="co">CO</option>
            </select>

            <div class="period-tabs">
              {#each ['day', 'week', 'month'] as period}
                <button
                  class:active={selectedPeriod === period}
                  onclick={() => selectedPeriod = period}
                >
                  {period === 'day' ? 'День' : period === 'week' ? 'Тиждень' : 'Місяць'}
                </button>
              {/each}
            </div>

            <div class="custom-range">
              <label>
                з
                <input
                  type="date"
                  bind:value={customFrom}
                  oninput={onCustomDateChange}
                />
              </label>
              <label>
                по
                <input
                  type="date"
                  bind:value={customTo}
                  oninput={onCustomDateChange}
                />
              </label>
            </div>
          </div>
        </div>

        {#if dateRange}
          <Chart
            sensorId={selectedSensor.sensor_id}
            parameter={selectedParameter}
            fromDate={dateRange.from}
            toDate={dateRange.to}
          />
        {:else}
          <div class="placeholder">Вкажіть коректний діапазон дат</div>
        {/if}
      {:else}
        <div class="placeholder">
          <p>Оберіть сенсор на карті, щоб переглянути дані</p>
        </div>
      {/if}
    </div>
  </main>
</div>

<style>
  :global(body) {
    margin: 0;
    font-family: 'Segoe UI', Roboto, sans-serif;
    background-color: #0f172a;
    color: #e2e8f0;
  }

  .app {
    display: flex;
    flex-direction: column;
    height: 100vh;
  }

  header {
    padding: 1rem 2rem;
    background: linear-gradient(135deg, #1e293b, #0f172a);
    border-bottom: 1px solid #334155;
    display: flex;
    align-items: baseline;
    gap: 1rem;
  }

  header h1 {
    margin: 0;
    font-size: 1.5rem;
    font-weight: 600;
    color: #38bdf8;
  }

  .subtitle {
    color: #94a3b8;
    font-size: 0.9rem;
  }

  main {
    display: flex;
    flex: 1;
    gap: 1rem;
    padding: 1rem;
    overflow: hidden;
  }

  .map-panel {
    flex: 1;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 4px 20px rgba(0,0,0,0.5);
  }

  .chart-panel {
    flex: 1;
    background: #1e293b;
    border-radius: 12px;
    padding: 1rem;
    display: flex;
    flex-direction: column;
    box-shadow: 0 4px 20px rgba(0,0,0,0.5);
  }

  .chart-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    margin-bottom: 1rem;
  }

  .chart-header h2 {
    margin: 0;
    font-size: 1.2rem;
    color: #f1f5f9;
    min-width: 150px;
  }

  .controls {
    display: flex;
    gap: 1rem;
    align-items: center;
    flex-wrap: wrap;
  }

  select {
    background: #334155;
    color: #e2e8f0;
    border: 1px solid #475569;
    padding: 0.3rem 0.6rem;
    border-radius: 6px;
    font-size: 0.9rem;
    cursor: pointer;
  }

  .period-tabs {
    display: flex;
    gap: 0.3rem;
  }

  .period-tabs button {
    background: #334155;
    border: none;
    color: #cbd5e1;
    padding: 0.3rem 0.8rem;
    border-radius: 6px;
    font-size: 0.85rem;
    cursor: pointer;
    transition: all 0.2s;
  }

  .period-tabs button.active {
    background: #38bdf8;
    color: #0f172a;
    font-weight: 600;
  }

  .custom-range {
    display: flex;
    gap: 0.5rem;
    align-items: center;
  }

  .custom-range label {
    display: flex;
    align-items: center;
    gap: 0.3rem;
    color: #cbd5e1;
    font-size: 0.85rem;
  }

  .custom-range input[type="date"] {
    background: #334155;
    color: #e2e8f0;
    border: 1px solid #475569;
    padding: 0.2rem 0.4rem;
    border-radius: 6px;
    font-size: 0.85rem;
    outline: none;
  }

  .placeholder {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #64748b;
    font-size: 1.1rem;
  }
</style>