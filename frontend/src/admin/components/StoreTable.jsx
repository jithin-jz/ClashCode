import React from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../../components/ui/table";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";
import { Pencil, Trash2, Image as ImageIcon, Copy } from "lucide-react";
import { AdminTableLoadingRow } from "../AdminSkeletons";

/**
 * StoreTable Component
 * 
 * Desktop-optimized table for managing store items.
 */
const StoreTable = ({
  loading,
  items,
  toggleItemField,
  duplicateItem,
  handleOpenDialog,
  handleDelete,
}) => {
  return (
    <div className="hidden overflow-hidden md:block admin-panel">
      <Table className="min-w-[760px]">
        <TableHeader>
          <TableRow className="border-white/10 hover:bg-transparent bg-white/[0.02]">
            <TableHead className="w-[80px] px-6 py-3 text-[10px] font-medium uppercase tracking-[0.18em] text-neutral-500">
              Icon
            </TableHead>
            <TableHead className="py-3 text-[10px] font-medium uppercase tracking-[0.18em] text-neutral-500">
              Item Details
            </TableHead>
            <TableHead className="py-3 text-[10px] font-medium uppercase tracking-[0.18em] text-neutral-500">
              Category
            </TableHead>
            <TableHead className="py-3 text-[10px] font-medium uppercase tracking-[0.18em] text-neutral-500">
              Price
            </TableHead>
            <TableHead className="py-3 text-[10px] font-medium uppercase tracking-[0.18em] text-neutral-500">
              Flags
            </TableHead>
            <TableHead className="px-6 py-3 text-right text-[10px] font-medium uppercase tracking-[0.18em] text-neutral-500">
              Actions
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {loading
            ? [...Array(6)].map((_, i) => (
                <AdminTableLoadingRow key={i} colSpan={6} />
              ))
            : items.map((item) => (
                <TableRow
                  key={item.id}
                  className="border-white/10 hover:bg-white/5 transition-colors group"
                >
                  <TableCell className="py-3 px-6">
                    <div className="w-10 h-10 bg-white/[0.04] rounded-lg border border-white/10 flex items-center justify-center overflow-hidden">
                      {item.image ? (
                        <img
                          src={item.image}
                          alt=""
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <ImageIcon size={18} className="text-neutral-600" />
                      )}
                    </div>
                  </TableCell>
                  <TableCell className="py-3">
                    <div className="flex flex-col">
                      <span className="text-sm font-medium text-neutral-100 tracking-tight">
                        {item.name}
                      </span>
                      <span className="text-[11px] text-neutral-500 line-clamp-1">
                        {item.description}
                      </span>
                    </div>
                  </TableCell>
                  <TableCell className="py-3">
                    <Badge
                      variant="outline"
                      className="admin-muted-badge rounded-md px-2 py-0.5 text-[9px] font-medium uppercase tracking-wider"
                    >
                      {item.category}
                    </Badge>
                  </TableCell>
                  <TableCell className="py-3 font-mono text-xs text-neutral-300">
                    {item.cost} XP
                  </TableCell>
                  <TableCell className="py-3">
                    <div className="flex flex-wrap gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => toggleItemField(item, "is_active")}
                        className="h-7 border-white/10 bg-white/[0.03] px-2 text-[10px] uppercase tracking-wider text-neutral-300 hover:bg-white/[0.06] hover:text-white"
                      >
                        {item.is_active ? "Visible" : "Hidden"}
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => toggleItemField(item, "featured")}
                        className="h-7 border-white/10 bg-white/[0.03] px-2 text-[10px] uppercase tracking-wider text-neutral-300 hover:bg-white/[0.06] hover:text-white"
                      >
                        {item.featured ? "Featured" : "Standard"}
                      </Button>
                    </div>
                  </TableCell>
                  <TableCell className="text-right py-3 px-6">
                    <div className="flex justify-end gap-1">
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => duplicateItem(item.id)}
                        className="h-8 w-8 text-neutral-400 hover:text-white hover:bg-white/10 rounded-md"
                      >
                        <Copy size={16} />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleOpenDialog(item)}
                        className="h-8 w-8 text-neutral-400 hover:text-white hover:bg-white/10 rounded-md"
                      >
                        <Pencil size={16} />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleDelete(item.id)}
                        className="h-8 w-8 text-neutral-400 hover:text-red-400 hover:bg-red-500/10 rounded-md"
                      >
                        <Trash2 size={16} />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
        </TableBody>
      </Table>
    </div>
  );
};

export default StoreTable;
