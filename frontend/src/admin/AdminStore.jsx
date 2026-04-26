import React, { useEffect, useMemo, useState } from "react";
import { Button } from "../components/ui/button";
import { Plus } from "lucide-react";
import { notify } from "../services/notification";
import api, { authAPI } from "../services/api";

// Sub-components
import StoreItemDialog from "./components/StoreItemDialog";
import StoreTable from "./components/StoreTable";
import StoreMobileList from "./components/StoreMobileList";
import StorePagination from "./components/StorePagination";

/**
 * AdminStore Component
 * 
 * The main container for Store Management in the Admin panel.
 * Orchestrates data fetching, CRUD operations, and view switching.
 */
const AdminStore = () => {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [currentItem, setCurrentItem] = useState(null);
  const [saving, setSaving] = useState(false);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  const [formData, setFormData] = useState({
    name: "",
    description: "",
    cost: 100,
    category: "THEME",
    icon_name: "Palette",
    image: "",
    is_active: true,
    item_data: "{}",
  });

  useEffect(() => {
    fetchItems();
  }, []);

  const totalCount = items.length;
  const totalPages = Math.max(1, Math.ceil(totalCount / pageSize));
  
  const paginatedItems = useMemo(() => {
    const start = (page - 1) * pageSize;
    return items.slice(start, start + pageSize);
  }, [items, page, pageSize]);

  useEffect(() => {
    if (page > totalPages) setPage(totalPages);
  }, [page, totalPages]);

  const fetchItems = async () => {
    setLoading(true);
    try {
      const response = await api.get("/store/items/");
      setItems(response.data);
    } catch {
      notify.error("Failed to fetch store items");
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDialog = (item = null) => {
    if (item) {
      setCurrentItem(item);
      setFormData({
        name: item.name,
        description: item.description,
        cost: item.cost,
        category: item.category,
        icon_name: item.icon_name,
        image: item.image || "",
        is_active: item.is_active,
        item_data: JSON.stringify(item.item_data || {}, null, 2),
      });
    } else {
      setCurrentItem(null);
      setFormData({
        name: "",
        description: "",
        cost: 100,
        category: "THEME",
        icon_name: "Palette",
        image: "",
        is_active: true,
        item_data: "{}",
      });
    }
    setIsDialogOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      let parsedData;
      try {
        parsedData = JSON.parse(formData.item_data);
      } catch {
        notify.error("Invalid JSON configuration");
        setSaving(false);
        return;
      }

      const payload = { ...formData, item_data: parsedData };

      if (currentItem) {
        await api.patch(`/store/items/${currentItem.id}/`, payload);
        notify.success("Item updated");
      } else {
        await api.post("/store/items/", payload);
        notify.success("Item created");
      }
      setIsDialogOpen(false);
      fetchItems();
    } catch {
      notify.error("Failed to save item");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id) => {
    notify.warning("Delete Item", {
      description: "Are you sure you want to delete this item? This action cannot be undone.",
      action: {
        label: "Delete",
        onClick: () => confirmDelete(id),
      },
    });
  };

  const confirmDelete = async (id) => {
    try {
      await api.delete(`/store/items/${id}/`);
      notify.success("Item deleted");
      fetchItems();
    } catch {
      notify.error("Failed to delete item");
    }
  };

  const toggleItemField = async (item, field) => {
    try {
      await api.patch(`/store/items/${item.id}/`, {
        [field]: !item[field],
      });
      notify.success(`${field === "featured" ? "Featured" : "Visibility"} updated`);
      fetchItems();
    } catch {
      notify.error("Failed to update item");
    }
  };

  const duplicateItem = async (itemId) => {
    try {
      await authAPI.duplicateStoreItem(itemId);
      notify.success("Item duplicated");
      fetchItems();
    } catch {
      notify.error("Failed to duplicate item");
    }
  };

  return (
    <div className="space-y-4">
      {/* Header Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <h2 className="text-xl font-semibold text-neutral-100 tracking-tight">
          Store Management
        </h2>
        <Button
          onClick={() => handleOpenDialog()}
          className="h-8 w-full gap-2 rounded-md bg-white px-3 font-medium text-black transition-colors hover:bg-zinc-200 sm:w-auto"
        >
          <Plus size={16} />
          <span className="text-xs">Add Item</span>
        </Button>
      </div>

      {/* Mobile View */}
      <StoreMobileList
        loading={loading}
        items={paginatedItems}
        handleOpenDialog={handleOpenDialog}
        duplicateItem={duplicateItem}
        handleDelete={handleDelete}
      />

      {/* Desktop View */}
      <StoreTable
        loading={loading}
        items={paginatedItems}
        toggleItemField={toggleItemField}
        duplicateItem={duplicateItem}
        handleOpenDialog={handleOpenDialog}
        handleDelete={handleDelete}
      />

      {/* Pagination Footer */}
      {!loading && (
        <StorePagination
          page={page}
          setPage={setPage}
          totalPages={totalPages}
          pageSize={pageSize}
          setPageSize={setPageSize}
          totalCount={totalCount}
        />
      )}

      {/* Item Modal */}
      <StoreItemDialog
        isOpen={isDialogOpen}
        setIsOpen={setIsDialogOpen}
        currentItem={currentItem}
        formData={formData}
        setFormData={setFormData}
        saving={saving}
        handleSubmit={handleSubmit}
      />
    </div>
  );
};

export default AdminStore;
