import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { FlatCompat } from '@eslint/eslintrc';
import js from '@eslint/js';
import tsParser from '@typescript-eslint/parser';
import securityPlugin from 'eslint-plugin-security';
import simpleImportSortPlugin from 'eslint-plugin-simple-import-sort';
import unusedImportsPlugin from 'eslint-plugin-unused-imports';
import unicornPlugin from 'eslint-plugin-unicorn';
import prettierPlugin from 'eslint-plugin-prettier';
import jsoncParser from 'jsonc-eslint-parser';
import yamlParser from 'yaml-eslint-parser';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const compat = new FlatCompat({
  baseDirectory: __dirname,
  recommendedConfig: js.configs.recommended,
  allConfig: js.configs.all,
  resolvePluginsRelativeTo: __dirname,
});

const ignores = [
  'node_modules/',
  'dist/',
  'build/',
  'coverage/',
  'tmp/',
  '**/node_modules/',
  'apps/editor/**',
  'backend/health-test/**',
  'bad.js',
  'editor/**',
  'test.js',
  'codexbridge/docs/**',
];

const extendedConfigs = [
  ...compat.extends(
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:import/recommended',
    'plugin:promise/recommended',
    'plugin:sonarjs/recommended-legacy',
    'plugin:jsdoc/recommended',
    'plugin:jsonc/recommended-with-jsonc',
    'plugin:yaml/legacy',
    'prettier'
  ),
];

const baseConfig = {
  files: ['**/*.{js,ts,tsx}', '**/*.mjs', '**/*.cjs'],
  languageOptions: {
    parser: tsParser,
    ecmaVersion: 'latest',
    sourceType: 'module',
    parserOptions: {
      project: ['./tsconfig.json'],
      tsconfigRootDir: __dirname,
    },
  },
  plugins: {
    security: securityPlugin,
    'simple-import-sort': simpleImportSortPlugin,
    'unused-imports': unusedImportsPlugin,
    prettier: prettierPlugin,
    unicorn: unicornPlugin,
  },
  rules: {
    'prettier/prettier': 'error',
    '@typescript-eslint/no-unused-vars': 'off',
    'unused-imports/no-unused-imports': 'error',
    'unused-imports/no-unused-vars': [
      'warn',
      {
        args: 'after-used',
        argsIgnorePattern: '^_',
        varsIgnorePattern: '^_',
        ignoreRestSiblings: true,
      },
    ],
    'simple-import-sort/imports': 'warn',
    'simple-import-sort/exports': 'warn',
    'consistent-return': 'error',
    'promise/always-return': 'warn',
    'promise/no-return-wrap': 'error',
    'security/detect-buffer-noassert': 'warn',
    'security/detect-child-process': 'warn',
    'security/detect-disable-mustache-escape': 'warn',
    'security/detect-eval-with-expression': 'error',
    'security/detect-new-buffer': 'error',
    'security/detect-no-csrf-before-method-override': 'warn',
    'security/detect-non-literal-fs-filename': 'warn',
    'security/detect-non-literal-regexp': 'warn',
    'security/detect-non-literal-require': 'warn',
    'security/detect-object-injection': 'off',
    'security/detect-possible-timing-attacks': 'warn',
    'security/detect-pseudoRandomBytes': 'warn',
    'security/detect-unsafe-regex': 'warn',
    'security/detect-bidi-characters': 'warn',
    'unicorn/prevent-abbreviations': 'off',
    'unicorn/filename-case': [
      'warn',
      {
        cases: {
          camelCase: true,
          pascalCase: true,
        },
      },
    ],
    'unicorn/no-array-reverse': 'off',
    'jsdoc/require-jsdoc': 'off',
    'import/no-unresolved': 'off',
    'import/order': 'off',
  },
};

const jsonConfig = {
  files: ['**/*.json'],
  languageOptions: {
    parser: jsoncParser,
  },
  rules: {
    'jsonc/sort-keys': 'off',
  },
};

const yamlConfig = {
  files: ['**/*.{yaml,yml}'],
  languageOptions: {
    parser: yamlParser,
  },
};

const jsOnlyConfig = {
  files: ['**/*.js'],
  languageOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module',
  },
};

export default [{ ignores }, ...extendedConfigs, baseConfig, jsonConfig, yamlConfig, jsOnlyConfig];
