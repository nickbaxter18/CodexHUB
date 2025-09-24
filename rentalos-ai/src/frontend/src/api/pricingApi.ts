import httpClient from './httpClient'

export const fetchPricingSuggestion = async (assetId: number) => {
  try {
    const { data } = await httpClient.post('/pricing/suggestions', {
      asset_id: assetId,
      duration: 7,
    })
    return data
  } catch (error) {
    return Promise.resolve({ asset_id: assetId, suggested_price: 120 })
  }
}
