import { allPets } from "../../shared/bundledPets";
import { PETDEX_SPRITE_SIZE, PETDEX_STATES, mapPetStateToPetdexState } from "../../shared/spriteStates";
import type { InstalledPet, PetState, SpriteAnimationState } from "../../shared/types";

const dodongStateImages: Partial<Record<PetState, string>> = {
  idle: new URL("./dodong-states/idle.png", import.meta.url).href,
  meetingCompact: new URL("./dodong-states/meeting-compact.png", import.meta.url).href,
  working: new URL("./dodong-states/working.png", import.meta.url).href,
  analyzing: new URL("./dodong-states/analyzing.png", import.meta.url).href,
  banweiLow: new URL("./dodong-states/banwei-low.png", import.meta.url).href,
  banweiMedium: new URL("./dodong-states/banwei-medium.png", import.meta.url).href,
  banweiHigh: new URL("./dodong-states/banwei-high.png", import.meta.url).href,
  neckGuide: new URL("./dodong-states/neck-guide.png", import.meta.url).href,
  exerciseRunning: new URL("./dodong-states/neck-guide.png", import.meta.url).href,
  exerciseDone: new URL("./dodong-states/exercise-done.png", import.meta.url).href,
  happy: new URL("./dodong-states/exercise-done.png", import.meta.url).href,
  waving: new URL("./dodong-states/banwei-low.png", import.meta.url).href,
  thinking: new URL("./dodong-states/analyzing.png", import.meta.url).href
};

export type SpritePetAsset = {
  kind: "sprite";
  src: string;
  animation: SpriteAnimationState;
  frameWidth: number;
  frameHeight: number;
  sheetWidth: number;
  sheetHeight: number;
};

export type FallbackPetAsset = {
  kind: "fallback";
};

export type StateImagePetAsset = {
  kind: "stateImage";
  src: string;
};

export type PetAsset = SpritePetAsset | FallbackPetAsset | StateImagePetAsset;

export function getSelectedPetAsset(
  selectedPetId: string,
  installedPets: InstalledPet[],
  state: PetState
): PetAsset {
  const installed = allPets(installedPets).find((pet) => pet.slug === selectedPetId) ?? allPets(installedPets)[0];
  if (installed?.slug === "dodong" || selectedPetId === "dodong") {
    return { kind: "stateImage", src: dodongStateImages[state] ?? dodongStateImages.idle ?? "" };
  }
  if (!installed || !installed.spritesheetPath) {
    return { kind: "fallback" };
  }

  const src = new URL(window.pawpause.assetUrl(installed.spritesheetPath));
  const petdexState = mapPetStateToPetdexState(state);

  return {
    kind: "sprite",
    src: src.href,
    animation: PETDEX_STATES[petdexState],
    frameWidth: PETDEX_SPRITE_SIZE.frameWidth,
    frameHeight: PETDEX_SPRITE_SIZE.frameHeight,
    sheetWidth: PETDEX_SPRITE_SIZE.sheetWidth,
    sheetHeight: PETDEX_SPRITE_SIZE.sheetHeight
  };
}
