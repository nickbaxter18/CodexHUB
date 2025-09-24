import httpClient from './httpClient'

export const buildPaymentPlan = async (payload: Record<string, unknown>) => {
  try {
    const { data } = await httpClient.post('/payments/plan', payload)
    return data
  } catch (error) {
    return Promise.resolve({ lease_id: payload['lease_id'], schedules: [] })
  }
}
