import httpClient from './httpClient'

export const abstractLease = async (document: string) => {
  try {
    const { data } = await httpClient.post('/leases/abstract', { document })
    return data
  } catch (error) {
    return Promise.resolve({
      tenant: 'Unknown',
      term_months: 0,
      monthly_rent: 0,
    })
  }
}
