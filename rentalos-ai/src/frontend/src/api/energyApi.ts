import httpClient from './httpClient'

export const recordEnergyTrade = async (payload: Record<string, unknown>) => {
  try {
    const { data } = await httpClient.post('/energy/trade', payload)
    return data
  } catch (error) {
    return Promise.resolve({
      asset_id: payload['asset_id'],
      direction: payload['direction'],
    })
  }
}
