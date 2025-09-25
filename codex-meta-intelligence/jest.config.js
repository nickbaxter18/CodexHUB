/** @type {import('jest').Config} */
export default {
  testEnvironment: 'node',
  transform: {
    '^.+\\.ts$': '<rootDir>/jest.transform.cjs',
  },
  testMatch: ['**/?(*.)+(spec|test).ts'],
  moduleNameMapper: {
    '^(.*)\\.js$': '$1',
  },
  roots: ['<rootDir>/tests'],
  moduleFileExtensions: ['ts', 'js'],
  collectCoverageFrom: ['src/**/*.ts'],
  coverageDirectory: 'coverage',
  clearMocks: true,
};
