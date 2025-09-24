import httpClient from './httpClient'

export const evaluateApplicant = async (payload: Record<string, unknown>) => {
  try {
    const { data } = await httpClient.post('/screening/evaluate', payload)
    return data
  } catch (error) {
    return Promise.resolve({
      applicant: payload['name'] ?? 'Unknown',
      score: 0,
    })
  }
}
