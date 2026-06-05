export interface IDataset {
  title: string;
  description: string;
  format: string;
  license: string;
  organization: string;
  schema?: string;
  id_catalogo?: number;
}

export interface IFilterState {
  geography: string;
  energyMatrix: Record<string, boolean>;
}
