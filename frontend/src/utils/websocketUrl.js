const getWindowWsProtocol = () =>
  window.location.protocol === "https:" ? "wss:" : "ws:";

const toWebSocketProtocol = (protocol) =>
  protocol === "https:" || protocol === "wss:" ? "wss:" : "ws:";

const normalizePath = (pathname, defaultPath, legacyPaths = []) => {
  const trimmed = String(pathname || "").replace(/^\/+|\/+$/g, "");
  const normalized = trimmed ? `/${trimmed}` : "/";

  if (normalized === "/" || legacyPaths.includes(normalized)) {
    return defaultPath;
  }

  return normalized;
};

const parseUrl = (rawUrl) => {
  try {
    return new URL(rawUrl, window.location.origin);
  } catch {
    return null;
  }
};

export const buildWebSocketUrl = ({
  explicitUrl,
  apiUrl,
  defaultPath,
  legacyPaths = [],
  label = "WebSocket",
  token = null,
}) => {
  console.log(
    `[buildWebSocketUrl] label=${label} apiUrl=${apiUrl} defaultPath=${defaultPath} window.location.host=${window.location.host}`,
  );
  let wsUrlString = "";

  if (explicitUrl) {
    const explicit = parseUrl(explicitUrl);
    if (explicit) {
      explicit.protocol = toWebSocketProtocol(explicit.protocol);
      explicit.pathname = normalizePath(
        explicit.pathname,
        defaultPath,
        legacyPaths,
      );
      explicit.hash = "";
      wsUrlString = explicit.toString();
    }
  }

  if (!wsUrlString && apiUrl) {
    if (apiUrl.startsWith("/")) {
      wsUrlString = `${getWindowWsProtocol()}//${window.location.host}${defaultPath}`;
    } else {
      const parsedApiUrl = parseUrl(apiUrl);
      if (parsedApiUrl) {
        parsedApiUrl.protocol = toWebSocketProtocol(parsedApiUrl.protocol);
        parsedApiUrl.pathname = defaultPath;
        parsedApiUrl.search = "";
        parsedApiUrl.hash = "";
        wsUrlString = parsedApiUrl.toString();
      }
    }
  }

  if (!wsUrlString) {
    wsUrlString = `${getWindowWsProtocol()}//${window.location.host}${defaultPath}`;
  }

  if (token) {
    try {
      const url = new URL(wsUrlString);
      url.searchParams.set("token", token);
      return url.toString();
    } catch {
      return wsUrlString;
    }
  }

  return wsUrlString;
};
