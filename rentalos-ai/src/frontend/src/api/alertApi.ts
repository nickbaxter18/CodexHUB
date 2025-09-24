import httpClient from './httpClient'

export const createAlert = async (payload: Record<string, unknown>) => {
  try {
    const { data } = await httpClient.post('/alerts', payload)
    return data
  } catch (error) {
    return Promise.resolve({
      channel: payload['channel'],
      message: payload['message'],
    })
  }
}
