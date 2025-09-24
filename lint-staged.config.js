export default {
  '*.{json,md,yaml,yml,css,scss}': ['prettier --write'],
  '*.py': ['python -m black', 'python -m isort'],
};
