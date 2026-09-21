// Ambiente de desenvolvimento (padrão do `ng serve`).
// A URL base da API fica centralizada aqui — não hardcode `localhost` no código.
export const environment = {
  production: false,
  apiBaseUrl: 'http://localhost:8000/api/v1',
  apiOrigin: 'http://localhost:8000',
};