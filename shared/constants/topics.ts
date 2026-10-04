export const TOPICS = [
  'Number System',
  'HCF and LCM',
  'Percentage',
  'Profit and Loss',
  'Ratio and Proportion',
  'Average',
  'Problems on Ages',
  'Simple Interest',
  'Compound Interest',
  'Time and Work',
  'Pipes and Cisterns',
  'Time, Speed and Distance',
  'Problems on Trains',
  'Mixtures and Allegations',
  'Probability',
  'Permutation and Combination',
  'Data Interpretation',
] as const

export type Topic = (typeof TOPICS)[number]
