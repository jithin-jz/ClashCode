import api from "./client";

export const paymentService = {
  createOrder: (amount) => api.post("/payments/create-order/", { amount }),
  verifyPayment: (data) => api.post("/payments/verify-payment/", data),
};
