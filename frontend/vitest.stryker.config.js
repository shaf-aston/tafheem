// Mutation testing only (npm run mutate, stryker.config.json). Stryker mutates modules in
// src/lib, so it needs only their own tests (a hook's are .jsx, beside it): the screen
// tests in src/test that import them too would add ~10 s per run and kill nothing more.
// Stryker's related mode then narrows this set to the tests that import the mutated file.
import { defineConfig, mergeConfig } from 'vitest/config'

import viteConfig from './vite.config.js'

export default mergeConfig(viteConfig, defineConfig({
  test: { include: ['src/lib/**/*.test.{js,jsx}'] },
}))
