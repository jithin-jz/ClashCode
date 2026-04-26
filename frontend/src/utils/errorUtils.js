/**
 * Extracts a user-friendly error message from a backend response.
 * Handles the new centralized error format: { error: "...", code: "...", request_id: "..." }
 * as well as standard DRF { detail: "..." } and field errors { field: ["..."] }.
 */
export const getErrorMessage = (
  error,
  defaultMessage = "An unexpected error occurred",
) => {
  const data = error?.response?.data;

  if (!data) return error?.message || defaultMessage;

  // 1. Centralized error format
  if (data.error) return data.error;

  // 2. Standard DRF detail
  if (data.detail) return data.detail;

  // 3. Field validation errors (e.g. { "email": ["This field is required."] })
  if (typeof data === "object" && !Array.isArray(data)) {
    const firstKey = Object.keys(data)[0];
    const firstError = data[firstKey];
    if (Array.isArray(firstError)) return `${firstKey}: ${firstError[0]}`;
    if (typeof firstError === "string") return firstError;
  }

  return defaultMessage;
};

/**
 * Extracts the support request ID from the error response.
 */
export const getRequestId = (error) => {
  return error?.response?.data?.request_id;
};
