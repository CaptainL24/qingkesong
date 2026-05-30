import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

export const APP_NAME = "PawPause";
export const STORE_NAME = "pawpause";

export const PET_WINDOW = {
  width: 220,
  height: 340
} as const;

export const SCREEN_BLOCK_WINDOW = {
  minWidth: 520,
  minHeight: 420
} as const;

export const SETTINGS_WINDOW = {
  width: 760,
  height: 680
} as const;

export const EXERCISE_WINDOW = {
  width: 940,
  height: 720
} as const;

export const LAUNCH_WINDOW = {
  width: 1280,
  height: 800
} as const;

export const PRELOAD_PATH = join(__dirname, "../preload/index.cjs");
export const RENDERER_HTML_PATH = join(__dirname, "../renderer/index.html");
export const EXERCISE_GAME_HTML_PATH = join(__dirname, "../renderer/game1_v2.html");
export const LAUNCH_HTML_PATH = join(__dirname, "../renderer/launch.html");
export const IS_DEV = Boolean(process.env.ELECTRON_RENDERER_URL);

export function exerciseGameUrl(): string {
  const devServer = process.env.ELECTRON_RENDERER_URL;
  if (devServer) return `${devServer}/game1_v2.html`;
  return EXERCISE_GAME_HTML_PATH;
}

export function launchPageUrl(): string {
  const devServer = process.env.ELECTRON_RENDERER_URL;
  if (devServer) return `${devServer}/launch.html`;
  return LAUNCH_HTML_PATH;
}

export const DISTRACTION_CHECK_INTERVAL_MS = 3000;
export const DISTRACTION_WARNING_COOLDOWN_MS = 60_000;
export const BREAK_RUN_DURATION_MS = 60_000;
export const BREAK_RUN_TICK_MS = 16;
