import httpClient from './httpClient'

export const fetchAuthStatus = async () => {
  const { data } = await httpClient.get('/auth/status')
  return data
}
