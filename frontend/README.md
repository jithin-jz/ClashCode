# 🎮 CLASHCODE - Frontend

The **CLASHCODE Frontend** is a modern, interactive web application built with **React** and **Vite**. It provides a gamified experience where users can solve coding challenges, manage their profiles, and interact with the community.

## 🚀 Tech Stack

- **Framework:** [React 19](https://react.dev/)
- **Build Tool:** [Vite](https://vitejs.dev/)
- **Styling:** [Tailwind CSS 4](https://tailwindcss.com/)
- **State Management:** [Zustand](https://github.com/pmndrs/zustand)
- **Animations:** [Framer Motion](https://www.framer.com/motion/)
- **Icons:** [Lucide React](https://lucide.dev/)
- **Code Editor:** [@monaco-editor/react](https://github.com/suren-atoyan/monaco-react)

## 📂 Project Structure

- `src/game/`: Core gameplay logic and the **Code Arena** editor.
- `src/pages/`: Main application screens (Home, Profile, Shop, etc.).
- `src/components/`: Reusable UI components built with Tailwind.
- `src/stores/`: Zustand stores for auth, game state, and notifications.
- `src/services/`: API client and WebSocket integration layers.
- `src/admin/`: Administrative dashboard components.

## 🧱 UI Architecture

- Professional frontend architecture guide: [`docs/UI_ARCHITECTURE.md`](./docs/UI_ARCHITECTURE.md)
- Recommended approach: **Feature-First + Design System** (tokens -> primitives -> layout -> feature UI -> page composition)

## 🛠️ Key Features

- **Interactive Code Arena:** Real-time code editing and execution validation.
- **Dynamic Game Map:** Unlock new levels and explore the Code of Clans world.
- **Profile Customization:** Show off your badges, XP, and contribution calendar.
- **Real-Time Social:** Integrated chat and community post feed.
- **Responsive Design:** Optimized for both desktop and mobile views.

## 🔧 Setup & Installation

### Prerequisites

- Node.js 18+
- npm or yarn

### Local Development

1. **Navigate to the frontend directory:**
   ```bash
   cd frontend
   ```
2. **Install dependencies:**
   ```bash
   npm install
   ```
3. **Environment Variables:**
   Configure `.env` with:
   - `VITE_API_URL`: Core API base. Use `/api` locally, or `https://api.your-domain.com/api` in deployment.
   - `VITE_CHAT_URL` (or `VITE_WS_URL`): Chat websocket base. Use `/ws/chat` locally, or `wss://api.your-domain.com/ws/chat` in deployment.
   - `VITE_NOTIFICATIONS_WS_URL`: Notifications websocket base. Use `/ws/notifications` locally, or `wss://api.your-domain.com/ws/notifications` in deployment.
   - `VITE_AI_URL`: AI service base. Use `/ai` locally, or `https://api.your-domain.com/ai` in deployment.

   A ready-to-copy local template now lives at `frontend/.env.example`.

4. **Start the development server:**

   ```bash
   npm run dev
   ```

   The supported local setup is to keep backend services running through the root `docker-compose.yml`, while the frontend runs directly on `http://localhost:5173`.

## 🏗️ Build & Production

To create a production-optimized build:

```bash
npm run build
```

The output will be in the `dist/` directory.
