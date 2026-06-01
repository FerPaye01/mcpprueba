export interface IDataset {
  title: string;
  description: string;
  format: string;
  license: string;
  organization: string;
}

export interface IFilterState {
  geography: string;
  energyMatrix: Record<string, boolean>;
}
