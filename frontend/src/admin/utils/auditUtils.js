import React from "react";
import { Badge } from "../../components/ui/badge";

/**
 * Utility functions for Audit Logs.
 */

export const sortLogs = (rows, ordering) => {
  const items = [...rows];
  const byTimestamp = (a, b) =>
    new Date(a?.timestamp || 0).getTime() -
    new Date(b?.timestamp || 0).getTime();
  const byAction = (a, b) =>
    String(a?.action || "").localeCompare(String(b?.action || ""));

  if (ordering === "timestamp") {
    items.sort((a, b) => byTimestamp(a, b) || byAction(a, b));
  } else if (ordering === "-timestamp") {
    items.sort((a, b) => byTimestamp(b, a) || byAction(a, b));
  } else if (ordering === "action") {
    items.sort((a, b) => byAction(a, b) || byTimestamp(b, a));
  } else if (ordering === "-action") {
    items.sort((a, b) => byAction(b, a) || byTimestamp(b, a));
  }
  return items;
};

export const getActionBadge = (action) => {
  switch (action) {
    case "TOGGLE_USER_BLOCK":
      return (
        <Badge
          variant="outline"
          className="admin-muted-badge text-[9px] uppercase tracking-wider"
        >
          Moderation
        </Badge>
      );
    case "DELETE_USER":
      return (
        <Badge
          variant="outline"
          className="bg-red-500/10 border-red-500/20 text-red-400 text-[9px] uppercase tracking-wider"
        >
          Deletion
        </Badge>
      );
    case "SEND_GLOBAL_NOTIFICATION":
      return (
        <Badge
          variant="outline"
          className="admin-muted-badge text-[9px] uppercase tracking-wider"
        >
          Broadcast
        </Badge>
      );
    default:
      return (
        <Badge
          variant="outline"
          className="admin-muted-badge text-[9px] uppercase tracking-wider text-neutral-400"
        >
          System
        </Badge>
      );
  }
};

export const renderDetails = (details) => {
  if (!details) return "-";
  if (typeof details === "string") return details;

  if (details.before !== undefined || details.after !== undefined) {
    const beforeState = details.before?.is_active ?? details.before;
    const afterState = details.after?.is_active ?? details.after;
    if (beforeState !== undefined && afterState !== undefined) {
      return `Changed: ${JSON.stringify(beforeState)} -> ${JSON.stringify(afterState)}`;
    }
  }

  if (details.message) return details.message;
  if (details.reason) return details.reason;

  const entries = Object.entries(details);
  if (entries.length > 0) {
    return entries.map(([k, v]) => `${k}: ${JSON.stringify(v)}`).join(", ");
  }

  return JSON.stringify(details);
};
