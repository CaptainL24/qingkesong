import type { InstalledPet } from "./types";

export const BUNDLED_PETS: InstalledPet[] = [
  {
    slug: "dodong",
    manifest: {
      id: "dodong",
      displayName: "比格多栋",
      description: "Internal prototype desktop pet inspired by the Biggie Dodong IP.",
      spritesheet: "",
      source: "builtin"
    },
    spritesheetPath: "",
    spritesheetExt: "png",
    importedAt: "builtin"
  },
  {
    slug: "duo",
    manifest: {
      id: "duo",
      displayName: "Duo",
      description: "Learning companion with expressive chibi sprite poses.",
      spritesheet: "spritesheet.webp",
      source: "builtin"
    },
    spritesheetPath: "petdex_pets/duo/spritesheet.webp",
    spritesheetExt: "webp",
    importedAt: "builtin"
  }
];

export function allPets(importedPets: InstalledPet[]): InstalledPet[] {
  const pets = new Map(BUNDLED_PETS.map((pet) => [pet.slug, pet]));
  for (const pet of importedPets) {
    pets.set(pet.slug, pet);
  }
  return [...pets.values()];
}
