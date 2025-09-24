export default {
  '*.{json,md,yaml,yml,css,scss}': ['prettier --write'],
  '*.py': ['py -m black', 'python -m isort'],
};
