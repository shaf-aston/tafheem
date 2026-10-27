import demoTree from './assets/demoTree.json'

// The one place the demo sentence comes from. A typed sentence would swap this
// for analyzeIraab(sentence) in api/nahw.js; storyData does not care which.
export const loadDemo = () => demoTree
