import React from "react";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";
import { Pencil, Trash2, Image as ImageIcon, Copy } from "lucide-react";

/**
 * StoreMobileList Component
 * 
 * Mobile-optimized card list for managing store items.
 */
const StoreMobileList = ({
  loading,
  items,
  handleOpenDialog,
  duplicateItem,
  handleDelete,
}) => {
  if (loading) {
    return [...Array(4)].map((_, i) => (
      <div
        key={i}
        className="admin-panel h-32 animate-pulse bg-white/[0.02] mb-3"
      />
    ));
  }

  if (items.length === 0) {
    return (
      <div className="admin-panel px-4 py-10 text-center text-sm italic text-neutral-500">
        No store items found.
      </div>
    );
  }

  return (
    <div className="space-y-3 md:hidden">
      {items.map((item) => (
        <div key={item.id} className="admin-panel p-4">
          <div className="flex items-start gap-3">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center overflow-hidden rounded-lg border border-white/10 bg-white/[0.04]">
              {item.image ? (
                <img src={item.image} alt="" className="h-full w-full object-cover" />
              ) : (
                <ImageIcon size={18} className="text-neutral-600" />
              )}
            </div>
            <div className="min-w-0 flex-1">
              <div className="truncate text-sm font-medium text-neutral-100">
                {item.name}
              </div>
              <div className="mt-1 line-clamp-2 text-[11px] text-neutral-500">
                {item.description}
              </div>
              <div className="mt-3 flex items-center justify-between gap-3">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge
                    variant="outline"
                    className="admin-muted-badge rounded-md px-2 py-0.5 text-[9px] font-medium uppercase tracking-wider"
                  >
                    {item.category}
                  </Badge>
                  {item.featured && (
                    <Badge
                      variant="outline"
                      className="admin-muted-badge rounded-md px-2 py-0.5 text-[9px] font-medium uppercase tracking-wider"
                    >
                      Featured
                    </Badge>
                  )}
                </div>
                <div className="text-right">
                  <div className="text-xs font-mono text-neutral-200">
                    {item.cost} XP
                  </div>
                  <div className="text-[10px] text-neutral-500">
                    {item.is_active ? "Visible" : "Hidden"}
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div className="mt-4 flex gap-2 border-t border-white/8 pt-3">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleOpenDialog(item)}
              className="h-9 flex-1 border-white/10 bg-white/[0.03] text-neutral-300 hover:bg-white/[0.06] hover:text-white"
            >
              <Pencil size={16} />
              Edit
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => duplicateItem(item.id)}
              className="h-9 flex-1 border-white/10 bg-white/[0.03] text-neutral-300 hover:bg-white/[0.06] hover:text-white"
            >
              <Copy size={16} />
              Copy
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleDelete(item.id)}
              className="h-9 flex-1 border-white/10 bg-white/[0.03] text-neutral-300 hover:bg-red-500/10 hover:text-red-400"
            >
              <Trash2 size={16} />
              Delete
            </Button>
          </div>
        </div>
      ))}
    </div>
  );
};

export default StoreMobileList;
