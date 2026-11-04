import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import { defineConfig, globalIgnores } from 'eslint/config'

// Feature folders under src/components, one per tab. A feature may use ui/, shell/, kit/ and the shared
// folders below, but not reach into a sibling feature: what two features share belongs in one of those, or in
// lib/. Enforced.
const FEATURES = [
  'colloquial', 'daleel', 'dawah', 'dictionary', 'grow', 'hadith', 'home', 'map',
  'memorise', 'nahw', 'quiz', 'quran', 'sarf', 'similar', 'timelines',
]
// Shared by several features (the account, the word and sentence cards, the practice board). They may
// use each other, never a feature.
const SHARED = ['grammar', 'level', 'practice', 'profile']
const siblingImports = (feature) => ({
  files: [`src/components/${feature}/**/*.{js,jsx}`],
  rules: {
    'no-restricted-imports': ['error', {
      patterns: [{
        regex: `^(\\.\\./)+(${FEATURES.filter((f) => f !== feature).join('|')})/`,
        message: `${feature}/ should not import from a feature folder: move what they share to ui/, a shared folder or lib/.`,
      }],
    }],
  },
})

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{js,jsx}'],
    extends: [
      js.configs.recommended,
      reactHooks.configs.flat.recommended,
      reactRefresh.configs.vite,
    ],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
      parserOptions: {
        ecmaVersion: 'latest',
        ecmaFeatures: { jsx: true },
        sourceType: 'module',
      },
    },
    rules: {
      // Components are only ever referenced from JSX, which this setup does not
      // count as a use, so PascalCase names are exempt as values and as arguments.
      'no-unused-vars': ['error', { varsIgnorePattern: '^[A-Z_]', argsIgnorePattern: '^[A-Z_]' }],
    },
  },
  {
    // A file past 300 lines is doing more than one job. A warning: the long ones are listed, not blocked.
    files: ['src/**/*.{js,jsx}'],
    ignores: ['**/*.test.{js,jsx}'],
    rules: { 'max-lines': ['warn', { max: 300, skipBlankLines: true, skipComments: true }] },
  },
  ...[...FEATURES, ...SHARED].map(siblingImports),
  {
    // Things under scripts/ are run by node from a terminal, not served to a
    // browser, so process, Buffer and the rest of node are theirs to use.
    files: ['scripts/**/*.{js,mjs}'],
    languageOptions: { globals: globals.node },
  },
])
