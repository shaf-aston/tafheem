import demoTree from './assets/demoTree.json'

// The one place the demo sentence comes from. A typed sentence would swap this
// for analyzeIraab(sentence) in api.js; SentenceDemo does not care which.
export const loadDemo = () => demoTree
