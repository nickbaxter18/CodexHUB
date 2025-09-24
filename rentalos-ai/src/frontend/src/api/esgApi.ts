import httpClient from './httpClient'

export const compileEsgReport = async (assetId: number) => {
  try {
    const { data } = await httpClient.post('/esg/report', { asset_id: assetId })
    return data
  } catch (error) {
    return Promise.resolve({ asset_id: assetId, score: 0 })
  }
}
