const ts = require('typescript');

module.exports = {
  process(src, filename) {
    const result = ts.transpileModule(src, {
      compilerOptions: {
        module: ts.ModuleKind.CommonJS,
        target: ts.ScriptTarget.ES2019,
        esModuleInterop: true,
        moduleResolution: ts.ModuleResolutionKind.NodeJs,
        sourceMap: true,
        allowJs: false,
      },
      fileName: filename,
    });
    return { code: result.outputText, map: result.sourceMapText ?? undefined };
  },
};
