import httpClient from './httpClient'

export const fetchAgenda = async () => {
  try {
    const { data } = await httpClient.get('/scheduling/agenda')
    return data
  } catch (error) {
    return Promise.resolve([])
  }
}
