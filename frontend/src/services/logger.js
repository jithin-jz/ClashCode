import * as Sentry from "@sentry/react";

/**
 * SLog - Centralized Logging & Error Tracking
 * Wraps Sentry for production monitoring and provides consistent local logging.
 */

const IS_PROD = import.meta.env.PROD;
const DSN = import.meta.env.VITE_SENTRY_DSN;

export const SLog = {
  init: () => {
    if (DSN) {
      Sentry.init({
        dsn: DSN,
        integrations: [
          Sentry.browserTracingIntegration(),
          Sentry.replayIntegration(),
        ],
        // Performance Monitoring
        tracesSampleRate: IS_PROD ? 0.2 : 1.0,
        // Session Replay
        replaysSessionSampleRate: 0.1,
        replaysOnErrorSampleRate: 1.0,
        environment: import.meta.env.MODE,
      });
      console.log("[SLog] Sentry initialized");
    } else {
      console.log("[SLog] Sentry DSN not found, using console only.");
    }
  },

  /**
   * Log an error and report to Sentry.
   */
  error: (message, error = null, context = {}) => {
    console.error(`[SLog] ERROR: ${message}`, error || "", context);

    if (DSN) {
      Sentry.withScope((scope) => {
        if (context.tags) {
          Object.entries(context.tags).forEach(([k, v]) => scope.setTag(k, v));
        }
        scope.setExtras(context);

        if (error instanceof Error) {
          Sentry.captureException(error);
        } else {
          Sentry.captureMessage(message, "error");
        }
      });
    }
  },

  /**
   * Log info message (local only, adds breadcrumb in Sentry).
   */
  info: (message, context = {}) => {
    if (!IS_PROD) {
      console.info(`[SLog] INFO: ${message}`, context);
    }

    Sentry.addBreadcrumb({
      category: "app.info",
      message,
      data: context,
      level: "info",
    });
  },

  /**
   * Log warning.
   */
  warn: (message, context = {}) => {
    console.warn(`[SLog] WARN: ${message}`, context);

    Sentry.addBreadcrumb({
      category: "app.warn",
      message,
      data: context,
      level: "warning",
    });

    if (IS_PROD && DSN) {
      Sentry.captureMessage(message, "warning");
    }
  },

  /**
   * Identify the user in Sentry for easier debugging.
   */
  setUser: (user) => {
    if (user) {
      Sentry.setUser({
        id: user.id || user.pk,
        username: user.username,
        email: user.email,
      });
    } else {
      Sentry.setUser(null);
    }
  },
};
