const BASE_URL = 'http://localhost:8000'

export async function getSensors() {
  const res = await fetch(`${BASE_URL}/api/sensors`)
  if (!res.ok) throw new Error('Failed to fetch sensors')
  return await res.json()
}

export async function getMeasurements(sensorId, parameter, from, to, limit = 500) {
  const params = new URLSearchParams({
    sensor_id: sensorId,
    limit: limit.toString()
  })
  if (parameter) params.append('parameter', parameter)
  if (from) params.append('from_date', from)
  if (to) params.append('to_date', to)

  const res = await fetch(`${BASE_URL}/api/measurements?${params}`)
  if (!res.ok) throw new Error('Failed to fetch measurements')
  return await res.json()
}
