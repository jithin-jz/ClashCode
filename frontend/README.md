# CLASHCODE FRONTEND

This is the React-based frontend for the **CLASHCODE** platform.
Built with **Vite**, **React 19**, and **Tailwind CSS**.

## 🚀 Key Features
- **High-Fidelity Skeletons**: Pixel-perfect loading screens using the [Boneyard](https://github.com/jithin-jz/boneyard-js) system.
- **Real-Time Updates**: Integrated WebSockets and Firebase Cloud Messaging (FCM) for instant notifications.
- **Animated Icons**: Custom icon proxy system mapping standard Lucide React icons to high-quality 'itshover' animations.
- **Secure Auth**: Production-grade OAuth flow supporting Google and GitHub providers.
- **Monaco Workspace**: Seamless code editing experience with custom themes and instant execution feedback.

## 📁 Directory Structure
| Directory | Description |
| :--- | :--- |
| `src/auth` | Authentication pages (Login, Register) |
| `src/bones` | Skeleton screen definitions and primitives |
| `src/common` | Layouts and shared high-level components |
| `src/components` | Reusable UI elements (Buttons, Cards, etc.) |
| `src/game` | Challenge workspace and game-related logic |
| `src/hooks` | Custom React hooks |
| `src/icons` | Icon library and proxies |
| `src/pages` | Top-level page components |
| `src/services` | API clients and WebSocket service |
| `src/stores` | Zustand state management |
| `src/styles` | Global CSS, design tokens, and animations |

## 🛠️ Development

1. **Install dependencies**:
   ```bash
   npm install
   ```
2. **Start dev server**:
   ```bash
   npm run dev
   ```
3. **Build for production**:
   ```bash
   npm run build
   ```

## 🧹 Maintenance
Keep the `/src/bones` directory updated when layout changes occur to ensure the loading experience remains pixel-perfect.
