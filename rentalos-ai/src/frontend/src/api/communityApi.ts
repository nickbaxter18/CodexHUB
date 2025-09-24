import httpClient from './httpClient'

export const createEvent = async (payload: Record<string, unknown>) => {
  try {
    const { data } = await httpClient.post('/community/events', payload)
    return data
  } catch (error) {
    return Promise.resolve({
      title: payload['title'],
      asset_id: payload['asset_id'],
    })
  }
}
