import httpClient from './httpClient'

export const fetchMaintenanceSchedule = async (assetId: number) => {
  try {
    const { data } = await httpClient.post('/maintenance/schedule', {
      asset_id: assetId,
    })
    return data
  } catch (error) {
    return Promise.resolve([])
  }
}
