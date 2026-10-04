export const PROBLEM_TYPES: Record<string, string[]> = {
  'Number System': [' divisibility', 'remainder', 'number series', 'digital root'],
  'HCF and LCM': ['hcf-lcm', 'product-of-numbers'],
  Percentage: ['percentage-change', 'successive-percentage', 'percentage-point'],
  'Profit and Loss': ['profit-percent', 'loss-percent', 'discount', 'marked-price'],
  'Ratio and Proportion': ['ratio', 'proportion', 'division', 'mixture'],
  Average: ['simple-average', 'weighted-average', 'numbers-removed'],
  'Problems on Ages': ['present-age', 'age-ratio', 'age-difference'],
  'Simple Interest': ['si-basic', 'si-difference', 'si-installments'],
  'Compound Interest': ['ci-basic', 'ci-vs-si', 'ci-installments'],
  'Time and Work': ['work-efficiency', 'pipes-cisterns', 'work-wages'],
  'Pipes and Cisterns': ['pipes-open', 'cistern-leak', 'pipes-alternate'],
  'Time, Speed and Distance': ['relative-speed', 'average-speed', 'trains', 'boats-streams'],
  'Problems on Trains': ['train-platform', 'train-train', 'train-man'],
  'Mixtures and Allegations': ['mixture-ratio', 'alligation', 'replacement'],
  Probability: ['simple-probability', 'coin-dice', 'cards', 'conditional'],
  'Permutation and Combination': ['permutation', 'combination', 'arrangement', 'selection'],
  'Data Interpretation': ['table', 'graph', 'pie-chart', 'bar-chart'],
}

export type ProblemTypeKey = keyof typeof PROBLEM_TYPES
export type ProblemType = (typeof PROBLEM_TYPES)[ProblemTypeKey][number]
