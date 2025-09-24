export default {
  '*.{js,ts,tsx}': ['pnpm exec eslint --fix'],
  '*.{json,md,yaml,yml,css,scss}': ['prettier --write'],
  '*.py': ['python -m black', 'python -m isort'],
};
