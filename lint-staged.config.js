export default {
  '*.{js,ts,tsx}': ['eslint --fix', 'prettier --write'],
  '*.{json,md,yaml,yml,css,scss}': ['prettier --write'],
  '*.py': ['python -m black', 'python -m isort'],
  '*.{py,js,ts,tsx}': ['cspell --no-progress --no-summary'],
};
