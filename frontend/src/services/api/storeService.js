import api from "./client";

export const storeService = {
  getItems: () => api.get("/store/items/"),
  getPurchasedItems: () => api.get("/store/purchased/"),
  purchaseItem: (id) => api.post(`/store/buy/${id}/`),
  equipItem: (id) => api.post("/store/equip/", { item_id: id }),
  unequipItem: (category) => api.post("/store/unequip/", { category }),
};
