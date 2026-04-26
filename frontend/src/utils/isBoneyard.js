/**
 * isBoneyard.js
 * Utility to detect if the current environment is the Boneyard skeleton crawler.
 * Refined to avoid false positives for real users with dev tools open.
 */
export const isBoneyard = () => {
  // window.boneyard_capture is explicitly set by the boneyard crawler script
  if (typeof window !== "undefined" && window.boneyard_capture) return true;

  // Strict user agent check
  const ua = typeof navigator !== "undefined" ? navigator.userAgent : "";
  if (/Boneyard|HeadlessChrome/i.test(ua)) return true;

  return false;
};
