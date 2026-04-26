export const MONACO_THEMES = {
  industrial: {
    base: "vs-dark",
    inherit: true,
    rules: [
      { token: "comment", foreground: "444444" },
      { token: "keyword", foreground: "ffffff", fontStyle: "bold" },
      { token: "string", foreground: "a3a3a3" },
    ],
    colors: {
      "editor.background": "#000000",
      "editor.foreground": "#e8e8e8",
    },
  },
  dracula: {
    base: "vs-dark",
    inherit: true,
    rules: [],
    colors: { "editor.background": "#282a36" },
  },
  nord: {
    base: "vs-dark",
    inherit: true,
    rules: [],
    colors: { "editor.background": "#2e3440" },
  },
  monokai: {
    base: "vs-dark",
    inherit: true,
    rules: [],
    colors: { "editor.background": "#272822" },
  },
  "solarized-dark": {
    base: "vs-dark",
    inherit: true,
    rules: [],
    colors: { "editor.background": "#002b36" },
  },
  cyberpunk: {
    base: "vs-dark",
    inherit: true,
    rules: [],
    colors: { "editor.background": "#0d0d0d" },
  },
};

export const THEME_NAME_MAP = {
  solarized_dark: "solarized-dark",
};

export const VALID_THEMES = [
  "dracula",
  "nord",
  "monokai",
  "solarized_dark",
  "solarized-dark",
  "cyberpunk",
];

export const defineMonacoThemes = (monaco) => {
  Object.entries(MONACO_THEMES).forEach(([name, config]) => {
    monaco.editor.defineTheme(name, config);
  });
};
