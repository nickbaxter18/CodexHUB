import httpClient from './httpClient'

export const listPlugins = async () => {
  const { data } = await httpClient.get('/plugins')
  return data
}
