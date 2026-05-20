<script>
  import { onMount, onDestroy } from 'svelte'
  import L from 'leaflet'
  import 'leaflet/dist/leaflet.css'

  let { sensors, onSelectSensor } = $props()

  let mapContainer
  let map
  let markersLayer

  onMount(() => {
    map = L.map(mapContainer, {
      center: [24, 15],
      zoom: 3,
      zoomControl: false,
      worldCopyJump: true
    })

    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      attribution: '© OpenStreetMap contributors, © CartoDB',
      subdomains: 'abcd',
      maxZoom: 19
    }).addTo(map)

    L.control.zoom({ position: 'bottomright' }).addTo(map)

    markersLayer = L.layerGroup().addTo(map)
    updateMarkers()
  })

  $effect(() => {
    if (map && sensors) updateMarkers()
  })

  function updateMarkers() {
    if (!markersLayer) return
    markersLayer.clearLayers()

    sensors.forEach(sensor => {
      const marker = L.circleMarker([sensor.latitude, sensor.longitude], {
        radius: 7,
        fillColor: '#38bdf8',
        color: '#0284c7',
        weight: 2,
        opacity: 1,
        fillOpacity: 0.8
      })
        .addTo(markersLayer)
        .bindPopup(`<b>${sensor.name}</b><br>${sensor.sensor_id}`)

      marker.on('click', () => onSelectSensor(sensor))
    })
  }

  onDestroy(() => {
    if (map) map.remove()
  })
</script>

<div bind:this={mapContainer} class="map"></div>

<style>
  .map {
    width: 100%;
    height: 100%;
  }
</style>