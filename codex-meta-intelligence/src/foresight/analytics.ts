export const movingAverage = (values: number[], window = values.length): number => {
  if (values.length === 0 || window <= 0) return 0;
  const slice = values.slice(-window);
  return slice.reduce((acc, value) => acc + value, 0) / slice.length;
};

export const weightedScore = (values: number[], weights: number[]): number => {
  if (values.length !== weights.length || values.length === 0) {
    return 0;
  }
  const totalWeight = weights.reduce((acc, value) => acc + value, 0);
  if (totalWeight === 0) return 0;
  let score = 0;
  for (let i = 0; i < values.length; i += 1) {
    const value = values[i]!;
    const weight = weights[i]!;
    score += value * weight;
  }
  return score / totalWeight;
};
