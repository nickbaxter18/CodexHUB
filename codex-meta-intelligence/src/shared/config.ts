interface EnvironmentConfig {
  cursorApiUrl: string;
  cursorStrictMode: boolean;
  knowledgeAutoLoad: boolean;
}

const resolveBoolean = (value: string | undefined, fallback: boolean): boolean => {
  if (value === undefined) return fallback;
  return !['0', 'false', 'off'].includes(value.toLowerCase());
};

export const loadConfiguration = (): EnvironmentConfig => {
  return {
    cursorApiUrl: process.env.CURSOR_API_URL ?? 'https://api.cursor.sh',
    cursorStrictMode: resolveBoolean(process.env.CURSOR_STRICT_MODE, false),
    knowledgeAutoLoad: resolveBoolean(process.env.KNOWLEDGE_AUTO_LOAD, true),
  };
};
